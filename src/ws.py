"""Socket IO app for WebSocket connections."""
import functools
import traceback
from datetime import timedelta
from typing import Any, Awaitable, Callable

import socketio

from .models import GameTimer, Session


app = socketio.AsyncServer(
    async_mode='sanic',
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True,
)

Handler = Callable[..., Awaitable[None]]


class ApiError(Exception):
    """Exception raised when the API detects an error."""

    def __init__(self, detail: str):
        """Store the details of the error."""
        super().__init__(detail)
        self.detail = detail


def assert_(value: bool, message: str):
    """Raise an ApiError if a value is not truthy."""
    if not value:
        raise ApiError(message)


def assert_manager_or(
        session: Session, alternative_condition: bool, alternative_name: str):
    """Assert that the client is a manager.

    If the timer has no manager, assert that alternative_condition is truthy.
    """
    if session.game.managed:
        assert_(
            session.is_manager,
            'Only a manager can send this event for managed games.',
        )
    else:
        assert_(
            alternative_condition,
            f'Only {alternative_name} can send this event for unmanaged '
            'games.',
        )


async def send_state(timer: GameTimer):
    """Send the current state of a timer to all clients."""
    # Make sure we have the latest state.
    timer = GameTimer.get_timer(timer.id)
    await app.emit('state', timer.to_dict(), room='t-' + str(timer.id))


async def send_error(message: str, sid: str):
    """Send an error message to a client."""
    await app.emit('error', {'detail': message}, room=sid)


def register_event(handler: Handler):
    """Register an event handler and catch exceptions."""
    @functools.wraps(handler)
    async def wrapped(sid: str, *args: Any, **kwargs: Any):
        """Call the wrapped handler and catch exceptions."""
        session = Session.get_session(sid)
        try:
            await handler(session, *args, **kwargs)
        except ApiError as error:
            await send_error(str(error), sid)
        except Exception as error:
            print('Traceback (most recent call last):')
            traceback.print_tb(error.__traceback__)
            print(f'{type(error).__name__}: {error}.')
            await send_error(str(error), sid)
    app.event(wrapped)


@app.event
async def connect(sid: str, environ: dict[str, Any]) -> bool:
    """Handle a client connecting to the socket."""
    raw_id = environ.get('HTTP_BLITZTIME_TIMER', None)
    if not raw_id:
        return False
    try:
        timer_id = int(raw_id)
    except ValueError:
        return False
    token = environ.get('HTTP_AUTHORIZATION', None)
    if token:
        side = GameTimer.get_timer_side(timer_id, token)
        if isinstance(side, GameTimer):
            # "side" is actually the timer.
            session = Session.create(id=sid, game=side, is_manager=True)
        elif not side:
            return False
        else:
            session = Session.create(id=sid, game=side.game, side=side)
    else:
        game = GameTimer.get_timer(timer_id)
        if not game:
            return False
        session = Session.create(id=sid, game=game)
    app.enter_room(sid, 't-' + str(timer_id))
    await send_state(session.game)
    return True


@register_event
async def disconnect(session: Session):
    """Handle a client disconnecting."""
    game = session.game
    session.delete_instance()
    await send_state(game)


@register_event
async def start_timer(session: Session):
    """Start an unstarted timer."""
    assert_manager_or(
        session, session.side_id == session.game.home_id, 'player 1',
    )
    assert_(not session.game.started_at, 'Game already started.')
    assert_(session.game.away, 'Away side has not joined yet.')
    session.game.start()
    await send_state(session.game)


@register_event
async def end_turn(session: Session):
    """End the client's turn."""
    assert_manager_or(
        session, session.side and session.side.is_turn,
        'the currently playing player',
    )
    session.game.get_current_side().end_turn()
    await send_state(session.game)


async def on_timeout(session: Session):
    """Check the client's opponent's time."""
    assert_(
        session.game.started_at and not session.game.has_ended,
        'Game is not ongoing.',
    )
    side = session.game.get_current_side()
    assert_(not side.is_timed_out, 'Player is not timed out.')
    side.end_turn()
    await send_state(side.game)


@register_event
async def timeout(session: Session):
    """Check the client's opponent's time."""
    await on_timeout(session)


@register_event
async def opponent_timed_out(session: Session):
    """Alias of `timeout` for backwards compatibility."""
    await on_timeout(session)


@register_event
async def end_game(session: Session):
    """Check the client's opponent's time."""
    if session.is_manager:
        reporting_side = None
    else:
        reporting_side = session.side
        assert_(reporting_side, 'This event cannot be sent by an observer.')
    current_side = session.game.get_current_side()
    assert_(current_side, 'Game is not ongoing.')
    current_side.end_turn()
    if reporting_side == session.game.home:
        session.game.end_reporter = 0
    elif reporting_side == session.game.away:
        session.game.end_reporter = 1
    else:
        session.game.end_reporter = -1
    # `game.end()` calls `game.save()`, so we don't have to.
    session.game.end()
    await send_state(session.game)


@register_event
async def add_time(session: Session, seconds: int):
    """Add time to both players' clocks."""
    assert_(session.is_manager, 'Only a manager can send this event.')
    assert_(session.game.ongoing, 'Game is not ongoing.')
    assert_(isinstance(seconds, int), 'Seconds to add should be an int.')
    time = timedelta(seconds=seconds)
    session.game.home.total_time += time
    session.game.away.total_time += time
    session.game.home.save()
    session.game.away.save()
    await send_state(session.game)
