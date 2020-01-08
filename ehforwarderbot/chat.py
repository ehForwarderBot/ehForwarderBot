# coding=utf-8

import copy
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, TypeVar, List

from .channel import SlaveChannel
from .coordinator import translator
from .middleware import Middleware
from .types import ModuleID, ChatID

__all__ = ['BaseChat',
           'Chat', 'PrivateChat', 'SystemChat', 'GroupChat',
           'ChatMember', 'SelfChatMember', 'SystemChatMember',
           'ChatNotificationState']


class ChatNotificationState(Enum):
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


class BaseChat(ABC):
    """
    Base chat class, this is an abstract class sharing properties among all
    chats, and users.

    Note:
        ``BaseChat`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.

    Attributes:
        module_id (str): Unique ID of the module.
        channel_emoji (str): Emoji of the channel, empty string if the chat
            is from a middleware.
        module_name (str): Name of the module.
        name (str): Name of the chat.
        alias (Optional[str]): Alternative name of the chat, usually set by user.
        id (str): Unique ID of the chat. This should be unique within the channel.
        description (str):
            A text description of the chat, usually known as “bio”,
            “description”, “purpose”, or “topic” of the chat.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
    """

    # Allow mypy to recognize subclass output for `return self` methods.
    _BaseChatSelf = TypeVar('_BaseChatSelf', bound='BaseChat')

    def __init__(self, *, channel: Optional[SlaveChannel] = None,
                 middleware: Optional[Middleware] = None,
                 module_name: str = "",
                 channel_emoji: str = "",
                 module_id: ModuleID = ModuleID(""),
                 name: str = "",
                 alias: Optional[str] = None,
                 id: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None,
                 description: str = ""):
        """
        Args:
            channel (Optional[:obj:`.SlaveChannel`]):
                Provide the channel object to fill :attr:`module_name`,
                :attr:`channel_emoji`, and :attr:`module_id` automatically.
            middleware (Optional[:obj:`.Middleware`]):
                Provide the middleware object to fill :attr:`module_name`,
                and :attr:`module_id` automatically.
            module_id (str): Unique ID of the module.
            channel_emoji (str): Emoji of the channel, empty string if the chat
                is from a middleware.
            module_name (str): Name of the module.
            name (str): Name of the chat.
            alias (Optional[str]): Alternative name of the chat, usually set by user.
            id (str): Unique ID of the chat. This should be unique within the channel.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
        """
        if channel:
            if isinstance(channel, SlaveChannel):
                self.module_name = channel.channel_name
                self.channel_emoji = channel.channel_emoji
                self.module_id = channel.channel_id
            else:
                raise ValueError("channel value should be an SlaveChannel object")
        elif isinstance(middleware, Middleware):
            self.module_id = middleware.middleware_id
            self.module_name = middleware.middleware_name
            self.channel_emoji = ""
        else:
            self.module_name = module_name
            self.channel_emoji = channel_emoji
            self.module_id = module_id

        self.name: str = name
        self.alias: Optional[str] = alias
        self.id: ChatID = id
        self.vendor_specific: Dict[str, Any] = vendor_specific if vendor_specific is not None else dict()
        self.description: str = description

    @property
    def display_name(self) -> str:
        """Shortcut property, equivalent to ``alias or name``"""
        return self.alias or self.name

    @property
    def long_name(self) -> str:
        """
        Shortcut property, if alias exists, this will provide the alias with name
        in parenthesis. Otherwise, this will return the name
        """
        if self.alias:
            return "{0} ({1})".format(self.alias, self.name)
        else:
            return self.name

    def copy(self: _BaseChatSelf) -> _BaseChatSelf:
        """Return a shallow copy of the object."""
        return copy.copy(self)

    @abstractmethod
    def verify(self):
        """
        Verify the completeness of the data.

        Raises:
            AssertionError: When this chat is invalid.
        """
        assert self.module_id, "Module ID should not be empty"
        assert isinstance(self.module_id, str), f"Module ID should be a string, {self.module_id!r} found."
        assert isinstance(self.module_name, str), f"Module Name should be a string, {self.module_name!r} found."
        assert isinstance(self.channel_emoji, str), f"Channel emoji should be a string, {self.channel_emoji!r} found."
        assert self.id, "Entity ID should not be empty"
        assert isinstance(self.id, str), f"Entity id should be a string, {self.id!r} found."
        assert isinstance(self.name, str), f"Entity name should be a string, {self.name!r} found."
        assert isinstance(self.alias, (str, type(None))), f"Entity alias should be either a string or None, {self.name!r} found."
        assert isinstance(self.description, str), f"Entity description should be a string, {self.description!r} found."

    def __eq__(self, other):
        return self.module_id == other.module_id and self.id == other.id

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.long_name} ({self.id}) @ {self.module_name}>"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"module_id={self.module_id!r}, "
            f"channel_emoji={self.channel_emoji!r}, "
            f"name={self.name!r}, "
            f"alias={self.alias!r}, "
            f"id={self.id!r}, "
            f"vendor_specific={self.vendor_specific!r}, "
            f"description={self.description!r}"
            f")"
        )


