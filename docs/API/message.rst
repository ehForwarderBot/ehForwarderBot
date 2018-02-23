EFBMsg
======

.. autoclass:: ehforwarderbot.EFBMsg
    :members:

.. automodule:: ehforwarderbot.message
    :members:
    :show-inheritance:
    :member-order: bysource
    :exclude-members: EFBMsg

Examples
--------

Prelude: Defining related chats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    master = coordinator.master
    slave = coordinator.slave['ehforwarderbot.channels.slave.eh.demo'] 
    alice = slave.get_chat(chat_uid="alice101")
    bob = slave.get_chat(chat_uid="bobrocks")
    wonderland = slave.get_chat(chat_uid="thewonderlandgroup")

Initialization and marking chats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    message = EFBMsg()

    # 1. a chat delivered from slave to master, or
    message.deliver_to = master
    message.chat = wonderland
    message.author = alice

    # 2. a chat delivered from master to slave
    message.deliver_to = slave
    message.chat = alice
    message.author = EFBChat(slave).self()

Marking message references (targeted message)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Information in this part should be retrieved 
    # from recorded historical data.
    message.target = EFBMsg()
    message.target.chat = alice
    message.target.author = alice
    message.target.text = "Hello, world." 
    message.target.type = MsgType.Text
    message.target.uid = "100000002"

Edit a previously sent message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    message.edit = True
    message.uid = "100000003"
    # Message UID should be the UID from the slave channel
    # regardless of where the message is delivered to.

Type-specific Information
~~~~~~~~~~~~~~~~~~~~~~~~~

1. Text message
    .. code-block:: python
    
        message.type = MsgType.Text
        message.text = "Hello, Wonderland."

2. Media message
    Information related to media processing is described
    in :doc:`/guide/media_processing`.

    The example below is for image (picture) messages.
    Audio, file, video, sticker works in the same way.

    In non-text messages, the ``text`` attribute is optional.

    .. code-block:: python

        message.type = MsgType.Image
        message.text = "Image caption"
        message.file = NamedTemporaryFile(suffix=".png")
        message.file.write(binary_data)
        message.filename = "holiday photo.png"
        message.mime = "image/png"

3. Location message
    In non-text messages, the ``text`` attribute is optional.

    .. code-block:: python

        message.type = MsgType.Location
        message.text = "I'm here! Come and find me!"
        message.attributes = EFBMsgLocationAttribute(51.4826, -0.0077)

4. Link message
    In non-text messages, the ``text`` attribute is optional.

    .. code-block:: python

        message.type = MsgType.Link
        message.text = "Check it out!"
        message.attributes = EFBMsgLinkAttribute(
            title="Example Domain",
            description="This domain is established to be used for illustrative examples in documents.",
            image="https://example.com/thumbnail.png",
            url="https://example.com"
        )

5. Status
    In non-text messages, the ``text`` attribute is optional.

    .. code-block:: python

        message.type = MsgType.Status
        message.attributes = EFBMsgStatusAttribute(EFBMsgStatusAttribute.TYPING)

6. Unsupported message
    ``text`` attribute is required for this type of message.

    .. code-block:: python

        message.type = MsgType.Unsupported
        message.text = "Alice requested USD 10.00 from you. "
                       "Please continue from your client."

Additional information
~~~~~~~~~~~~~~~~~~~~~~

1. Substitution
    .. code-block:: python

        message.text = "Hey @alice, @bob, and @all. Attention!"
        message.substitutions = EFBMsgSubstitutions({
            (4, 10): alice,
            (12, 16): bob,
            (22, 26): EFBChat(slave).self()
        })

2. Commands
    .. code-block:: python

        message.text = "Carol sent you a friend request."
        message.commands = EFBMsgCommands([
            EFBCommand(name="Accept", callable_name="accept_friend_request",
                       kwargs={"username": "carol_jhonos", "hash": "2a9329bd93f"}),
            EFBCommand(name="Decline", callable_name="decline_friend_request",
                       kwargs={"username": "carol_jhonos", "hash": "2a9329bd93f"})
        ])
