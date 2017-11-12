from abc import abstractmethod, ABC
from typing import Tuple, Optional

from . import EFBChannel

__all__ = ["EFBChatUpdates", "EFBMemberUpdates"]


class EFBStatus(ABC):
    @abstractmethod
    def __init__(self):
        raise Exception("Do not use EFBStatus directly.")


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
    def __init__(self, channel: EFBChannel, new_chats: Optional[Tuple[str]]=tuple(),
                 removed_chats: Optional[Tuple[str]]=tuple(), modified_chats: Optional[Tuple[str]]=tuple()):
        """
        Args:
            channel (ehforwarderbot.EFBChannel): Slave channel that issues the update
            new_chats: Unique ID of new chats
            removed_chats: Unique ID of removed chats
            modified_chats: Unique ID of modified chats
        """
        self.channel: EFBChannel = channel
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

    def __init__(self, channel: EFBChannel, chat_id: str,
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
        self.channel: EFBChannel = channel
        self.channel_id: str = channel.channel_id
        self.chat_id: str = chat_id
        self.new_members: Tuple[str] = new_members
        self.removed_members: Tuple[str] = removed_members
        self.modified_members: Tuple[str] = modified_members


class EFBMessageRemoval(EFBStatus):
    """
    Inform the master channel to remove a certain message.

    Attributes:
        channel: Slave channel issuing the status
        channel_id: ID of the channel
        chat_id (str): Unique ID of the chat where the message exists
        message_id (str): Unique ID of the message to remove,
            must be identical to the message ID used while sending the message.
    """

    def __init__(self, channel: EFBChannel, chat_id: str, message_id: str):
        self.channel: EFBChannel = channel
        self.channel_id: str = channel.channel_id
        self.chat_id: str = chat_id
        self.message_id: str = message_id
