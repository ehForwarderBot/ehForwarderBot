Channel
=======

.. automodule:: ehforwarderbot.channel
    :members:

Common operations
-----------------

Sending messages and statuses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sending messages and statuses to other channels is the most
common operation of a channel. When enough information is gathered
from external sources, the channel would then further process
and pack them into the relevant objects,
i.e. :py:class:`~.message.Message` and :py:class:`~.status.Status`.

When the object is built, the channel should sent it to the coordinator for
following steps.

For now, both :obj:`~.message.Message` and :obj:`~.status.Status` has an
attribute that indicates that where this object would be
delivered to (:attr:`~.message.Message.deliver_to` and
:attr:`~.status.Status.destination_channel`). This is used by
the coordinator when delivering the message. 

Messages MUST be sent using :meth:`.coordinator.send_message`.
Statuses MUST be sent using :meth:`.coordinator.send_status`.

When the object is passed onto the coordinator, it will be
further processed by the middleware and then to its destination.

For example, to send a message to the master channel

.. code-block:: python

    def on_message(self, data: Dict[str, Any]):
        """Callback when a message is received by the slave channel from
        the IM platform.
        """
        # Prepare message content ...
        message = coordinator.send_message(Message(
            chat=chat,
            author=author,
            type=message_type,
            text=text,
            # more details ...
            uid=data['uid'],
            deliver_to=coordinator.master
        ))
        # Post-processing ...

About Channel ID
----------------

With the introduction of instance IDs, it is required to use the
``self.channel_id`` or equivalent instead of any hard-coded
ID or constants while referring to the channel (e.g. while
retrieving the path to the configuration files, creating
chat and message objects, etc).