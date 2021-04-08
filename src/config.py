"""Read JSON config for the bot."""
import json
import logging
import pathlib


BASE_PATH = pathlib.Path(__file__).parent.parent

with open(str(BASE_PATH / 'config.json')) as f:
    config = json.load(f)


def get_log_level(field: str, default: int) -> int:
    """Parse a logging level field from the config file."""
    raw = config.get(field)
    if not raw:
        return default
    return {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
        'notset': logging.NOTSET,
        'none': logging.NOTSET,
    }[raw.lower()]


HTTP_LOG_LEVEL = get_log_level('http_log_level', logging.INFO)
WS_LOG_LEVEL = get_log_level('ws_log_level', logging.INFO)

DB_NAME = config.get('db_name', 'blitztime')
DB_USER = config.get('db_user', 'blitztime')
DB_HOST = config.get('db_host', '127.0.0.1')
DB_PORT = config.get('db_port', 5432)
DB_PASSWORD = config['db_password']
DB_LOG_LEVEL = get_log_level('db_log_level', logging.INFO)
