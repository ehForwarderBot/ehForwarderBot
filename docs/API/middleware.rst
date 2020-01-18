Middleware
=============

.. autoclass:: ehforwarderbot.Middleware
    :members:

About Middleware ID
-------------------

With the introduction of instance IDs, it is required to use the
``self.middleware_id`` or equivalent instead of any hard-coded
ID or constants while referring to the middleware ID (e.g. while
retrieving the path to the configuration files, etc).

Accept commands from user through Master Channel
------------------------------------------------

Despite we do not limit how the User interact with your
middleware, there are 2 common ways to do it through a
master channel.

Capture messages
~~~~~~~~~~~~~~~~
If the action is chat-specific, you can capture messages with a
specific pattern. Try to make the pattern easy to type but unique
enough so that you don't accidentally catch messages that were
meant to sent to the chat.

You may also construct a virtual chat or chat member of type "System"
to give responses to the User.

“Additional features”
~~~~~~~~~~~~~~~~~~~~~
If the action is not specific to any chat, but to the system
as a whole, we have provided the same command line-like interface
as in slave channels to middlewares as well. Details are available
at :ref:`slave-additional-features`.

Chat-specific interactions
--------------------------

Middlewares can have chat-specific interactions through capturing messages
and reply to them with a chat member created by the middleware.

The following code is an example of a middleware that interact with the user
by capturing messages.

When the master channel sends a message with a text starts with ``time```,
the middleware captures this message and reply with the name of the chat
and current time on the server. The message captured is not delivered to
any following middlewares or the slave channel.

.. code-block:: python

    def process_message(self: Middleware, message: Message) -> Optional[Message]:
        if message.deliver_to != coordinator.master and \  # sent from master channel
            text.startswith('time`'):

            # Make a system chat object.
            # For difference between `make_system_member()` and `add_system_member()`,
            # see their descriptions above.
            author = message.chat.make_system_member(
                uid="__middleware_example_time_reporter__",
                name="Time reporter",
                middleware=self
            )

            # Make a reply message
            reply = Message(
                uid=f"__middleware_example_{uuid.uuid4()}__",
                text=f"Greetings from chat {message.chat.name} on {datetime.now().strftime('%c')}.",
                chat=chat,
                author=author,  # Using the new chat we created before
                type=MsgType.Text,
                target=message,  # Quoting the incoming message
                deliver_to=coordinator.master  # message is to be delivered to master
            )
            # Send the message back to master channel
            coordinator.send_message(reply)

            # Capture the message to prevent it from being delivered to following middlewares
            # and the slave channel.
            return None

        # Continue to deliver messages not matching the pattern above.
        return message
