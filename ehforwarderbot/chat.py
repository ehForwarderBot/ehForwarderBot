# coding=utf-8

import copy
from typing import List, Dict, Any, Optional

from .channel import EFBChannel
from .constants import ChatType


__all__ = ['EFBChat']


class EFBChat:
    """
    EFB Chat object. This is used to represent a chat or a group member.

    Attributes:
        channel_id (str): Unique ID of the channel.
        channel_emoji (str): Emoji of the channel.
        channel_name (str): Name of the channel.
        chat_name (str): Name of the chat.
        chat_alias (str): Alternative name of the chat, usually set by user.
        chat_type (:obj:`.ChatType`): Type of the chat.
        chat_uid (str): Unique ID of the chat. This should be unique within the channel.
        is_chat (bool): Indicate if this object represents a chat. Defaulted to ``True``.
            This should be set to ``False`` when used on a group member.
        group (:obj:`.EFBChat` or None): The parent chat of the member. Only
            available to chat member objects. Defaulted to ``None``.
        members (list of :obj:`.EFBChat`): Provide a list of members
            in the group. Defaulted to an empty ``list``. You may want to extend this
            object and implement a ``@property`` method set for loading members on
            demand.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
        is_self (bool): Indicate if this chat represents the user.
        is_system (bool): Indicate if this chat represents a system chat/member.
    """

    SELF_ID = "__self__"
    SYSTEM_ID = "__system__"

    def __init__(self, channel: Optional[EFBChannel]=None):
        """
        Args:
            channel (Optional[:obj:`.EFBChannel`]):
                Provide the channel object to fill :attr:`channel_name`,
                :attr:`channel_emoji`, and :attr:`channel_id` automatically.
        """
        self.channel_name: str = None
        self.channel_emoji: str = None
        self.channel_id: str = None
        if isinstance(channel, EFBChannel):
            self.channel_name: str = channel.channel_name
            self.channel_emoji: str = channel.channel_emoji
            self.channel_id: str = channel.channel_id

        self.chat_name: str = None
        self.chat_type: ChatType = None
        self.chat_alias: str = None
        self.chat_uid: str = None
        self.is_chat: bool = True
        self.members: List[EFBChat] = []
        self.group: Optional[EFBChat] = None
        self.vendor_specific: Dict[str, Any] = dict()

    def self(self) -> 'EFBChat':
        """
        Set the chat as yourself.
        In this context, "yourself" means the user behind the master channel.
        Every channel should relate this to the corresponding target.

        Returns:
            EFBChat: This object.
        """
        self.chat_name = "You"
        self.chat_alias = None
        self.chat_uid = EFBChat.SELF_ID
        self.chat_type = ChatType.User
        return self

    def system(self) -> 'EFBChat':
        """
        Set the chat as a system chat.
        Only set for channel-level and group-level system chats.

        Returns:
            EFBChat: This object.
        """
        self.chat_name = "System"
        self.chat_alias = None
        self.chat_uid = EFBChat.SYSTEM_ID
        self.chat_type = ChatType.User
        return self

    @property
    def is_self(self) -> bool:
        """If this chat represents the user"""
        return self.chat_uid == EFBChat.SELF_ID

    @property
    def is_system(self) -> bool:
        """If this chat is a system chat"""
        return self.chat_uid == EFBChat.SYSTEM_ID

    def copy(self) -> 'EFBChat':
        return copy.copy(self)

    def verify(self):
        """
        Verify the completeness of the data.

        Raises:
            ValueError: When this chat is invalid.
        """
        if any(i is None for i in (self.chat_uid, self.channel_id)):
            raise ValueError("Chat data is incomplete.")
        if not isinstance(self.chat_type, ChatType):
            raise ValueError("Invalid chat type.")
        if self.chat_type == ChatType.Group:
            if any(not isinstance(i, EFBChat) or not i.chat_type == ChatType.User for i in self.members):
                raise ValueError("The group has an invalid member.")
        if self.group is not None and (not isinstance(self.group, EFBChat) or
                                       not self.group.chat_type == ChatType.Group):
            raise ValueError("The member is in an invalid group.")

    def __eq__(self, other):
        return self.channel_id == other.channel_id and self.chat_uid == other.chat_uid

    def __str__(self):
        return "<EFBChat: {c.chat_name} ({alias}{c.chat_uid}) @ {c.channel_name}>" \
            .format(c=self, alias=self.chat_alias + ", " if self.chat_alias else "")
