# coding=utf-8

from abc import abstractmethod, ABC
from typing import Iterable

from . import EFBChannel, EFBMsg, coordinator

__all__ = ["EFBStatus", "EFBChatUpdates", "EFBMemberUpdates", "EFBMessageRemoval"]


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


class EFBChatUpdates(EFBStatus):
    """EFBChatUpdates(channel: EFBChannel, new_chats: Optional[Iterable[str]]=tuple(), removed_chats: Optional[Iterable[str]]=tuple(), modified_chats: Optional[Iterable[str]]=tuple())

    Inform the master channel on updates of slave chats.

    Attributes:
        channel (:obj:`.EFBChannel`): Slave channel that issues the update
        new_chats (Optional[Iterable[str]]): Unique ID of new chats
        removed_chats (Optional[Iterable[str]]): Unique ID of removed chats
        modified_chats (Optional[Iterable[str]]): Unique ID of modified chats
    """
    def __init__(self, channel: 'EFBChannel', new_chats: Iterable[str]=tuple(),
                 removed_chats: Iterable[str]=tuple(), modified_chats: Iterable[str]=tuple()):
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

    def __init__(self, channel: 'EFBChannel', chat_id: str,
                 new_members: Iterable[str]=tuple(), removed_members: Iterable[str]=tuple(),
                 modified_members: Iterable[str]=tuple()):
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

    def __init__(self, source_channel: 'EFBChannel', destination_channel: 'EFBChannel', message: 'EFBMsg'):
        """__init__(source_channel: EFBChannel, destination_channel: EFBChannel, message: EFBMsg)

        Create a message removal status

        Try to provided as much as you can, if not, provide a minimum information
        in the channel:

        * Slave channel ID and chat ID (:attr:`message.chat.channel_id <.EFBChat.channel_id>`
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
        if not self.message.chat.channel_id or not self.message.chat.chat_uid or not self.message.uid:
            raise ValueError("Message does not contain the minimum information required")
