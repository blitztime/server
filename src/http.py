"""Sanic app for HTTP endpoints."""
import functools
import traceback
from typing import Any, Awaitable, Callable

from peewee import fn

import pydantic

from sanic import Request, Sanic
from sanic.response import HTTPResponse, json

from sanic_cors import CORS

from .models import GameSide, GameTimer, Session, TimerStageSettings


app = Sanic(name='Blitztime', configure_logging=False)
CORS(app)

View = Callable[..., Awaitable[HTTPResponse]]


class TimerSettings(pydantic.BaseModel):
    """Options for creating a timer."""

    stages: list[TimerStageSettings]
    as_manager: bool = False


class ApiError(Exception):
    """Exception raised when the API detects an error in input."""

    def __init__(self, code: int, detail: str):
        """Store the details of the error."""
        super().__init__(detail)
        self.code = code
        self.detail = detail


def catch_exceptions(view: View) -> View:
    """Wrap a view to catch errors and return them as JSON."""
    @functools.wraps(view)
    async def wrapped(
            request: Request, *args: Any, **kwargs: Any) -> HTTPResponse:
        """Attempt to call the base view, and catch errors."""
        try:
            return await view(request, *args, **kwargs)
        except ApiError as error:
            return json({'detail': error.detail}, status=error.code)
        except pydantic.ValidationError as error:
            return json({'detail': str(error)})
        except Exception as error:
            print('Traceback (most recent call last):')
            traceback.print_tb(error.__traceback__)
            print(f'{type(error).__name__}: {error}.')
            return json({'detail': str(error)}, status=500)
    return wrapped


@app.get('/timer/<timer_id:int>')
@catch_exceptions
async def get_timer(request: Request, timer_id: int) -> HTTPResponse:
    """Get information on a timer."""
    timer = GameTimer.get_timer(timer_id)
    if timer is None:
        raise ApiError(404, 'Timer not found.')
    return json(timer.to_dict())


@app.post('/timer/<timer_id:int>/<side:int>')
@catch_exceptions
async def join_timer(
        request: Request, timer_id: int, side: int) -> HTTPResponse:
    """Join the home or away side of a timer."""
    if side < 0 or side > 2:
        raise ApiError(422, 'Side must be 0 (home) or 1 (away).')
    timer = GameTimer.get_timer(timer_id)
    if timer is None:
        raise ApiError(404, 'Timer not found.')
    if (timer.home and side == 0) or (timer.away and side == 1):
        raise ApiError(409, 'Side already joined.')
    game_side = GameSide.create()
    if side == 0:
        timer.home = game_side
    else:
        timer.away = game_side
    timer.save()
    return json({'token': game_side.token, 'timer': timer_id})


@app.post('/timer')
@catch_exceptions
async def create_timer(request: Request) -> HTTPResponse:
    """Create a new timer."""
    options = TimerSettings.parse_obj(request.json)
    if options.stages[0].start_turn != 0:
        raise ApiError(422, 'First stage must start on turn 0.')
    if options.as_manager:
        timer = GameTimer.create(settings=options.stages)
        token = timer.manager_token
    else:
        side = GameSide.create()
        timer = GameTimer.create(home=side, settings=options.stages)
        token = side.token
    return json({'token': token, 'timer': timer.id})


@app.get('/stats')
@catch_exceptions
async def get_stats(request: Request) -> HTTPResponse:
    """Get stats on the app."""
    timers, ongoing = GameTimer.select(
        fn.COUNT(GameTimer.id),
        fn.COUNT(GameTimer.id).filter(~GameTimer.has_ended),
    ).scalar(as_tuple=True)
    connected = Session.select().count()
    return json({
        'all_timers': timers,
        'ongoing_timers': ongoing,
        'connected': connected,
    })