class ChatMember(BaseChat):
    """Member of a chat.

    Note:
        ``ChatMember`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.

    Attributes:
        chat (:obj:`.Chat`): Chat associated with this member.
        name (str): Name of the chat.
        alias (Optional[str]): Alternative name of the chat, usually set by user.
        id (str): Unique ID of the chat. This should be unique within the channel.
        description (str):
            A text description of the chat, usually known as “bio”,
            “description”, “purpose”, or “topic” of the chat.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
    """

    def __init__(self, chat: 'Chat', *,
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = ""):
        """
        Args:
            chat (:class:`~.chat.Chat`): Chat associated with this member.
            name (str): Name of the chat member.
            alias (Optional[str]): Alias of the chat member, optional.
            id (str): Unique ID of the chat member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
        """
        super().__init__(module_name=chat.module_name, channel_emoji=chat.channel_emoji,
                         module_id=chat.module_id, name=name, alias=alias, id=id,
                         vendor_specific=vendor_specific, description=description)
        self.chat: 'Chat' = chat

    def verify(self):
        super().verify()
        assert isinstance(self.chat, Chat)

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.long_name} ({self.id}) @ {self.chat}>"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"chat={self.chat}, "
            f"name={self.name!r}, "
            f"alias={self.alias!r}, "
            f"id={self.id!r}, "
            f"vendor_specific={self.vendor_specific!r}, "
            f"description={self.description!r}"
            f")"
        )


class SelfChatMember(ChatMember):
    """The user themself as member of a chat.

    Note:
        ``SelfChatMember`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.
    """

    SELF_ID = ChatID("__self__")

    def __init__(self, chat: 'Chat', *,
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = ""):
        """
        Args:
            chat (:class:`~.chat.Chat`): Chat associated with this member.
            name (str): Name of the chat member.
            alias (Optional[str]): Alias of the chat member, optional.
            id (str): Unique ID of the chat member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
        """
        name = name or translator.gettext("You")
        id = id or self.SELF_ID
        super().__init__(chat, name=name, alias=alias, id=id,
                         vendor_specific=vendor_specific, description=description)


class SystemChatMember(ChatMember):
    """A system account/prompt as member of a chat.

    Use this chat to send messages that is not from any specific member.

    Note:
        ``SystemChatMember`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.
    """

    SYSTEM_ID = ChatID("__system__")

    def __init__(self, chat: 'Chat', *,
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = ""):
        """
        Args:
            chat (:class:`~.chat.Chat`): Chat associated with this member.
            name (str): Name of the chat member.
            alias (Optional[str]): Alias of the chat member, optional.
            id (str): Unique ID of the chat member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
        """
        name = name or translator.gettext("System")
        id = id or self.SYSTEM_ID
        super().__init__(chat, name=name, alias=alias, id=id,
                         vendor_specific=vendor_specific, description=description)


