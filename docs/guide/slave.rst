Slave channels
==============

Slave channel is more like a wrap over an API of IM,
it encloses messages from the IM into appropriate
objects and deliver it to the master channel.

Although we suggest that slave channel should match
with an IM platform, but you may try to model it for
anything that can deliver information as messages, and
has a limited list of end-points to deliver messages
to and from as chats.

In most of the cases, slave channels should be
identified as one single user from the IM platform,
instead of a bot.  We suggest you to use a bot for
slave channels only when

- the IM platform puts no difference between a user
  and a bot, or
- bots on the IM platform can do exactly same things,
  if not more, as a user, and bots can be created
  easier than user account.

Methods to be implemented
-------------------------

Below is a list of methods that are required to be 
implemented by the slave channel.

* :meth:`.EFBChannel.get_chat_picture`
* :meth:`.EFBChannel.get_chat`
* :meth:`.EFBChannel.get_chats`
* :meth:`.EFBChannel.poll`
* :meth:`.EFBChannel.send_message`
* :meth:`.EFBChannel.send_status`

.. _slave-additional-features:

Additional features
-------------------

Slave channels can offer more functions than what EFB
requires, such as creating groups, search for friends, 
etc, via *additional features*.

Such features are accessed by the user in a CLI-like
style. An "additional feature" method should only take one
string parameter aside from ``self``, and wrap it with 
:meth:`~ehforwarderbot.utils.extra` decorator. The ``extra``
decorator takes 2 arguments: ``name`` -- a short name of the
feature, and ``desc`` -- a description of the feature with
its usage.

``desc`` should describe what the feature does and how
to use it. It's more like the help text for an CLI program. 
Since method of invoking the feature depends on the
implementation of the master channel, you should use 
``"{function_name}"`` as its name in ``desc``,
and master channel will replace it with respective name
depend on their implementation.

The method should in the end return a string, which will 
be shown to the user as its result. Depending on the 
functionality of the feature, it may be just a simple
success message, or a long chunk of results.

The callable should not raise any exception to its caller.
Any exceptions occurred within should be ``expect``\ ed and
processed.

Callable name of such methods has a more strict standard
than a normal Python 3 identifier name, for compatibility 
reason. An additional feature callable name should:

* be case sensitive
* include only upper and lower-case letters, digits, and underscore.
* does not start with a digit.
* be in a length between 1 and 20 inclusive
* *be as short and concise as possible, but keep understandable*

In RegEx, it's can be expressed as::

    ^[A-Za-z][A-Za-z0-9_]{0,19}$

.. admonition:: Example
    :class: tip

    .. code-block:: python
    
        @extra(name="Echo",
               desc="Return back the same string from input.\n"
                    "Usage:\n"
                    "    {function_name} text")
        def echo(self, arguments: str = "") -> str:
            return arguments

Message commands
----------------

Message commands are usually sent by slave channels so that
users can respond to certain messages that has specific 
required actions.

Possible cases when message commands could be useful:

* Add as friends when a contact card is received.
* Accept or decline when a friend request is received.
* Vote to a voting message.
* Like / thumb up to a message if applicable.

A message can be attached with a ``list`` of commands, in 
which each of them has:

* a human-friendly name,
* a callable name,
* a ``list`` of positional arguments (``*args``), and
* a ``dict`` of keyword arguments (``**kwargs``)

When a user clicked the button, the corresponding method
of your channel will be called with provided arguments.

Note that all such methods MUST return a ``str`` as a 
respond to the action from user, and they should NOT raise
any exception to its caller. Any exceptions occurred within
should be ``expect``\ ed and processed.


Message delivery
----------------

Slave channels should deliver all messages that the IM
provides, including what the user sent not with this channel.
But it should not deliver message sent from the master channel
again back to the master channel as a new message.

Messages should be delivered regardless of the notification
settings user had in the IM platform, but you can:

- include notification settings in the ``vendor_specific``
  section of the chats or message object, whichever is
  applicable, and then let middlewares to decide whether to
  deliver it; or
- provide options in the slave channel to ignore certain messages
  provided by the IM server.
  
Implementation details
----------------------

See :class:`EFBChannel`.