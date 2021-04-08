================
Socket.IO Events
================

Connections to the Socket.IO socket can be made at the base URL. The ``Blitztime-Timer`` must be set to the ID of the timer you wish to connect to. Unless you are joining as an observer, you must also set the ``Authorization`` header to the token you've receieved (see HTTP endpoints).

Observers may not send any events.

Client-sent events
==================

``start_timer``
---------------

Start a timer that has not yet started. This can only be sent by the host, once the away side has joined. No data should be included.

``end_turn``
------------

End the turn of the connected client. This may only be sent when it is the client's turn. No data should be included. This can only be sent using a player token.

``opponent_timed_out``
----------------------

Should be sent by one client when that client's opponent has timed out. This will instruct the server to re-check the game, and end the game if necessary. If a client notices that it itself has timed out, it should instead use ``end_turn``. No data should be included. This can only be sent using a player token.

``add_time``
------------

Add time to both the home and away timers. Time should be given in seconds as the event data, an integer. This can only be sent using a manager token.

Server-sent events
==================

``state``
---------

This indicates that the current state of the game has changed. It includes as data a ``Timer`` object.

``error``
---------

This indicates that the client sent an erroneous event. The ``detail`` field may include more information.
