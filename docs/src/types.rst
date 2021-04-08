=====
Types
=====

These are the types of JSON object the server may return/accept, as referenced elsewhere in the docs.

``Timer``
=========

The state of a game timer.

Fields:

- ``id``: ``int``
- ``turn_number``: ``int`` (note that this is updated once every turn, rather than just once every round - for each turn one user takes, the turn number will be two higher)
- ``turn_started_at``: ``datetime`` or ``null``, the time the current turn started (see below)
- ``started_at``: ``datetime`` or ``null``, the time the first move started (see below)
- ``has_ended``: ``bool``
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
