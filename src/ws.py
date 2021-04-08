"""Socket IO app for WebSocket connections."""
from datetime import timedelta
from typing import Any, Optional

import socketio

from .models import GameSide, GameTimer


app = socketio.AsyncServer(
    async_mode='sanic',
    cors_allowed_origins=[],
    logger=True,
    engineio_logger=True
)


async def send_state(timer: GameTimer):
    """Send the current state of a timer to all clients."""
    await app.emit('state', timer.to_dict(), room='t-' + str(timer.id))


async def send_error(message: str, sid: str):
    """Send an error message to a client."""
    await app.emit('error', {'detail': message}, room=sid)


async def get_game_side(sid: str) -> Optional[GameSide]:
    """Get the game side a connection is for."""
    side = GameSide.get_or_none(GameSide.session_id == sid)
    if not side:
        await send_error('Only players can send this event.', sid)
    else:
        return side
    return None


async def get_game(sid: str) -> Optional[GameTimer]:
    """Get the game a connection is a manager for."""
    timer = GameTimer.get_or_none(GameTimer.manager_session_id == sid)
    if not timer:
        await send_error('Only managers can send this event.', sid)
    else:
        return timer
    return None


@app.event
async def connect(sid: str, environ: dict[str, Any]) -> bool:
    """Handle a client connecting to the socket."""
    raw_id = environ.get('HTTP_Blitztime-Timer', None)
    if not raw_id:
        return False
    try:
        timer_id = int(raw_id)
    except ValueError:
        return False
    token = environ.get('HTTP_Authorization', None)
    if token:
        side = GameTimer.get_timer_side(timer_id, token)
        if isinstance(side, GameTimer):
            # "side" is actually the timer.
            side.manager_session_id = sid
            side.observers += 1
            side.save()
            await send_state(side)
        elif not side:
            return False
        else:
            side.session_id = sid
            side.save()
            await send_state(side.game)
    else:
        game = GameTimer.get_timer(timer_id)
        if not game:
            return False
        game.observers += 1
        game.save()
    app.enter_room(sid, str(timer_id))
    await send_state(side.game)
    return True


@app.event
async def disconnect(sid: str):
    """Handle a client disconnecting."""
    side = GameSide.get_or_none(GameSide.session_id == sid)
    if side:
        side.session_id = None
        side.save()
    else:
        side.game.observers -= 1
        side.game.save()
    await send_state(side.game)


@app.event
async def start_timer(sid: str, data: Any):
    """Start an unstarted timer."""
    side = await get_game_side(sid)
    if not side:
        return
    if side.game.started_at:
        await send_error('Game already started.', sid)
        return
    if side.game.host_id != side.id:
        await send_error('Only host can start game.', sid)
        return
    if not side.game.away:
        await send_error('Away side has not joined yet.', sid)
        return
    side.game.start()
    await send_state(side.game)


@app.event
async def end_turn(sid: str, data: Any):
    """End the client's turn."""
    side = await get_game_side(sid)
    if not side:
        return
    if not side.is_turn:
        await send_error('Not currently your turn.', sid)
        return
    await side.end_turn()
    await send_state(side.game)


@app.event
async def opponent_timed_out(sid: str, data: Any):
    """Check the client's opponent's time."""
    side = await get_game_side(sid)
    if not side:
        return
    if (not side.game.started_at) or side.game.has_ended:
        await send_error('Game is not ongoing.', sid)
        return
    if side.opponent.is_timed_out:
        await send_error('Opponent is not timed out.', sid)
        return
    side.opponent.end_turn()
    await send_state(side.game)


@app.event
async def add_time(sid: str, seconds: int):
    """Add time to both players' clocks."""
    game = await get_game(sid)
    if not game:
        return
    if (not side.game.started_at) or side.game.has_ended:
        await send_error('Game is not ongoing.', sid)
        return
    if not isinstance(seconds, int):
        await send_error('Seconds to add should be an int.', sid)
        return
    time = timedelta(seconds=seconds)
    game.home.total_time += time
    game.away.total_time += time
    game.home.save()
    game.away.save()
    await send_state(game)
