=====
Types
=====

These are the types of JSON entity the server may return/accept, as referenced elsewhere in the docs.

``Timer``
=========

The state of a game timer.

Fields:

- ``id``: ``int``
- ``turn_number``: ``int`` (note that this is updated once every turn, rather than just once every round - for each turn one user takes, the turn number will be two higher)
- ``turn_started_at``: ``datetime`` or ``null``, the time the current turn started (see below)
- ``started_at``: ``datetime`` or ``null``, the time the first move started (see below)
- ``has_ended``: ``bool``
- ``end_reporter``: ``UserPosition`` (see below) or ``null``, the side that reported the end, if the game was ended early.
- ``home``: ``TimerSide`` (see below) or ``null``
- ``away``: ``TimerSide`` (see below) or ``null``
- ``settings``: ``array`` of ``StageSettings`` (see below)
- ``observers``: ``int``

``TimerSide``
=============

The state of one side of a timer.

Fields:

- ``is_turn``: ``boolean``
- ``total_time``: ``timedelta`` as of the start of the last turn, see below
- ``connected``: ``boolean``

``StageSettings``
=================

Settings for one stage of a timer.

Fields:

- ``start_turn``: ``timedelta`` (see below)
- ``seconds_fixed_per_turn``: ``timedelta`` (see below)
- ``seconds_incremement_per_turn``: ``timedelta`` (see below)
- ``initial_seconds``: ``timedelta`` (see below)

``AppStats``
============

Stats relating to usage of the app.

Fields:

- ``all_timers``: ``int``
- ``ongoing_timers``: ``int``
- ``connected``: ``int``

``UserPosition``
================

An ``int`` defining the position of a user in a game. Possible values:

- ``-2``: Observer
- ``-1``: Manager
- ``0``: Home
- ``1``: Away

Note that there is currently no situation in which ``-2`` would be used.

``Error``
=========

An error, either client-side or server-side.

Fields:

- ``detail``: ``string``

``timedelta``
=============

This is a ``real``, representing a number of seconds.

``datetime``
============

Like a ``timedelta``, but represents seconds since the Unix epoch.
