"""Sanic app for HTTP endpoints."""
import functools
import traceback
from typing import Any, Awaitable, Callable

from peewee import fn

import pydantic

from sanic import Request, Sanic
from sanic.response import HTTPResponse, json

from .models import GameSide, GameTimer, TimerStageSettings


app = Sanic(name='Blitztime', configure_logging=False)

View = Callable[..., Awaitable[HTTPResponse]]


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


@app.post('/timer/<timer_id:int>/away')
@catch_exceptions
async def join_game(request: Request, timer_id: int) -> HTTPResponse:
    """Join the away side of a timer."""
    timer = GameTimer.get_timer(timer_id)
    if timer is None:
        raise ApiError(404, 'Timer not found.')
    if timer.has_away_joined:
        raise ApiError(409, 'Game already full.')
    side = GameSide.create()
    timer.away = side
    timer.save()
    return json({'token': side.token, 'timer': timer_id})


@app.post('/timer')
@catch_exceptions
async def create_timer(request: Request) -> HTTPResponse:
    """Create a new timer."""
    side = GameSide.create()
    settings = pydantic.parse_obj_as(list[TimerStageSettings], request.json)
    if settings[0].start_turn != 0:
        raise ApiError(422, 'First stage must start on turn 0.')
    timer = GameTimer.create(home=side, settings=settings)
    return json({'token': side.token, 'timer': timer.id})


@app.get('/stats')
@catch_exceptions
async def get_stats(request: Request) -> HTTPResponse:
    """Get stats on the app."""
    timers, ongoing, observers = GameTimer.select(
        fn.COUNT(GameTimer.id),
        fn.COUNT(GameTimer.id).filter(~GameTimer.has_ended),
        fn.COALESCE(fn.SUM(GameTimer.observers), 0),
    ).scalar(as_tuple=True)
    print(timers, ongoing, observers)
    players = GameSide.select().where(GameSide.token.is_null(False)).count()
    return json({
        'all_timers': timers,
        'ongoing_timers': ongoing,
        'connected': observers + players,
    })
