"""Peewee ORM model definitions."""
from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

import peewee

from playhouse.postgres_ext import JSONField, PostgresqlExtDatabase

import pydantic

from . import config


db = PostgresqlExtDatabase(
    config.DB_NAME,
    user=config.DB_USER,
    password=config.DB_PASSWORD,
    host=config.DB_HOST,
    port=config.DB_PORT,
)

TZ = timezone.utc


def create_token() -> str:
    """Securely generate an authentication token."""
    return base64.b64encode(os.urandom(32)).decode()


class TimedeltaField(peewee.DateTimeField):
    """A field that stores a timedelta as a datetime."""

    def db_value(self, value: timedelta) -> str:
        """Convert the timedelta to a datetime."""
        as_date = datetime.fromtimestamp(value.total_seconds(), tz=TZ)
        return super().db_value(as_date)

    def python_value(self, value: str) -> timedelta:
        """Convert the datetime to a timedelta."""
        as_date: datetime = super().python_value(value)
        return timedelta(seconds=as_date.timestamp())


class TimerStageSettings(pydantic.BaseModel):
    """Settings for one stage of a timer."""

    start_turn: int
    seconds_fixed_per_turn: int
    seconds_incremement_per_turn: int
    initial_seconds: int

    @property
    def fixed_time_per_turn(self) -> timedelta:
        """Get the time per turn as a timedelta."""
        return timedelta(seconds=self.seconds_fixed_per_turn)

    @property
    def increment_per_turn(self) -> timedelta:
        """Get the time increment per turn as a timedelta."""
        return timedelta(seconds=self.seconds_incremement_per_turn)

    @property
    def initial_time(self) -> timedelta:
        """Get the total time allowed as a timedelta."""
        return timedelta(seconds=self.initial_seconds)


class TimerSettings(JSONField):
    """A field that stores timer settings as JSON."""

    def python_value(self, value: Any) -> Optional[list[TimerStageSettings]]:
        """Convert a JSON value to timer settings."""
        value = super().python_value(value)
        if value is None:
            return None
        stages = [TimerStageSettings(**options) for options in value]
        return sorted(stages, key=lambda stage: stage.start_turn)

    def db_value(self, value: Optional[list[TimerStageSettings]]) -> Any:
        """Convert timer settings to a JSON value."""
        if value is None:
            dumped = None
        else:
            dumped = [settings.dict() for settings in value]
        return super().db_value(dumped)


class BaseModel(peewee.Model):
    """Base model to set default settings."""

    class Meta:
        """Peewee settings config."""

        use_legacy_table_names = False
        database = db


class GameSide(BaseModel):
    """One side of a game timer."""

    token = peewee.TextField(default=create_token)
    session_id = peewee.TextField(null=True)
    is_turn = peewee.BooleanField(default=False)
    total_time = TimedeltaField(default=timedelta(0))

    def to_dict(self) -> dict[str, Any]:
        """Get the state of the side as a dict to return as JSON."""
        return {
            'is_turn': self.is_turn,
            'total_time': self.total_time.total_seconds(),
            'connected': bool(self.session_id),
        }

    def end_turn(self):
        """End this side's turn and start the next."""
        now = datetime.now(tz=TZ)
        opponent = self.opponent
        self.is_turn = False
        opponent.is_turn = True
        settings = self.game.get_settings()
        self.game.turn_number += 1
        extra_time = (
            now - self.game.turn_started_at - settings.fixed_time_per_turn
        )
        if extra_time > timedelta(0):
            self.total_time -= extra_time
            if self.total_time < timedelta(0):
                self.game.end()
                return
        self.total_time += settings.increment_per_turn
        if (
                settings.start_turn > 0
                and self.game.turn_number // 2 == settings.start_turn):
            self.total_time = self.game.get_settings().initial_time
        self.game.turn_started_at = now
        self.save()
        opponent.save()
        self.game.save()

    def is_timed_out(self) -> bool:
        """Check if this side is timed out."""
        now = datetime.now(tz=TZ)
        if not self.is_turn:
            return False
        settings = self.game.get_settings()
        extra_time = (
            now - self.game.turn_started_at - settings.fixed_time_per_turn
        )
        if extra_time > timedelta(0):
            return self.total_time - extra_time < timedelta(0)
        return False

    @property
    def opponent(self) -> GameSide:
        """Get the player's opponent."""
        if self.id == self.game.home_id:
            return self.game.away
        else:
            return self.game.home

    @property
    def game(self) -> GameTimer:
        """Get the game this player is from."""
        return GameTimer.get(
            (GameTimer.home == self) | (GameTimer.away == self)
        )


class GameTimer(BaseModel):
    """Timer state for a game."""

    turn_number = peewee.IntegerField(default=-1)
    turn_started_at = peewee.DateTimeField(null=True)
    started_at = peewee.DateTimeField(null=True)
    has_ended = peewee.BooleanField(default=False)
    home = peewee.ForeignKeyField(GameSide, null=True)
    away = peewee.ForeignKeyField(GameSide, null=True)
    settings = TimerSettings()
    observers = peewee.IntegerField(default=0)
    manager_token = peewee.TextField(default=create_token)
    manager_session_id = peewee.TextField(null=True)

    @classmethod
    def get_timer(cls, id: int) -> Optional[GameTimer]:
        """Get a timer by ID, and join on foreign keys."""
        query = cls.select().where(cls.id == id).join(
            GameSide,
            on=(cls.home == GameSide.id) | (cls.away == GameSide.id),
            join_type=peewee.JOIN.LEFT_OUTER
        ).limit(1)
        records = list(query)
        if records:
            return records[0]
        return None

    @classmethod
    def get_timer_side(cls, id: int, token: str) -> Optional[
            Union[GameSide, GameTimer]]:
        """Get a timer by ID and token.

        Second return indicates whether the token is for home or away.
        """
        timer = cls.get_timer(id)
        if not timer:
            return None
        if timer.home and timer.home.token == token:
            return timer.home
        elif timer.away and timer.away.token == token:
            return timer.away
        elif timer.manager_token == token:
            return timer
        return None

    def to_dict(self) -> dict[str, Any]:
        """Get the state of the game as a dict to return as JSON."""
        turn_started_at = (
            self.turn_started_at.timestamp() if self.turn_started_at else None
        )
        started_at = self.started_at.timestamp() if self.started_at else None
        return {
            'id': self.id,
            'turn_number': self.turn_number,
            'turn_started_at': turn_started_at,
            'started_at': started_at,
            'has_ended': self.has_ended,
            'home': self.home.to_dict() if self.home else None,
            'away': self.away.to_dict() if self.away else None,
            'settings': [stage.dict() for stage in self.settings],
            'observers': self.observers,
        }

    def get_settings(self) -> TimerStageSettings:
        """Get the settings for the current stage."""
        turn = max(self.turn_number, 0) // 2
        for stage in reversed(self.settings):
            if stage.start_turn <= turn:
                return stage
        # We should never get here, since one stage should have start_turn=0.
        raise ValueError('No first stage found.')

    def start(self):
        """Start the game, and home's timer."""
        now = datetime.now(tz=TZ)
        self.turn_number = 0
        self.home.is_turn = True
        self.turn_started_at = now
        self.started_at = now
        self.save()

    def end(self):
        """End the game."""
        self.has_ended = True
        self.home.save()
        self.away.save()
        self.save()

    def get_current_side(self) -> Optional[GameSide]:
        """Get the player whose turn it currently is."""
        if self.home.is_turn:
            return self.home
        if self.away.is_turn:
            return self.away
        return None


db.create_tables([GameSide, GameTimer])
