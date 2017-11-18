from abc import abstractmethod, ABC
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from . import EFBChannel, EFBMsg

__all__ = ["EFBStatus", "EFBChatUpdates", "EFBMemberUpdates", "EFBMessageRemoval"]


class EFBStatus(ABC):
    @abstractmethod
    def __init__(self):
        raise NotImplementedError()


class EFBChatUpdates(EFBStatus):
    """
    Inform the master channel on updates of slave chats.
        
    Attributes:
        channel: Slave channel that issues the update
        channel_id (str): ID of the issuing channel.
        new_chats: Unique ID of new chats
        removed_chats: Unique ID of removed chats
        modified_chats: Unique ID of modified chats
    """
    def __init__(self, channel: 'EFBChannel', new_chats: Optional[Tuple[str]]=tuple(),
                 removed_chats: Optional[Tuple[str]]=tuple(), modified_chats: Optional[Tuple[str]]=tuple()):
        """
        Args:
            channel (ehforwarderbot.EFBChannel): Slave channel that issues the update
            new_chats: Unique ID of new chats
            removed_chats: Unique ID of removed chats
            modified_chats: Unique ID of modified chats
        """
        self.channel: 'EFBChannel' = channel
        self.channel_id: str = channel.channel_id
        self.new_chats: Tuple[str] = new_chats
        self.removed_chats: Tuple[str] = removed_chats
        self.modified_chats: Tuple[str] = modified_chats


class EFBMemberUpdates(EFBStatus):
    """
    Inform the master channel on updates of members in a slave chat.

    Attributes:
        channel: Slave channel that issues the update
        channel_id (str): ID of the issuing channel.
        chat_id (str): Unique ID of the chat.
        new_members: Unique ID of new members
        removed_members: Unique ID of removed members
        modified_members: Unique ID of modified members
    """

    def __init__(self, channel: 'EFBChannel', chat_id: str,
                 new_members: Optional[Tuple[str]]=tuple(), removed_members: Optional[Tuple[str]]=tuple(),
                 modified_members: Optional[Tuple[str]]=tuple()):
        """
        Args:
            channel: Slave channel that issues the update
            chat_id (str): Unique ID of the chat.
            new_members: Unique ID of new members
            removed_members: Unique ID of removed members
            modified_members: Unique ID of modified members
        """
        self.channel: 'EFBChannel' = channel
        self.channel_id: str = channel.channel_id
        self.chat_id: str = chat_id
        self.new_members: Tuple[str] = new_members
        self.removed_members: Tuple[str] = removed_members
        self.modified_members: Tuple[str] = modified_members


class EFBMessageRemoval(EFBStatus):
    """
    Inform a channel to remove a certain message.

    This is usually known as "delete from everyone", "delete from recipient",
    "recall a message", or "revoke a message" as well, depends on the IM.

    Some channels may not support removal of messages, and raises a
    :obj:`EFBOperationNotSupported` exception.

    Attributes:
        source_channel: Channel issued the status
        destination_channel: Channel the status is issued to
        message: Message to remove.
            This may not be a complete :obj:`EFBMsg` object.
    """

    def __init__(self, source_channel: 'EFBChannel', destination_channel: 'EFBChannel', message: 'EFBMsg'):
        """
        Create a message removal status

        Try to provided as much as you can, if not, provide a minimum information
        in the channel:

        * Slave channel ID and chat ID (``message.chat.channel_id`` and ``message.chat.chat_uid``)
        * Message unique ID from the slave channel (``message.uid``)

        Args:
            source_channel: Channel issued the status
            destination_channel: Channel the status is issued to
            message: Message to remove.
        """
        self.source_channel: 'EFBChannel' = source_channel
        self.destination_channel: 'EFBChannel' = destination_channel
        self.message: 'EFBMsg' = message
