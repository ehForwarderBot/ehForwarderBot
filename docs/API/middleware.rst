EFBMiddleware
=============

.. autoclass:: ehforwarderbot.EFBMiddleware
    :members:

About Middleware ID
-------------------

With the introduction of instance IDs, it is required to use the
``self.middleware_id`` or equivalent instead of any hard-coded
ID or constants while referring to the middleware ID (e.g. while
retrieving the path to the configuration files, etc).

Receive commands with user through Master Channel
-------------------------------------------------

Despite we do not limit how users can perform actions to your
middleware, there are 2 common ways to do it through a
master channel.

Capture messages
~~~~~~~~~~~~~~~~
If the action is chat-specific, you might want to catch
messages that match specific pattern. Try to make the pattern
easy to type but unique enough so that you don't accidentally
catch messages that were meant to sent to the chat.

You may also construct a virtual sender of type "System" to
give response to the user.

"Additional features"
~~~~~~~~~~~~~~~~~~~~~
If the action is not specific to any chat, but to the system
as a whole, we have provided the same command line-like interface
as in slave channels to middlewares as well. Details are available
at :ref:`slave-additional-features`.
