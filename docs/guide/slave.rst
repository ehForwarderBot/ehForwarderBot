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

In most of the cases, slave channels SHOULD be
identified as one single user from the IM platform,
instead of a bot. You should only use a bot for slave
channels when:

- the IM platform puts no difference between a user
  and a bot, or
- bots on the IM platform can do exactly same things,
  if not more, as a user, and bots can be created
  easier than user account.

.. _slave-additional-features:

Additional features
-------------------

Slave channels can offer more functions than what EFB
requires, such as creating groups, search for friends, 
etc, via *additional features*.

Such features are accessed by the user in a CLI-like
style. An “additional feature” method MUST only take one
string parameter aside from ``self``, and wrap it with 
:meth:`~ehforwarderbot.utils.extra` decorator. The ``extra``
decorator takes 2 arguments: ``name`` -- a short name of the
feature, and ``desc`` -- a description of the feature with
its usage.

``desc`` SHOULD describe what the feature does and how
to use it. It's more like the help text for an CLI program. 
Since method of invoking the feature depends on the
implementation of the master channel, you SHOULD use
``"{function_name}"`` as its name in ``desc``,
and master channel will replace it with respective name
depend on their implementation.

The method MUST in the end return a string, which will
be shown to the user as its result, or ``None`` to notify the master channel
there will be further interaction happen. Depending on the
functionality of the feature, it may be just a simple
success message, or a long chunk of results.

The callable MUST NOT raise any exception to its caller.
Any exceptions occurred within should be ``expect``\ ed and
processed.

Callable name of such methods has a more strict standard
than a normal Python 3 identifier name, for compatibility 
reason. An additional feature callable name MUST:

* be case sensitive
* include only upper and lower-case letters, digits, and underscore.
* does not start with a digit.
* be in a length between 1 and 20 inclusive
* *be as short and concise as possible, but keep understandable*

It can be expressed in a regular expression as::

    ^[A-Za-z][A-Za-z0-9_]{0,19}$

An example is as follows:

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

A message can be attached with a ``list`` of commands, in 
which each of them has:

* a human-friendly name,
* a callable name,
* a ``list`` of positional arguments (``*args``), and
* a ``dict`` of keyword arguments (``**kwargs``)

When the User clicked the button, the corresponding method
of your channel will be called with provided arguments.

Note that all such methods MUST return a ``str`` as a 
respond to the action from user, and they MUST NOT raise
any exception to its caller. Any exceptions occurred within
MUST be ``expect``\ ed and processed.


Message delivery
----------------

Slave channels SHOULD deliver all messages that the IM
provides, including what the User sent outside of this channel.
But it SHOULD NOT deliver message sent from the master channel
again back to the master channel as a new message.

  
Implementation details
----------------------

See :class:`.SlaveChannel`.