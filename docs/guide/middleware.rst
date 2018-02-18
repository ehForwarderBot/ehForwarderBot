Middlewares
===========

Middlewares works in between the master channel and
slave channels, they look through messages and statuses
delivered between channels, passing them on, make changes
or discarding them, one after another.

Like channels, middlewares will also each have an instance
per EFB session, managed by the coordinator. However, they
don't have centrally polling threads, which means if a
middleware wants to have a polling thread or something
similar running in the background, it has to stop the thread
using Python's ``atexit`` or otherwise.

Message and Status Processing
-----------------------------

Each middleware by default has 2 methods, :meth:`~.ehforwarderbot.EFBMiddleware.process_message`
which processes message objects, and :meth:`~.ehforwarderbot.EFBMiddleware.process_status`
which processes status objects. If they are not overridden,
they will not touch on the object and pass it on as is.

To modify an object, just override the relative method and
make changes to it. To discard an object, simply return ``None``.
When an object is discarded, it will not be passed further
to other middlewares or channels, which means a middleware
or a channel should never receive a ``None`` message or
status.

Other Usages
------------

Having rather few limitation compare to channels, middlewares are
rather easy to write, which allows it to do more than
just intercept messages and statuses.

Some ideas:

- Periodic broadcast to master / slave channels
- Integration with chat bots
- Automated operations on vendor-specific commands /
  additional features
- Share user session from slave channel with other
  programs
- etc...