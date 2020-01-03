# coding=utf-8

import copy
import warnings
from enum import Enum
from typing import Dict, Any, Optional, TypeVar, Sequence

from .channel import EFBChannel
from .constants import ChatType
from .middleware import EFBMiddleware
from .types import ModuleID, ChatID

__all__ = ['EFBChat', 'EFBChatNotificationState']

# Allow mypy to recognize subclass output for `return self` methods.
EFBChatSelf = TypeVar('EFBChatSelf', bound='EFBChat', covariant=True)


class EFBChatNotificationState(Enum):
    """
    Indicates the notifications settings of a chat in its slave channel
    or middleware. If an exact match is not available, choose the most similar one.
    """

    NONE = 0
    """No notification is sent to slave IM channel at all."""

    MENTIONS = 1
    """Notifications are sent only when the user is mentioned in the message,
    in the form of @-references or quote-reply (message target).
    """

    ALL = -1
    """All messages in the chat triggers notifications."""


class EFBChat:
    """
    EFB Chat object. This is used to represent a chat or a group member.

    Note:
        ``EFBChat`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.

    Attributes:
        module_id (str): Unique ID of the module.
        channel_emoji (str): Emoji of the channel, empty string if the chat
            is from a middleware.
        module_name (str): Name of the module.
        chat_name (str): Name of the chat.
        chat_alias (Optional[str]): Alternative name of the chat, usually set by user.
        chat_type (:obj:`.ChatType`): Type of the chat.
        chat_uid (str): Unique ID of the chat. This should be unique within the channel.
        description (str): A text description of the chat, usually known as “bio”,
            “description”, “purpose”, or “topic” of the chat.
        is_chat (bool): Indicate if this object represents a chat. Defaulted to ``True``.
            This should be set to ``False`` when used on a group member.
        has_self (bool): Indicate if this chat has yourself. Defaulted to ``True``.

            This should be set to ``False`` when the user is not a member of a group,
            or when you cannot send messages to this chat at the moment. It
            should also be ``False`` when this object represents a group member
            instead of a chat.
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

    SELF_ID = ChatID("__self__")
    SYSTEM_ID = ChatID("__system__")

    def __init__(self, channel: Optional[EFBChannel] = None,
                 middleware: Optional[EFBMiddleware] = None,
                 module_name: str = "",
                 channel_emoji: str = "",
                 module_id: ModuleID = ModuleID(""),
                 chat_name: str = "",
                 chat_alias: Optional[str] = None,
                 chat_type: ChatType = ChatType.Unknown,
                 chat_uid: ChatID = ChatID(""),
                 is_chat: bool = True,
                 notification: EFBChatNotificationState = EFBChatNotificationState.ALL,
                 members: 'Sequence[EFBChat]' = None,
                 group: 'Optional[EFBChat]' = None,
                 vendor_specific: Dict[str, Any] = None,
                 description: str = "",
                 has_self: bool = True):
        """
        Args:
            channel (Optional[:obj:`.EFBChannel`]):
                Provide the channel object to fill :attr:`module_name`,
                :attr:`channel_emoji`, and :attr:`module_id` automatically.
            middleware (Optional[:obj:`.EFBMiddleware`]):
                Provide the middleware object to fill :attr:`module_name`,
                and :attr:`module_id` automatically.
        """
        if isinstance(channel, EFBChannel):
            self.module_name = channel.channel_name
            self.channel_emoji = channel.channel_emoji
            self.module_id = channel.channel_id
        elif isinstance(middleware, EFBMiddleware):
            self.module_id = middleware.middleware_id
            self.module_name = middleware.middleware_name
            self.channel_emoji = ""
        else:
            self.module_name = module_name
            self.channel_emoji = channel_emoji
            self.module_id = module_id

        self.chat_name: str = chat_name
        self.chat_type: ChatType = chat_type
        self.chat_alias: Optional[str] = chat_alias
        self.chat_uid: ChatID = chat_uid
        self.is_chat: bool = is_chat
        self.notification: EFBChatNotificationState = notification
        self.members: Sequence[EFBChat] = members if members is not None else []
        self.group: Optional[EFBChat] = group
        self.vendor_specific: Dict[str, Any] = vendor_specific if vendor_specific is not None else dict()
        self.description: str = description
        self.has_self: bool = has_self

    def self(self: EFBChatSelf) -> EFBChatSelf:
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

    def system(self: EFBChatSelf) -> EFBChatSelf:
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
        return "<EFBChat: {c.long_name} ({c.chat_uid}) @ {c.module_name} (Notification: {c.notification.name})>" \
            .format(c=self)
