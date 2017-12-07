EFBChannel
==========

.. autoclass:: ehforwarderbot.EFBChannel
    :members:

Common operations
-----------------

Sending messages and statuses
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sending messages and statuses to other channels is the most
common operation of a channel. When the channel has gathered 
enough information from external soruces, it should be 
further processed and packed into the relative objects, 
i.e. :obj:`.EFBMsg` and :obj:`.EFBStatus`.

When the related information is packed into their relative 
objects, it can be sent to the coordinator for the next
step. 

For now, both :obj:`.EFBMsg` and :obj:`.EFBStatus` has an
attribute that indicates that where this object should be
delivered to (:attr:`.EFBMsg.deliver_to` and 
:attr:`.EFBStatus.destination_cahnnel`). This is used by 
the coordinator when delivering the message. 

For messages, it can be delivered with :meth:`.coordinator.send_message`,
and statuses can be delivered with :meth:`.coordinator.send_status`.

When the object is passed onto the coordinator, it will be
further processed by the middleware.