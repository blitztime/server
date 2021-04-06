======
Errors
======

When the server detects a client-side or server-side error, it will send an ``Error`` object.

When the error is detected in an HTTP request, this will be sent as the body of the response, along with a relevant status code. When the error is detected in a Socket.IO event, it will be sent as the data for an event called ``error``.
