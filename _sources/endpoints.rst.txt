==============
HTTP Endpoints
==============

``GET /timer/{timer_id}``
=========================

Get information on a timer.

Parameters:

- ``timer_id``: The ID of a timer, ``int`` in path.

Returns:

- a ``Timer`` object.

Raises: ``422`` (bad timer ID), ``404`` (timer not found) or ``500`` (server error).

``POST /timer/{timer_id}/{side}``
=================================

Join the home or away side of a timer.

Parameters (path):

- ``timer_id``: The ID of a timer, ``int``.
- ``side``: Either ``0`` (home) or ``1`` (away).

Returns (JSON body):

- ``token``: A string, the token to use to connect.
- ``timer``: An int, the ID of the new timer.

Raises: ``422`` (bad timer ID), ``404`` (timer not found), ``409`` (timer already has away) or ``500`` (server error).

``POST /timer``
===============

Create a new timer.

Parameters (JSON body):

- ``stages``: an array of ``StageSettings`` objects.
- ``as_manager``: optional ``boolean``, default false.

Returns (JSON body):

- ``token``: A string, the token to use to connect.
- ``timer``: An int, the ID of the new timer.

Raises: ``422`` (bad settings) or ``500`` (server error).

If ``as_manager`` is ``false``, you will be added to the game as the host, and the token returned will be a player token. Otherwise, no host will be added and the token returned will be a manager token.

``GET /stats``
==============

Get stats relating to the app.

Returns (JSON body):

- an ``AppStats`` object.

Raises: ``500`` (server error).