class Chat(BaseChat, ABC):
    """
    A chat object, indicates a user, a group, or a system chat.

    Note:
        ``Chat`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.

    Attributes:
        module_id (str): Unique ID of the module.
        channel_emoji (str): Emoji of the channel, empty string if the chat
            is from a middleware.
        module_name (str): Name of the module.
        name (str): Name of the chat.
        alias (Optional[str]): Alternative name of the chat, usually set by user.
        id (str): Unique ID of the chat. This should be unique within the channel.
        description (str):
            A text description of the chat, usually known as “bio”,
            “description”, “purpose”, or “topic” of the chat.
        notification (:class:`ChatNotificationState`): Indicate the notification settings of the chat in
            its slave channel (or middleware), defaulted to :const:`~.ChatNotificationState.ALL`.
        members (list of :obj:`.ChatMember`): Provide a list of members
            in the chat. Defaulted to an empty ``list``. You may want to extend this
            object and implement a ``@property`` method set for loading members on
            demand.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
        self (Optional[:obj:`SelfChatMember`): the user as a member of the chat (if available).
    """

    self: Optional[SelfChatMember]
    """The user as a member of the chat (if available)."""

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""),
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = "",
                 members: List[ChatMember] = None,
                 notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        """
        Args:
            module_id (str): Unique ID of the module.
            channel_emoji (str): Emoji of the channel, empty string if the chat
                is from a middleware.
            module_name (str): Name of the module.
            name (str): Name of the chat.
            alias (Optional[str]): Alternative name of the chat, usually set by user.
            id (str): Unique ID of the chat. This should be unique within the channel.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
            notification (ChatNotificationState): Indicate the notification settings of the chat in
                its slave channel (or middleware), defaulted to ``ALL``.
            members (list of :obj:`.ChatMember`): Provide a list of members of the chat.
                Defaulted to an empty :obj:`list`.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            with_self (bool): Initialize the chat with the user themself as a member.
        """
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id,
                         vendor_specific=vendor_specific, description=description)
        self.members: List[ChatMember] = members if members is not None else []
        if with_self:
            self.self = SelfChatMember(self)
            self.members.append(self.self)
        else:
            self.self = None
        self.notification: ChatNotificationState = notification

    @property
    def has_self(self) -> bool:
        """Indicate if this chat has yourself."""
        return any(isinstance(member, SelfChatMember) for member in self.members)

    def add_member(self, name: str, id: ChatID, alias: Optional[str] = None,
                   vendor_specific: Dict[str, Any] = None, description: str = "") -> ChatMember:
        """Add a member to the chat.

        Args:
            name (str): Name of the member.
            id (str): ID of the member.
            alias (Optional[str]): Alias of the member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
        """
        member = ChatMember(self, name=name, alias=alias, id=id,
                            vendor_specific=vendor_specific, description=description)
        self.members.append(member)
        return member

    def add_system_member(self, name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                          vendor_specific: Dict[str, Any] = None, description: str = "") -> SystemChatMember:
        """Add a system member to the chat.

        Args:
            name (str): Name of the member.
            id (str): ID of the member.
            alias (Optional[str]): Alias of the member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
        """
        member = SystemChatMember(self, name=name, alias=alias, id=id,
                                  vendor_specific=vendor_specific, description=description)
        self.members.append(member)
        return member

    def get_member(self, member_id: ChatID) -> ChatMember:
        """Find a member of chat by its ID.

        Args:
            member_id (str): ID of the chat member.

        Returns:
            the chat member.

        Raises:
              KeyError: when the ID provided is not found.
        """
        for i in self.members:
            if i.id == member_id:
                return i
        raise KeyError("")

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.long_name} ({self.id}) @ {self.channel_emoji}{self.module_name} ({self.module_id})>"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"module_id={self.module_id!r}, "
            f"channel_emoji={self.channel_emoji!r}, "
            f"name={self.name!r}, "
            f"alias={self.alias!r}, "
            f"id={self.id!r}, "
            f"vendor_specific={self.vendor_specific!r}, "
            f"members={self.members!r}, "
            f"notification={self.notification!r}, "
            f"description={self.description!r}"
            f")"
        )


class PrivateChat(Chat):
    """A private chat, where usually only the opponent and the user themself are
    in the chat. Chat bots shall also be categorized under this type.

    There should only be at most one non-system member of the chat apart from
    the user themself, otherwise it might lead to unintended behavior.

    This object is by default initialized with the opponent as its member.

    If the ``with_self`` argument is ``True`` (which is the default setting),
    the user themself would also be initialized as a member of the chat.

    Args:
        opponent: the opponent of the chat as a member
    """
    opponent: ChatMember

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, id: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)
        self.opponent = self.add_member(name=name, alias=alias, id=id, vendor_specific=vendor_specific,
                                        description=description)
        self.verify()

    def verify(self):
        super().verify()
        assert all(isinstance(member, ChatMember) for member in self.members), \
            f"Some members of this chat is not a valid one: {self.members!r}"


class SystemChat(Chat):
    """A system chat, where usually only the opponent (system chat member) and
    the user themself are in the chat. This object is used to represent system
    chat where the opponent of the chat is neither a user nor a chat bot of the
    remote IM.

    Middlewares are recommended to create chats with this type when they want
    to send messages in this type.

    This object is by default initialized with the system opponent as its member.

    If the ``with_self`` argument is ``True`` (which is the default setting),
    the user themself would also be initialized as a member of the chat.

    Args:
        opponent: the opponent of the chat as a member
    """

    opponent: SystemChatMember

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, id: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)
        self.opponent = self.add_system_member(name=name, alias=alias, id=id, vendor_specific=vendor_specific,
                                               description=description)
        self.verify()

    def verify(self):
        super().verify()
        assert all(isinstance(member, ChatMember) for member in self.members)


class GroupChat(Chat):
    """A group chat, where there are usually multiple members present.

    Members can be added with the :meth:`.add_member` method.

    If the ``with_self`` argument is ``True`` (which is the default setting),
    the user themself would also be initialized as a member of the chat.

    Examples:

        >>> group = GroupChat(channel=slave_channel, name="Wonderland", id="wonderland001")
        >>> group.add_member(name="Alice", id="alice")
        ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='Alice', alias=None, id='alice', vendor_specific={}, description='')
        >>> group.add_member(name="bob", alias="Bob James", id="bob")
        ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='bob', alias='Bob James', id='bob', vendor_specific={}, description='')
        >>> from pprint import pprint
        >>> pprint(group.members)
        [SelfChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='You', alias=None, id='__self__', vendor_specific={}, description=''),
         ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='Alice', alias=None, id='alice', vendor_specific={}, description=''),
         ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='bob', alias='Bob James', id='bob', vendor_specific={}, description='')]
    """

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, id: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)
        self.verify()

    def verify(self):
        super().verify()
        assert all(isinstance(member, ChatMember) for member in self.members)
