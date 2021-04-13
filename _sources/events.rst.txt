================
Socket.IO Events
================

Connections to the Socket.IO socket can be made at the base URL. The ``Blitztime-Timer`` must be set to the ID of the timer you wish to connect to. Unless you are joining as an observer, you must also set the ``Authorization`` header to the token you've receieved (see HTTP endpoints).

Client-sent events
==================

``start_timer``
---------------

Start a timer that has not yet started. This can only be sent once the away side has joined. No data should be included.

If this is a managed game, only the manager can send this. Otherwise, only the home player can.

``end_turn``
------------

End the turn of the side who's turn it currently is. No data should be included.

If this is a managed game, only the manager can send this. Otherwise, only the player who's turn it currently is can.

``timeout``
-----------

Instruct the server to re-check the game, and end the game if necessary.  No data should be included. This can be sent by any client, even an observer.

This is aliased to ``opponent_timed_out`` for backwards compatibility, but this is deprecated.

``add_time``
------------

Add time to both the home and away timers. Time should be given in seconds as the event data, an integer. This can only be sent by a manager. If the game is not managed, this event cannot be sent.

``end_game``
------------

End the game before the timer has run out (eg. defeat, resignation).

If this is a managed game, only the manager can send this. Otherwise, only a player can.


Server-sent events
==================

``state``
---------

This indicates that the current state of the game has changed. It includes as data a ``Timer`` object.

``error``
---------

This indicates that the client sent an erroneous event. The ``detail`` field may include more information.
