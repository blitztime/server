# Blitztime API Server

Blitztime is an online game timer for Polytopia.

It is very similar to, and probably usable as a replacement for, a chess timer.

This is an implementation of the Blitztime API server in Python, using Peewee as an ORM for PostgreSQL, Sanic as an HTTP server and python-socketio for Socket.IO sockets (a layer on top of WebSockets, also providing alternative transports).

## Setup

1. [Install Python 3.9+ (3.x where x >= 9).](https://www.python.org/downloads/)
2. [Install Poetry.](https://python-poetry.org/docs/#installation)
3. From the directory containing this README, run `poetry install --no-dev`.
4. [Install PostgreSQL, and create a database for Blitztime.](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04)
5. Create a file called `config.json` in the directory containing this README. See "Configuration" below for required and allowed options.
6. To run the server, do `poetry run poe serve`.

## Configuration

The following options are available in the configuration file:

| Name              | Default     | Description                       |
|:-----------------:|:-----------:|:----------------------------------|
| `allowed_origins` | `[]`        | Allowed origins for CORS headers. |
| `db_name`         | `blitztime` | Name of the database.             |
| `db_user`         | `blitztime` | Username for the database.        |
| `db_host`         | `127.0.0.1` | Host address of the database.     |
| `db_port`         | `5432`      | Host port of the database.        |
| `db_password`     | Required    | Password for the database.        |
| `db_log_level`    | `INFO`      | Logging level for Peewee.         |
| `http_log_level`  | `INFO`      | Logging level for Sanic.          |
| `ws_log_level`    | `INFO`      | Logging level for Socket.IO.      |

To get every executed SQL statement logged to stdout, set `db_log_level` to `DEBUG`.

## Development

To install development dependencies, just run `poetry install`. This project has a strict set of linting rules. Do `poetry run poe lint` to lint.

Source code for the docs is in `docs/src`. You can build the docs with `poetry run poe docs`, and then open them in your favourite browser with, for example, `firefox docs/out`. Avoid committing `docs/out` to keep diffs smaller.
