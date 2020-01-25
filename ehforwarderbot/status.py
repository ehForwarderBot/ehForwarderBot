# coding=utf-8

from abc import abstractmethod, ABC
from contextlib import suppress
from typing import Dict, Collection, Any, Optional

from . import Channel, Message, coordinator
from .channel import SlaveChannel
from .chat import Chat, ChatMember
from .types import Reactions, ReactionName, ChatID, MessageID

__all__ = ["Status", "ChatUpdates", "MemberUpdates", "MessageRemoval",
           "ReactToMessage", "MessageReactionsUpdate"]


class Status(ABC):
    """
    Abstract class of a status

    Attributes:
        destination_channel (:obj:`.Channel`): The
            channel that this status is sent to, usually
            the master channel.
    """

    @abstractmethod
    def __init__(self):
        self.destination_channel: 'Channel' = None
        raise NotImplementedError()

    @abstractmethod
    def verify(self):
        raise NotImplementedError()

    def __getstate__(self):
        state = self.__dict__.copy()
        if state['destination_channel'] is not None:
            state['destination_channel'] = state['destination_channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        self.__dict__.update(state)
        with suppress(NameError):
            dc = coordinator.get_module_by_id(state['destination_channel'])
            if isinstance(dc, Channel):
                self.destination_channel = dc


class ChatUpdates(Status):
    """Inform the master channel on updates of slave chats.

    Attributes:
        channel (:obj:`.SlaveChannel`): Slave channel that issues the update
        new_chats (Optional[Collection[str]]): Unique ID of new chats
        removed_chats (Optional[Collection[str]]): Unique ID of removed chats
        modified_chats (Optional[Collection[str]]): Unique ID of modified chats
    """

    # noinspection PyMissingConstructor
    def __init__(self, channel: 'SlaveChannel',
                 new_chats: Collection[ChatID] = tuple(),
                 removed_chats: Collection[ChatID] = tuple(),
                 modified_chats: Collection[ChatID] = tuple()):
        """
        Args:
            channel (:obj:`.SlaveChannel`): Slave channel that issues the update
            new_chats (Optional[Collection[str]]): Unique ID of new chats
            removed_chats (Optional[Collection[str]]): Unique ID of removed chats
            modified_chats (Optional[Collection[str]]): Unique ID of modified chats
        """
        self.channel: 'SlaveChannel' = channel
        self.new_chats: Collection[ChatID] = new_chats
        self.removed_chats: Collection[ChatID] = removed_chats
        self.modified_chats: Collection[ChatID] = modified_chats
        self.destination_channel = coordinator.master
        self.verify()

    def __str__(self):
        return "<ChatUpdates @ {s.channel.channel_name}; New: {s.new_chats}; " \
               "Removed: {s.removed_chats}; Modified: {s.modified_chats}>".format(s=self)

    def verify(self):
        assert isinstance(self.channel, SlaveChannel), f"Slave channel {self.channel!r} is not valid."

    def __getstate__(self):
        state = super(ChatUpdates, self).__getstate__()
        if state['channel'] is not None:
            state['channel'] = state['channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        super(ChatUpdates, self).__setstate__(state)
        with suppress(NameError):
            c = coordinator.get_module_by_id(state['channel'])
            if isinstance(c, SlaveChannel):
                self.channel = c


class MemberUpdates(Status):
    """Inform the master channel on updates of members in a slave chat.

    Attributes:
        channel (:obj:`.SlaveChannel`): Slave channel that issues the update
        chat_id (str): Unique ID of the chat.
        new_members (Optional[Collection[str]]): Unique ID of new members
        removed_members (Optional[Collection[str]]): Unique ID of removed members
        modified_members (Optional[Collection[str]]): Unique ID of modified members
    """

    # noinspection PyMissingConstructor
    def __init__(self, channel: 'SlaveChannel', chat_id: ChatID,
                 new_members: Collection[ChatID] = tuple(),
                 removed_members: Collection[ChatID] = tuple(),
                 modified_members: Collection[ChatID] = tuple()):
        """
        Args:
            channel (:obj:`.SlaveChannel`): Slave channel that issues the update
            chat_id (str): Unique ID of the chat.
            new_members (Optional[Collection[str]]): Unique ID of new members
            removed_members (Optional[Collection[str]]): Unique ID of removed members
            modified_members (Optional[Collection[str]]): Unique ID of modified members
        """
        self.channel: 'SlaveChannel' = channel
        self.chat_id: ChatID = chat_id
        self.new_members: Collection[ChatID] = new_members
        self.removed_members: Collection[ChatID] = removed_members
        self.modified_members: Collection[ChatID] = modified_members
        self.destination_channel = coordinator.master
        self.verify()

    def __str__(self):
        return "<MemberUpdates: {s.chat_id} @ {s.channel.channel_name}; New: {s.new_chats}; " \
               "Removed: {s.removed_chats}; Modified: {s.modified_chats}>".format(s=self)

    def verify(self):
        assert isinstance(self.channel, SlaveChannel), f"Slave channel {self.channel!r} is not valid."

    def __getstate__(self):
        state = super(MemberUpdates, self).__getstate__()
        if state['channel'] is not None:
            state['channel'] = state['channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        super(MemberUpdates, self).__setstate__(state)
        with suppress(NameError):
            c = coordinator.get_module_by_id(state['channel'])
            if isinstance(c, SlaveChannel):
                self.channel = c


class MessageRemoval(Status):
    """Inform a channel to remove a certain message.

    This is usually known as “delete from everyone”, “delete from recipient”,
    “recall a message”, “unsend”, or “revoke a message” as well, depends on
    the IM platform.

    Some channels MAY not support removal of messages, and raises a
    :obj:`.exceptions.EFBOperationNotSupported` exception.

    Feedback by sending another ``MessageRemoval`` back is not required
    when this object is sent from a master channel. Master channels SHOULD
    treat a successful delivery of this status as a successful removal.

    Attributes:
        source_channel (:obj:`.Channel`): Channel issued the status
        destination_channel (:obj:`.Channel`): Channel the status is issued to
        message (:obj:`~.message.Message`): Message to remove.
            This MAY not be a complete :obj:`.message.Message` object.

    Raises:
        :obj:`.exceptions.EFBOperationNotSupported`:
            When message removal is not supported in the channel.
    """

    # noinspection PyMissingConstructor
    def __init__(self, source_channel: 'Channel', destination_channel: 'Channel', message: 'Message'):
        """Create a message removal status

        Try to provided as much as you can, if not, provide a minimum information
        in the channel:

        * Slave channel ID and chat ID (:attr:`message.chat.module_id <.Chat.module_id>`
          and :attr:`message.chat.uid <.Chat.uid>`)
        * Message unique ID from the slave channel (:attr:`message.uid <.message.Message.uid>`)

        Args:
            source_channel (:obj:`~.channel.Channel`): Channel issued the status
            destination_channel (:obj:`~.channel.Channel`): Channel the status is issued to
            message (:obj:`~.message.Message`): Message to remove.
        """
        self.source_channel: 'Channel' = source_channel
        self.destination_channel: 'Channel' = destination_channel
        self.message: 'Message' = message
        self.verify()

    def __str__(self):
        return "<MessageRemoval: {s.message}; {s.source_channel.channel_name} " \
               "-> {s.destination_channel.channel_name}>".format(s=self)

    def verify(self):
        assert isinstance(self.source_channel, Channel), \
            f"Source channel {self.source_channel!r} is not valid."
        assert isinstance(self.destination_channel, Channel), \
            f"Destination channel {self.destination_channel!r} is not valid."
        assert isinstance(self.message, Message), \
            f"Message {self.message!r} is not valid."
        assert self.message.chat.module_id and self.message.chat.uid and self.message.uid, \
            f"Message does not contain the minimum information required: {self.message!r}"

    def __getstate__(self):
        state = super(MessageRemoval, self).__getstate__()
        if state['source_channel'] is not None:
            state['source_channel'] = state['source_channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        super(MessageRemoval, self).__setstate__(state)
        with suppress(NameError):
            sc = coordinator.get_module_by_id(state['source_channel'])
            if isinstance(sc, Channel):
                self.source_channel = sc


class ReactToMessage(Status):
    """
    Created when user react to a message, issued from master channel.

    When this status is sent, a :obj:`.status.MessageReactionsUpdate` is
    RECOMMENDED to be issued back to master channel.

    Args:
        chat (:obj:`Chat`): The chat where message is sent
        msg_id (str): ID of the message to react to
        reaction (Optional[str]): The reaction name to be sent, usually an emoji.
            Set to ``None`` to remove reaction.
        destination_channel (:obj:`.SlaveChannel`):
            Channel the status is issued to, extracted from the chat object.

    Raises:
        :obj:`.exceptions.EFBMessageReactionNotPossible`:
            Raised when the reaction is not valid (e.g. the specific reaction is not
            in the list of possible reactions).
        :obj:`.exceptions.EFBOperationNotSupported`:
            Raised when reaction in any form is not supported to the message at all.
    """

    # noinspection PyMissingConstructor
    def __init__(self, chat: 'Chat', msg_id: str, reaction: Optional[ReactionName]):
        """
        Args:
            chat (:obj:`.Chat`): The chat where message is sent
            msg_id (str): ID of the message to react to
            reaction: The reaction name to be sent, usually an emoji
        """
        self.chat: 'Chat' = chat
        self.msg_id: str = msg_id
        self.reaction: Optional[str] = reaction
        if getattr(self.chat, 'module_id', None):
            self.destination_channel = coordinator.slaves[self.chat.module_id]
        self.verify()

    def verify(self):
        assert isinstance(self.chat, Chat), f"Chat {self.chat!r} is not valid."
        assert self.msg_id, f"Message ID {self.msg_id!r} is not valid."
        assert isinstance(self.destination_channel, SlaveChannel), \
            f"Destination channel is not a slave channel, but {self.destination_channel}."


class MessageReactionsUpdate(Status):
    """
    Update reacts of a message, issued from slave channel to master channel.

    Args:
        chat (:obj:`.Chat`): The chat where message is sent
        msg_id (str): ID of the message for the reacts
        reactions:
            Indicate reactions to the message. Dictionary key represents the
            reaction name, usually an emoji. Value is a collection of users
            who reacted to the message with that certain emoji.
            All :obj:`Chat` objects in this dict MUST be members in the chat
            of the message.
        destination_channel (:obj:`.MasterChannel`):
            Channel the status is issued to, which is always the master channel.
    """

    # noinspection PyMissingConstructor
    def __init__(self, chat: 'Chat', msg_id: MessageID, reactions: Reactions):
        """
        Args:
            chat (:obj:`.Chat`): The chat where message is sent
            msg_id (str): ID of the message for the reacts
            reactions:
                Indicate reactions to the message. Dictionary key represents the
                reaction name, usually an emoji. Value is a collection of users
                who reacted to the message with that certain emoji.
                All :obj:`Chat` objects in this dict MUST be members in the chat
                of the message.
        """
        self.chat: 'Chat' = chat
        self.msg_id: MessageID = msg_id
        self.reactions: Reactions = reactions
        self.destination_channel = coordinator.master
        self.verify()

    def verify(self):
        assert isinstance(self.chat, Chat), f"Chat {self.chat!r} is not valid."

        assert self.msg_id, f"Message ID {self.msg_id} is not valid."
        for reaction, users in self.reactions.items():
            for user in users:
                assert isinstance(user, ChatMember), f"Expected reactor of {reaction} to be a ChatMember, but {user!r} found."
