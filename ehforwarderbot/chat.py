# coding=utf-8

import copy
import warnings
from enum import Enum
from typing import List, Dict, Any, Optional

from .channel import EFBChannel
from .constants import ChatType
from .middleware import EFBMiddleware

__all__ = ['EFBChat', 'EFBChatNotificationState']


class EFBChatNotificationState(Enum):
    """
    Indicates the notifications settings of a chat in its slave channel
    or middleware. If an exact match is not available, choose the most similar one.
    """

    NONE = 0
    """No notification is sent to slave IM channel at all."""

    MENTIONS = 1
    """Notifications are sent only when the user is mentioned in the message,
    in the form of @-references or direct reply (message target).
    """

    ALL = -1
    """All messages in the chat triggers notifications."""


class EFBChat:
    """
    EFB Chat object. This is used to represent a chat or a group member.

    Attributes:
        module_id (str): Unique ID of the module.
        channel_emoji (Optional[str]): Emoji of the channel, if available.
        module_name (str): Name of the module.
        chat_name (str): Name of the chat.
        chat_alias (str): Alternative name of the chat, usually set by user.
        chat_type (:obj:`.ChatType`): Type of the chat.
        chat_uid (str): Unique ID of the chat. This should be unique within the channel.
        is_chat (bool): Indicate if this object represents a chat. Defaulted to ``True``.
            This should be set to ``False`` when used on a group member.
        notification (EFBChatNotificationState): Indicate the notification settings of the chat in
            its slave channel (or middleware), defaulted to ``ALL``.
        group (:obj:`.EFBChat` or None): The parent chat of the member. Only
            available to chat member objects. Defaulted to ``None``.
        members (list of :obj:`.EFBChat`): Provide a list of members
            in the group. Defaulted to an empty ``list``. You may want to extend this
            object and implement a ``@property`` method set for loading members on
            demand.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
    """

    SELF_ID = "__self__"
    SYSTEM_ID = "__system__"

    def __init__(self, channel: Optional[EFBChannel] = None,
                 middleware: Optional[EFBMiddleware] = None):
        """
        Args:
            channel (Optional[:obj:`.EFBChannel`]):
                Provide the channel object to fill :attr:`module_name`,
                :attr:`channel_emoji`, and :attr:`module_id` automatically.
            middleware (Optional[:obj:`.EFBMiddleware`]):
                Provide the middleware object to fill :attr:`module_name`,
                and :attr:`module_id` automatically.
        """
        self.module_name: str = ""
        self.channel_emoji: Optional[str] = None
        self.module_id: str = ""
        if isinstance(channel, EFBChannel):
            self.module_name: str = channel.channel_name
            self.channel_emoji: str = channel.channel_emoji
            self.module_id: str = channel.channel_id
        elif isinstance(middleware, EFBMiddleware):
            self.module_id: str = middleware.middleware_id
            self.module_name: str = middleware.middleware_name

        self.chat_name: str = ""
        self.chat_type: ChatType = ChatType.Unknown
        self.chat_alias: Optional[str] = None
        self.chat_uid: str = ""
        self.is_chat: bool = True
        self.notification: EFBChatNotificationState = EFBChatNotificationState.ALL
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
        self.chat_type = ChatType.System
        return self

    @property
    def display_name(self) -> str:
        """Shortcut property, equivalent to ``chat_alias or chat_name``"""
        return self.chat_alias or self.chat_name

    @property
    def long_name(self) -> str:
        """
        Shortcut property, if alias exists, this will provide the alias with name
        in parenthesis. Otherwise, this will return the name
        """
        if self.chat_alias:
            return "{0} ({1})".format(self.chat_alias, self.chat_name)
        else:
            return self.chat_name

    @property
    def is_self(self) -> bool:
        """If this chat represents the user"""
        return self.chat_uid == EFBChat.SELF_ID

    @property
    def is_system(self) -> bool:
        """If this chat is a system chat"""
        return self.chat_type == ChatType.System

    @property
    def channel_id(self) -> str:
        """Alias to module_id. (This property will be deprecated)"""
        warnings.warn("channel_id will be deprecated. Use module_id instead.", PendingDeprecationWarning)
        return self.module_id

    @channel_id.setter
    def channel_id(self, value):
        warnings.warn("channel_id will be deprecated. Use module_id instead.", PendingDeprecationWarning)
        self.module_id = value

    @property
    def channel_name(self) -> str:
        """Alias to module_name. (This property will be deprecated)"""
        warnings.warn("channel_name will be deprecated. Use module_name instead.", PendingDeprecationWarning)
        return self.module_name

    @channel_name.setter
    def channel_name(self, value):
        warnings.warn("channel_name will be deprecated. Use module_name instead.", PendingDeprecationWarning)
        self.module_name = value

    def copy(self) -> 'EFBChat':
        return copy.copy(self)

    def verify(self):
        """
        Verify the completeness of the data.

        Raises:
            ValueError: When this chat is invalid.
        """
        if any(not i for i in (self.chat_uid, self.module_id)):
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
        return self.module_id == other.module_id and self.chat_uid == other.chat_uid

    def __str__(self):
        return "<EFBChat: {c.chat_name} ({alias}{c.chat_uid}) @ {c.module_name}>" \
            .format(c=self, alias=self.chat_alias + ", " if self.chat_alias else "")
