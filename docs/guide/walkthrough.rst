Walk-through — How EFB works
============================

EH Forwarder Bot is an extensible framework that allows
user to control and manage accounts from different chat
platforms in a unified interface. It consists of 4 parts:
a Master Channel, some Slave Channels, some Middlewares
and a Coordinator.

.. image:: ../_static/EFB-docs-0.png
    :align: center
    :alt: EFB Project Structure

Master Channel
    The channel that directly interact with the user.
    There is guaranteed to have one and only one master
    channel in an EFB Session.

Slave Channel
    The channel that delivers messages to and from
    their relative platform. There should be at lease one
    slave channel in an EFB Session.

Coordinator
    Component of the framework that maintains the
    instances of channels, and delivers messages between
    channels.

Middleware
    Module that processes messages and statuses
    delivered between channels, and make modifications
    where needed.

Concepts to know
----------------

Module
    A common term that means both channels and
    middlewares.

Chat
    A place where conversations happen. Consists of User
    Chats (private messages), Group Chats, and System
    Chats.

User / User Chat
    A user of the IM platform that the user can possibly
    chat with, or a conversation with them. Messages from
    such conversation has one and only one unique author.
    *(Except messages that are from the user themself, or
    from the system.)*

    For platforms that support bot or something similar,
    they would also be considered as a "user", unless
    messages in such chat can be sent from any user other
    than the bot.

    For chats that the user receive messages, but cannot
    send message to, it should also be considered as a
    user chat, only to raise an exception when messages
    was trying to send to the chat.

Group chat
    A chat that involves more than one user. A group chat
    should have a list of members (users) that can involve
    in the conversation.

System chat
    A chat that is a part of the system. Usually used for
    chats that are either a part of the IM platform, or
    the channel. Slave channels can use this feature to
    send system message and notifications to the master
    channel.

Message
    Messages are delivered strictly between the master
    channel and a slave channel. It usually carries
    an information of a certain type.

    Each message should at least have a unique ID that is
    distinct within the slave channel related to it. Any
    edited message should be able to be identified with
    the same unique ID.

Status
    Information that is not formatted into a message. Usually
    includes updates of chats and members of chats, and
    removal of messages.

Slave Channels
--------------

The job of slave channels is relatively simple.

1. Deliver messages to and from the master channel.
2. Maintains a list of all available chats, and group members.
3. Monitors changes of chats and notify the master channel.

Features that does not fit into the standard EFB Slave Channel
model can be offered as :ref:`slave-additional-features`.

Master Channels
---------------

Master channels is relatively more complicated and also
more flexible. As it directly faces the user, its user
interface should be user-friendly, or at least friendly
to the targeted users.

The job of the master channel includes:

1. Receive, process and display messages from slave
   channels.
2. Display a full list of chats from all slave channels.
3. Offer an interface for the user to use "extra functions"
   from slave channels.
4. Process updates from slave channels.
5. Provide a user-friendly interface as far as possible.

Middlewares
-----------

Middlewares can monitor and make changes to or nullify
messages and statuses delivered between channels.
Middlewares are executed in order of registration, one
after another. A middleware will always receive the
messages processed by the preceding middleware if
available. Once a middleware nullify a message or status,
the message will not be processed and delivered any
further.