"""Sanic app for both WebSocket connections and HTTP endpoints.

To run, do:

$ python3 -m sanic src.app

This is production-ready.
"""
import logging

from . import config, http, ws


LOGS = (
    ('peewee', config.DB_LOG_LEVEL),
    ('sanic.root', config.HTTP_LOG_LEVEL),
    ('socketio', config.WS_LOG_LEVEL),
    ('engineio', config.WS_LOG_LEVEL)
)
for log, level in LOGS:
    logger = logging.getLogger(log)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '{levelname}:{name}:{message}', style='{'
    ))
    logger.addHandler(handler)
    logger.setLevel(level)

ws.app.attach(http.app)
app = http.app
