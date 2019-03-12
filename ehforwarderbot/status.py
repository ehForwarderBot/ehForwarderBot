# coding=utf-8

from abc import abstractmethod, ABC
from typing import Iterable, Dict, Iterable, TYPE_CHECKING, Any

from ehforwarderbot import ChannelType, ChatType
from . import EFBChannel, EFBMsg, coordinator

if TYPE_CHECKING:
    from . import EFBChat

__all__ = ["EFBStatus", "EFBChatUpdates", "EFBMemberUpdates", "EFBMessageRemoval",
           "EFBReactToMessage", "EFBMessageReactUpdate"]


class EFBStatus(ABC):
    """
    Abstract class of a status

    Attributes:
        destination_channel (:obj:`.EFBChannel`): The
            channel that this status is sent to, usually
            the master channel.
    """

    @abstractmethod
    def __init__(self):
        self.destination_channel: 'EFBChannel' = None
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
        try:
            dc = coordinator.get_module_by_id(state['destination_channel'])
            if isinstance(dc, EFBChannel):
                self.destination_channel = dc
        except NameError:
            pass


class EFBChatUpdates(EFBStatus):
    """EFBChatUpdates(channel: EFBChannel, new_chats: Optional[Iterable[str]]=tuple(), removed_chats: Optional[Iterable[str]]=tuple(), modified_chats: Optional[Iterable[str]]=tuple())

    Inform the master channel on updates of slave chats.

    Attributes:
        channel (:obj:`.EFBChannel`): Slave channel that issues the update
        new_chats (Optional[Iterable[str]]): Unique ID of new chats
        removed_chats (Optional[Iterable[str]]): Unique ID of removed chats
        modified_chats (Optional[Iterable[str]]): Unique ID of modified chats
    """

    # noinspection PyMissingConstructor
    def __init__(self, channel: 'EFBChannel', new_chats: Iterable[str] = tuple(),
                 removed_chats: Iterable[str] = tuple(), modified_chats: Iterable[str] = tuple()):
        """__init__(channel: EFBChannel, new_chats: Iterable[str]=tuple(), removed_chats: Iterable[str]=tuple(), modified_chats: Iterable[str]=tuple())

        Args:
            channel (:obj:`.EFBChannel`): Slave channel that issues the update
            new_chats (Optional[Iterable[str]]): Unique ID of new chats
            removed_chats (Optional[Iterable[str]]): Unique ID of removed chats
            modified_chats (Optional[Iterable[str]]): Unique ID of modified chats
        """
        self.channel: 'EFBChannel' = channel
        self.new_chats: Iterable[str] = new_chats
        self.removed_chats: Iterable[str] = removed_chats
        self.modified_chats: Iterable[str] = modified_chats
        self.destination_channel: 'EFBChannel' = coordinator.master

    def __str__(self):
        return "<EFBChatUpdates @ {s.channel.channel_name}; New: {s.new_chats}; " \
               "Removed: {s.removed_chats}; Modified: {s.modified_chats}>".format(s=self)

    def verify(self):
        if self.channel is None or not isinstance(self.channel, EFBChannel):
            raise ValueError("Channel is not valid.")

    def __getstate__(self):
        state = super(EFBChatUpdates, self).__getstate__()
        if state['channel'] is not None:
            state['channel'] = state['channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        super(EFBChatUpdates, self).__setstate__(state)
        try:
            c = coordinator.get_module_by_id(state['channel'])
            if isinstance(c, EFBChannel):
                self.channel = c
        except NameError:
            pass


class EFBMemberUpdates(EFBStatus):
    """EFBMemberUpdates(channel: EFBChannel, chat_id: str, new_members: Optional[Iterable[str]]=tuple(), removed_members: Optional[Iterable[str]]=tuple(), modified_members: Optional[Iterable[str]]=tuple())

    Inform the master channel on updates of members in a slave chat.

    Attributes:
        channel (:obj:`.EFBChannel`): Slave channel that issues the update
        chat_id (str): Unique ID of the chat.
        new_members (Optional[Iterable[str]]): Unique ID of new members
        removed_members (Optional[Iterable[str]]): Unique ID of removed members
        modified_members (Optional[Iterable[str]]): Unique ID of modified members
    """

    # noinspection PyMissingConstructor
    def __init__(self, channel: 'EFBChannel', chat_id: str,
                 new_members: Iterable[str] = tuple(), removed_members: Iterable[str] = tuple(),
                 modified_members: Iterable[str] = tuple()):
        """__init__(channel: EFBChannel, chat_id: str, new_members: Iterable[str]=tuple(), removed_members: Iterable[str]=tuple(), modified_members: Optional[Iterable[str]]=tuple())

        Args:
            channel (:obj:`.EFBChannel`): Slave channel that issues the update
            chat_id (str): Unique ID of the chat.
            new_members (Optional[Iterable[str]]): Unique ID of new members
            removed_members (Optional[Iterable[str]]): Unique ID of removed members
            modified_members (Optional[Iterable[str]]): Unique ID of modified members
        """
        self.channel: 'EFBChannel' = channel
        self.chat_id: str = chat_id
        self.new_members: Iterable[str] = new_members
        self.removed_members: Iterable[str] = removed_members
        self.modified_members: Iterable[str] = modified_members
        self.destination_channel: 'EFBChannel' = coordinator.master

    def __str__(self):
        return "<EFBMemberUpdates: {s.chat_id} @ {s.channel.channel_name}; New: {s.new_chats}; " \
               "Removed: {s.removed_chats}; Modified: {s.modified_chats}>".format(s=self)

    def verify(self):
        if self.channel is None or not isinstance(self.channel, EFBChannel):
            raise ValueError("Channel is not valid.")

    def __getstate__(self):
        state = super(EFBMemberUpdates, self).__getstate__()
        if state['channel'] is not None:
            state['channel'] = state['channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        super(EFBMemberUpdates, self).__setstate__(state)
        try:
            c = coordinator.get_module_by_id(state['channel'])
            if isinstance(c, EFBChannel):
                self.channel = c
        except NameError:
            pass


class EFBMessageRemoval(EFBStatus):
    """EFBMessageRemoval(source_channel: EFBChannel, destination_channel: EFBChannel, message: EFBMsg)

    Inform a channel to remove a certain message.

    This is usually known as "delete from everyone", "delete from recipient",
    "recall a message", or "revoke a message" as well, depends on the IM.

    Some channels may not support removal of messages, and raises a
    :obj:`.exceptions.EFBOperationNotSupported` exception.

    Attributes:
        source_channel (:obj:`.EFBChannel`): Channel issued the status
        destination_channel (:obj:`.EFBChannel`): Channel the status is issued to
        message (:obj:`.EFBMsg`): Message to remove.
            This may not be a complete :obj:`.EFBMsg` object.
    """

    # noinspection PyMissingConstructor
    def __init__(self, source_channel: 'EFBChannel', destination_channel: 'EFBChannel', message: 'EFBMsg'):
        """__init__(source_channel: EFBChannel, destination_channel: EFBChannel, message: EFBMsg)

        Create a message removal status

        Try to provided as much as you can, if not, provide a minimum information
        in the channel:

        * Slave channel ID and chat ID (:attr:`message.chat.module_id <.EFBChat.module_id>`
          and :attr:`message.chat.chat_uid <.EFBChat.chat_uid>`)
        * Message unique ID from the slave channel (:attr:`message.uid <.EFBMsg.uid>`)

        Args:
            source_channel (:obj:`.EFBChannel`): Channel issued the status
            destination_channel (:obj:`.EFBChannel`): Channel the status is issued to
            message (:obj:`.EFBMsg`): Message to remove.
        """
        self.source_channel: 'EFBChannel' = source_channel
        self.destination_channel: 'EFBChannel' = destination_channel
        self.message: 'EFBMsg' = message

    def __str__(self):
        return "<EFBMessageRemoval: {s.message}; {s.source_channel.channel_name} " \
               "-> {s.destination_channel.channel_name}>".format(s=self)

    def verify(self):
        if self.source_channel is None or not isinstance(self.source_channel, EFBChannel):
            raise ValueError("Source channel is not valid.")
        if self.destination_channel is None or not isinstance(self.destination_channel, EFBChannel):
            raise ValueError("Destination channel is not valid.")
        if self.message is None or not isinstance(self.message, EFBMsg):
            raise ValueError("Message channel is not valid.")
        if not self.message.chat.module_id or not self.message.chat.chat_uid or not self.message.uid:
            raise ValueError("Message does not contain the minimum information required")

    def __getstate__(self):
        state = super(EFBMessageRemoval, self).__getstate__()
        if state['source_channel'] is not None:
            state['source_channel'] = state['source_channel'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        super(EFBMessageRemoval, self).__setstate__(state)
        try:
            sc = coordinator.get_module_by_id(state['source_channel'])
            if isinstance(sc, EFBChannel):
                self.source_channel = sc
        except NameError:
            pass


class EFBReactToMessage(EFBStatus):
    """
    Created when user react to a message, issued from master channel.

    Args:
        chat (:obj:`EFBChat`): The chat where message
        msg_id (str): ID of the message to react to
        reaction (str): The reaction name to be sent, usually an emoji
        destination_channel (:obj:`.EFBChannel`):
            Channel the status is issued to, extracted from the chat object.
    """

    # noinspection PyMissingConstructor
    def __init__(self, chat: 'EFBChat', msg_id: str, reaction: str):
        """
        Args:
            chat (:obj:`EFBChat`): The chat where message
            msg_id (str): ID of the message to react to
            reaction (str): The reaction name to be sent, usually an emoji
        """
        self.chat: 'EFBChat' = chat
        self.msg_id: str = msg_id
        self.reaction: str = reaction
        dc = coordinator.get_module_by_id(self.chat.module_id)
        if isinstance(dc, EFBChannel):
            self.destination_channel = dc

    def verify(self):
        if not self.chat:
            raise ValueError("Chat is not valid.")
        if not self.destination_channel or not isinstance(self.destination_channel, EFBChannel):
            raise ValueError("Destination channel does not exist.")
        if self.destination_channel.channel_type != ChannelType.Slave:
            raise ValueError("Destination channel is not a slave channel.")


class EFBMessageReactUpdate(EFBStatus):
    """
    Update reacts of a message, issued from slave channel to master channel.

    Args:
        chat (:obj:`EFBChat`): The chat where message
        msg_id (str): ID of the message for the reacts
        reactions (Dict[str, Iterable[:obj:`EFBChat`]]):
            Indicate reactions to the message. Dictionary key represents the
            reaction name, usually an emoji. Value is a collection of users
            who reacted to the message with that certain emoji.
            All :obj:`EFBChat` objects in this dict must be of a user or a
            group member.
        destination_channel (:obj:`.EFBChannel`):
            Channel the status is issued to, which is always the master channel.
    """

    # noinspection PyMissingConstructor
    def __init__(self, chat: 'EFBChat', msg_id: str, reactions: Dict[str, Iterable['EFBChat']]):
        """
        Args:
            chat (:obj:`EFBChat`): The chat where message
            msg_id (str): ID of the message for the reacts
            reactions (Dict[str, Iterable[:obj:`EFBChat`]]):
                Indicate reactions to the message. Dictionary key represents the
                reaction name, usually an emoji. Value is a collection of users
                who reacted to the message with that certain emoji.
                All :obj:`EFBChat` objects in this dict must be of a user or a
                group member.
        """
        self.chat: 'EFBChat' = chat
        self.msg_id: str = msg_id
        self.reactions: Dict[str, Iterable[EFBChat]] = reactions
        self.destination_channel = coordinator.master

    def verify(self):
        if not self.chat:
            raise ValueError("Chat is not valid.")
        for reaction, users in self.reactions.items():
            for user in users:
                if user.chat_type == ChatType.Group:
                    raise ValueError("Chat {} from reaction {} is a group.".format(user, reaction))
