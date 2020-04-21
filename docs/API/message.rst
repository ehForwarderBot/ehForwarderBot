Message
=======
.. py:currentmodule:: ehforwarderbot.message

.. rubric:: Summary

.. autosummary::

    Message
    LinkAttribute
    LocationAttribute
    StatusAttribute
    MessageCommands
    MessageCommand
    Substitutions

.. rubric:: Classes

.. autoclass:: ehforwarderbot.message.Message
    :members:

.. automodule:: ehforwarderbot.message
    :members:
    :show-inheritance:
    :member-order: bysource
    :exclude-members: Message

Examples
--------

Prelude: Defining related chats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    master: MasterChannel = coordinator.master
    slave: SlaveChannel = coordinator.slave['demo.slave']
    alice: PrivateChat = slave.get_chat("alice101")
    bob: PrivateChat = slave.get_chat("bobrocks")
    wonderland: GroupChat = slave.get_chat("thewonderlandgroup")
    wonderland_alice: ChatMember = wonderland.get_member("alice101")

Initialization and marking chats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. A message delivered from slave channel to master channel

    .. code-block:: python

        message = Message(
            deliver_to=master,
            chat=wonderland,
            author=wonderland_alice,
            # More attributes go here...
        )

2. A message delivered from master channel to slave channel

    .. code-block:: python

        message = Message(
            deliver_to=slave,
            chat=alice,
            author=alice.self,
            # More attributes go here...
        )

Quoting a previous message (targeted message)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Data of the quoted message SHOULD be retrieved from recorded historical data.
:attr:`.Message.deliver_to` is not required for quoted message, and
complete data is not required here. For details, see :attr:`.Message.target`.

You MAY use the :meth:`.Channel.get_message` method to get the message object
from the sending channel, but this might not always be possible depending on
the implementation of the channel.

.. code-block:: python

    message.target = Message(
        chat=alice,
        author=alice.other,
        text="Hello, world.",
        type=MsgType.Text,
        uid=MessageID("100000002")
    )

Edit a previously sent message
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Message ID MUST be the ID from the slave channel regardless of where the
message is delivered to.

.. code-block:: python

    message.edit = True
    message.uid = MessageID("100000003")

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

    In non-text messages, the ``text`` attribute MAY be an empty string.

    .. code-block:: python

        message.type = MsgType.Image
        message.text = "Image caption"
        message.file = NamedTemporaryFile(suffix=".png")
        message.file.write(binary_data)
        message.file.seek(0)
        message.filename = "holiday photo.png"
        message.mime = "image/png"

3. Location message

    In non-text messages, the ``text`` attribute MAY be an empty string.

    .. code-block:: python

        message.type = MsgType.Location
        message.text = "I'm here! Come and find me!"
        message.attributes = LocationAttribute(51.4826, -0.0077)

4. Link message

    In non-text messages, the ``text`` attribute MAY be an empty string.

    .. code-block:: python

        message.type = MsgType.Link
        message.text = "Check it out!"
        message.attributes = LinkAttribute(
            title="Example Domain",
            description="This domain is established to be used for illustrative examples in documents.",
            image="https://example.com/thumbnail.png",
            url="https://example.com"
        )

5. Status

    In status messages, the ``text`` attribute is disregarded.

    .. code-block:: python

        message.type = MsgType.Status
        message.attributes = StatusAttribute(StatusAttribute.TYPING)

6. Unsupported message

    ``text`` attribute is required for this type of message.

    .. code-block:: python

        message.type = MsgType.Unsupported
        message.text = "Alice requested USD 10.00 from you. "
                       "Please continue with your Bazinga App."

Additional information
~~~~~~~~~~~~~~~~~~~~~~

1. Substitution

    @-reference the User Themself, another member in the same chat, and the
    entire chat in the message text.

    .. code-block:: python

        message.text = "Hey @david, @bob, and @all. Attention!"
        message.substitutions = Substitutions({
            # text[4:10] == "@david", here David is the user.
            (4, 10): wonderland.self,
            # text[12:16] == "@bob", Bob is another member of the chat.
            (12, 16): wonderland.get_member("bob"),
            # text[22:26] == "@all", this calls the entire group chat, hence the
            # chat object is set as the following value instead.
            (22, 26): wonderland
        })

2. Commands

    .. code-block:: python

        message.text = "Carol sent you a friend request."
        message.commands = MessageCommands([
            EFBCommand(name="Accept", callable_name="accept_friend_request",
                       kwargs={"username": "carol_jhonos", "hash": "2a9329bd93f"}),
            EFBCommand(name="Decline", callable_name="decline_friend_request",
                       kwargs={"username": "carol_jhonos", "hash": "2a9329bd93f"})
        ])
