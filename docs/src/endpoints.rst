==============
HTTP Endpoints
==============

``GET /timer/{timer_id}``
=========================

Get information on a timer.

Parameters:

- ``timer_id`` The ID of a timer, ``int`` in path.

Returns:

- a ``Timer`` object.

Raises: ``422`` (bad timer ID), ``404`` (timer not found) or ``500`` (server error).

``POST /timer/{timer_id}/away``
===============================

Join the away side of a timer.

Parameters:

- ``timer_id`` The ID of a timer, ``int`` in path

Returns (JSON body):

- ``token`` A string, the token to use to connect.
- ``timer`` An int, the ID of the new timer.

Raises: ``422`` (bad timer ID), ``404`` (timer not found), ``409`` (timer already has away) or ``500`` (server error).

``POST /timer``
===============

Create a new timer.

Parameters:

- an array of ``StageSettings`` objects in a JSON body.

Returns (JSON body):

- ``token`` A string, the token to use to connect.
- ``timer`` An int, the ID of the new timer.

Raises: ``422`` (bad settings) or ``500`` (server error).

``GET /stats``
==============

Get stats relating to the app.

Returns:

- an ``AppStats`` object.

Raises: ``500`` (server error).
