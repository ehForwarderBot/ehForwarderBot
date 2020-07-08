# coding=utf-8

import copy
import warnings
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, Optional, TypeVar, MutableSequence

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
    """Notifications are sent only when the User is mentioned in the message,
    in the form of @-references or quote-reply (message target).
    """

    ALL = -1
    """All messages in the chat triggers notifications."""


class BaseChat(ABC):
    """
    Base chat class, this is an abstract class sharing properties among all
    chats and members. No instance can be created directly from this class.

    Note:
        ``BaseChat`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.

    Attributes:
        module_id (:obj:`.ModuleID` (str)): Unique ID of the module.
        channel_emoji (str): Emoji of the channel, empty string if the chat
            is from a middleware.
        module_name (:obj:`.ModuleID` (str)): Name of the module.
        name (str): Name of the chat.
        alias (Optional[str]): Alternative name of the chat, usually set by user.
        uid (:obj:`.ChatID` (str)): Unique ID of the chat. This MUST be unique within the channel.
        description (str):
            A text description of the chat, usually known as “bio”,
            “description”, “purpose”, or “topic” of the chat.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
    """

    # Allow mypy to recognize subclass output for `return self` methods.
    _BaseChatSelf = TypeVar('_BaseChatSelf', bound='BaseChat', covariant=True)

    def __init__(self, *, channel: Optional[SlaveChannel] = None,
                 middleware: Optional[Middleware] = None,
                 module_name: str = "",
                 channel_emoji: str = "",
                 module_id: ModuleID = ModuleID(""),
                 name: str = "",
                 alias: Optional[str] = None,
                 uid: ChatID = ChatID(""),
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
            module_id: Unique ID of the module.
            channel_emoji (str): Emoji of the channel, empty string if the chat
                is from a middleware.
            module_name (str): Name of the module.
            name (str): Name of the chat.
            alias (Optional[str]): Alternative name of the chat, usually set by user.
            uid: Unique ID of the chat. This MUST be unique within the channel.
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
                raise ValueError(
                    "channel value should be an SlaveChannel object")
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
        if id:
            warnings.warn("`id` argument is deprecated, use `uid` instead.", DeprecationWarning)
            self.uid: ChatID = id
        else:
            self.uid = uid
        self.vendor_specific: Dict[str,
                                   Any] = vendor_specific if vendor_specific is not None else dict()
        self.description: str = description

    @property
    def id(self) -> ChatID:
        warnings.warn("`id` property of a chat/member is deprecated, use `uid` instead.", DeprecationWarning)
        return self.uid

    @id.setter
    def id(self, val: ChatID):
        warnings.warn("`id` property of a chat/member is deprecated, use `uid` instead.", DeprecationWarning)
        self.uid = val

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
        assert isinstance(self.module_id, str), \
            f"Module ID should be a string, {self.module_id!r} found."
        assert isinstance(self.module_name, str), \
            f"Module Name should be a string, {self.module_name!r} found."
        assert isinstance(self.channel_emoji, str), \
            f"Channel emoji should be a string, {self.channel_emoji!r} found."
        assert self.uid, "Entity ID should not be empty"
        assert isinstance(self.uid, str), \
            f"Entity id should be a string, {self.uid!r} found."
        assert isinstance(self.name, str), \
            f"Entity name should be a string, {self.name!r} found."
        assert isinstance(self.alias, (str, type(None))), \
            f"Entity alias should be either a string or None, {self.name!r} found."
        assert isinstance(self.description, str), \
            f"Entity description should be a string, {self.description!r} found."

    def __eq__(self, other):
        return self.module_id == other.module_id and self.uid == other.uid

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.long_name} ({self.uid}) @ {self.module_name}>"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"module_id={self.module_id!r}, "
            f"channel_emoji={self.channel_emoji!r}, "
            f"name={self.name!r}, "
            f"alias={self.alias!r}, "
            f"uid={self.uid!r}, "
            f"vendor_specific={self.vendor_specific!r}, "
            f"description={self.description!r}"
            f")"
        )


class ChatMember(BaseChat):
    """Member of a chat. Usually indicates a member in a group, or the other
    participant in a private chat. Chat bots created by the users of the
    IM platform is also considered as a plain :class:`.ChatMember`.

    To represent the User Themself, use :class:`.SelfChatMember`.

    To represent a chat member that is a part of the system, the slave channel,
    or a middleware, use :class:`.SystemChatMember`.

    :class:`.ChatMember`\\ s MUST be created with reference of the chat it
    belongs to. Different objects MUST be created even when the same person
    appears in different groups or in a private chat.

    :class:`.ChatMember`\\ s are RECOMMENDED to be created using
    :meth:`.Chat.add_member` method.

    Note:
        ``ChatMember`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.
    """
    def __init__(self, chat: 'Chat', *,
                 name: str = "", alias: Optional[str] = None, uid: ChatID = ChatID(""),
                 id: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = "",
                 middleware: Optional[Middleware] = None):
        """
        Args:
            chat (:class:`~.chat.Chat`): Chat associated with this member.

        Keyword Args:
            name (str): Name of the member.
            alias (Optional[str]): Alternative name of the member, usually set by user.
            uid (:obj:`.ChatID` (str)):
                Unique ID of the member. This MUST be unique within the channel.
                This ID can be the same with a private chat of the same person.
            description (str):
                A text description of the member, usually known as “bio”,
                “description”, “summary” or “introduction” of the member.
            middleware (:class:`.Middleware`): Initialize this chat as a part
                of a middleware.
        """
        if middleware:
            super().__init__(module_name=middleware.middleware_name, channel_emoji="",
                             module_id=middleware.middleware_id, name=name, alias=alias, id=id, uid=uid,
                             vendor_specific=vendor_specific, description=description)
        else:
            super().__init__(module_name=chat.module_name, channel_emoji=chat.channel_emoji,
                             module_id=chat.module_id, name=name, alias=alias, id=id, uid=uid,
                             vendor_specific=vendor_specific, description=description)
        self.chat: 'Chat' = chat

    def verify(self):
        super().verify()
        assert isinstance(self.chat, Chat)

    def __eq__(self, other):
        return (
                isinstance(other, ChatMember) and
                other.uid == self.uid and
                other.chat == self.chat
        )

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.long_name} ({self.uid}) @ {self.chat}>"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"chat={self.chat}, "
            f"name={self.name!r}, "
            f"alias={self.alias!r}, "
            f"uid={self.uid!r}, "
            f"vendor_specific={self.vendor_specific!r}, "
            f"description={self.description!r}"
            f")"
        )


class SelfChatMember(ChatMember):
    """The User Themself as member of a chat.

    :class:`.SelfChatMember`\\ s are RECOMMENDED to be created together with a
    chat object by setting ``with_self`` value to ``True``. The created object
    is accessible at :attr:`.Chat.self`.

    The default ID of a :class:`.SelfChatMember` object is
    :attr:`.SelfChatMember.SELF_ID`, and the default name is a translated
    version of the word “You”.

    You are RECOMMENDED to change the ID of this object if provided by your IM
    platform, and you MAY change the name or alias of this object depending on
    your needs.

    Note:
        ``SelfChatMember`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.

    Attributes:
        SELF_ID: The default ID of a :class:`.SelfChatMember`.
    """

    SELF_ID = ChatID("__self__")

    def __init__(self, chat: 'Chat', *,
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 uid: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = "",
                 middleware: Optional[Middleware] = None):
        """
        Args:
            chat (:class:`~.chat.Chat`): Chat associated with this member.

        Keyword Args:
            name (str): Name of the member.
            alias (Optional[str]): Alternative name of the member, usually set by user.
            uid (:obj:`.ChatID` (str)):
                Unique ID of the member. This MUST be unique within the channel.
                This ID can be the same with a private chat of the same person.
            description (str):
                A text description of the member, usually known as “bio”,
                “description”, “summary” or “introduction” of the member.
            middleware (:class:`.Middleware`): Initialize this chat as a part
                of a middleware.
        """
        name = name or translator.gettext("You")
        uid = uid or id or self.SELF_ID
        super().__init__(chat, name=name, alias=alias, id=id, uid=uid,
                         vendor_specific=vendor_specific, description=description,
                         middleware=middleware)


class SystemChatMember(ChatMember):
    """A system account/prompt as member of a chat.

    Use this chat to send messages that is not from any specific member.
    Middlewares are RECOMMENDED to use this member type to communicate with
    the User in an existing chat.

    Chat bots created by the users of the IM platform SHOULD NOT be created
    as a :class:`.SystemChatMember`, but a plain :class:`.ChatMember` instead.

    :class:`.SystemChatMember`\\ s are RECOMMENDED to be created using
    :meth:`.Chat.add_system_member` or :meth:`.Chat.make_system_member` method.

    Note:
        ``SystemChatMember`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.

    Attributes:
        SYSTEM_ID: The default ID of a :class:`.SystemChatMember`.
    """

    SYSTEM_ID = ChatID("__system__")

    def __init__(self, chat: 'Chat', *,
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 uid: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = "",
                 middleware: Optional[Middleware] = None):
        """
        Args:
            chat (:class:`~.chat.Chat`): Chat associated with this member.

        Keyword Args:
            name (str): Name of the member.
            alias (Optional[str]): Alternative name of the member, usually set by user.
            uid (:obj:`.ChatID` (str)):
                Unique ID of the member. This MUST be unique within the channel.
                This ID can be the same with a private chat of the same person.
            description (str):
                A text description of the member, usually known as “bio”,
                “description”, “summary” or “introduction” of the member.
            middleware (:class:`.Middleware`): Initialize this chat as a part
                of a middleware.
        """
        name = name or translator.gettext("System")
        uid = uid or id or self.SYSTEM_ID
        super().__init__(chat, name=name, alias=alias, id=id, uid=uid,
                         vendor_specific=vendor_specific, description=description,
                         middleware=middleware)


class Chat(BaseChat, ABC):  # lgtm [py/missing-equals]
    """
    A chat object, indicates a user, a group, or a system chat. This class is
    abstract. No instance can be created directly from this class.

    If your IM platform is providing an ID of the User Themself, and it is using
    this ID to indicate the author of a message, you SHOULD update
    :attr:`Chat.self.uid <.BaseChat.uid>` accordingly.

    .. code-block:: python

        >>> channel.my_chat_id
        "david_divad"
        >>> chat = Chat(channel=channel, name="Alice", uid=ChatID("alice123"))
        >>> chat.self.uid = channel.my_chat_id

    By doing so, you can get the author in one step:

    .. code-block:: python

        author = chat.get_member(author_id)

    ... instead of using a condition check:

    .. code-block:: python

        if author_id == channel.my_chat_id:
            author = chat.self
        else:
            author = chat.get_member(author_id)

    Note:
        ``Chat`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.

    Attributes:
        module_id (:obj:`.ModuleID` (str)): Unique ID of the module.
        channel_emoji (str): Emoji of the channel, empty string if the chat
            is from a middleware.
        module_name (str): Name of the module.
        name (str): Name of the chat.
        alias (Optional[str]): Alternative name of the chat, usually set by user.
        uid (:obj:`~.ChatID` (str)): Unique ID of the chat. This MUST be unique within the channel.
        description (str):
            A text description of the chat, usually known as “bio”,
            “description”, “purpose”, or “topic” of the chat.
        notification (:class:`ChatNotificationState`): Indicate the notification settings of the chat in
            its slave channel (or middleware), defaulted to :const:`~.ChatNotificationState.ALL`.
        members (list of :obj:`.ChatMember`): Provide a list of members
            in the chat. Defaulted to an empty ``list``.

            You can extend this object and implement a ``@property`` method
            set for loading members on demand.

            Note that this list may include members created by middlewares when the object is
            a part of a message, and these members MAY not appear when trying to retrieve
            from the slave channel directly. These members would have a different
            :attr:`~.BaseChat.module_id` specified from the chat.
        vendor_specific (Dict[str, Any]): Any vendor specific attributes.
        self (Optional[:obj:`SelfChatMember`]): the User as a member of the chat (if available).
    """

    self: Optional[SelfChatMember]
    """The user as a member of the chat (if available)."""

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""),
                 name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                 uid: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None, description: str = "",
                 members: MutableSequence[ChatMember] = None,
                 notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        """
        Keyword Args:
            module_id (str): Unique ID of the module.
            channel_emoji (str): Emoji of the channel, empty string if the chat
                is from a middleware.
            module_name: Name of the module.
            name (str): Name of the chat.
            alias (Optional[str]): Alternative name of the chat, usually set by user.
            id: Unique ID of the chat. This MUST be unique within the channel.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
            notification (ChatNotificationState): Indicate the notification settings of the chat in
                its slave channel (or middleware), defaulted to ``ALL``.
            members (MutableSequence[:obj:`.ChatMember`]): Provide a list of members of the chat.
                Defaulted to an empty :obj:`list`.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            with_self (bool): Initialize the chat with the User Themself as a member.
        """
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, uid=uid,
                         vendor_specific=vendor_specific, description=description)
        self.members: MutableSequence[ChatMember] = members if members is not None else []
        if with_self:
            self.self = self.add_self()
        else:
            self.self = None
        self.notification: ChatNotificationState = notification

    @property
    def has_self(self) -> bool:
        """Indicate if this chat has yourself."""
        return any(isinstance(member, SelfChatMember) for member in self.members)

    def add_self(self) -> SelfChatMember:
        """Add self to the list of members.

        Raises:
            AssertionError: When there is already a self in the list of members.
        """
        if getattr(self, 'self', None) and isinstance(self.self, SelfChatMember):
            return self.self
        assert not any(isinstance(i, SelfChatMember) for i in self.members)
        s = SelfChatMember(self)
        self.members.append(s)
        return s

    def add_member(self, name: str, uid: ChatID, alias: Optional[str] = None,
                   id: ChatID = ChatID(""),
                   vendor_specific: Dict[str, Any] = None, description: str = "",
                   middleware: Optional[Middleware] = None) -> ChatMember:
        """Add a member to the chat.

        Tip:
            This method does not check for duplicates. Only add members with this
            method if you are sure that they are not added yet. To check if
            the member is already added before adding, you can do something like
            this:

            .. code-block:: python

                with contextlib.suppress(KeyError):
                    return chat.get_member(uid)
                return chat.add_member(name, uid, alias=..., vendor_specific=...)

        Args:
            name (str): Name of the member.
            uid: ID of the member.

        Keyword Args:
            alias (Optional[str]): Alias of the member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
            middleware (Optional[:class:`.Middleware`]): Initialize this chat as a part
                of a middleware.
        """
        if id:
            warnings.warn("`id` argument is deprecated, use `uid` instead.", DeprecationWarning)
            uid = uid or id
        member = ChatMember(self, name=name, alias=alias, uid=uid,
                            vendor_specific=vendor_specific, description=description,
                            middleware=middleware)
        self.members.append(member)
        return member

    def make_system_member(self, name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                           uid: ChatID = ChatID(""),
                           vendor_specific: Dict[str, Any] = None, description: str = "",
                           middleware: Optional[Middleware] = None) -> SystemChatMember:
        """Make a system member for this chat.

        Useful for slave channels and middlewares to create an author of a message from
        a system member when the “system” member is NOT intended to become a member of
        the chat.

        Keyword Args:
            name (str): Name of the member.
            uid: ID of the member.
            alias (Optional[str]): Alias of the member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
            middleware (Optional[:class:`.Middleware`]): Initialize this chat as a part
                of a middleware.
        """
        return SystemChatMember(self, name=name, alias=alias, id=id, uid=uid,
                                vendor_specific=vendor_specific, description=description,
                                middleware=middleware)

    def add_system_member(self, name: str = "", alias: Optional[str] = None, id: ChatID = ChatID(""),
                          uid: ChatID = ChatID(""),
                          vendor_specific: Dict[str, Any] = None, description: str = "",
                          middleware: Optional[Middleware] = None) -> SystemChatMember:
        """Add a system member to the chat.

        Useful for slave channels and middlewares to create an author of a message from
        a system member when the “system” member is intended to become a member of
        the chat.

        Tip:
            This method does not check for duplicates. Only add members with this
            method if you are sure that they are not added yet.

        Keyword Args:
            name (str): Name of the member.
            uid: ID of the member.
            alias (Optional[str]): Alias of the member.
            vendor_specific (Dict[str, Any]): Any vendor specific attributes.
            description (str):
                A text description of the chat, usually known as “bio”,
                “description”, “purpose”, or “topic” of the chat.
            middleware (Optional[:class:`.Middleware`]): Initialize this chat as a part
                of a middleware.
        """
        member = self.make_system_member(name=name, alias=alias, id=id, uid=uid,
                                         vendor_specific=vendor_specific, description=description,
                                         middleware=middleware)
        self.members.append(member)
        return member

    def get_member(self, member_id: ChatID) -> ChatMember:
        """Find a member of chat by its ID.

        Args:
            member_id: ID of the chat member.

        Returns:
            the chat member.

        Raises:
            KeyError: when the ID provided is not found.
        """
        for i in self.members:
            if i.uid == member_id:
                return i
        raise KeyError

    def __str__(self):
        return f"<{self.__class__.__name__}: {self.long_name} ({self.uid}) @ {self.channel_emoji}{self.module_name} ({self.module_id})>"

    def __repr__(self):
        return (
            f"{self.__class__.__name__}("
            f"module_name={self.module_name!r}, "
            f"module_id={self.module_id!r}, "
            f"channel_emoji={self.channel_emoji!r}, "
            f"name={self.name!r}, "
            f"alias={self.alias!r}, "
            f"uid={self.uid!r}, "
            f"vendor_specific={self.vendor_specific!r}, "
            f"members={self.members!r}, "
            f"notification={self.notification!r}, "
            f"description={self.description!r}"
            f")"
        )


class PrivateChat(Chat):
    """A private chat, where usually only the User Themself and the other
    participant are in the chat. Chat bots SHOULD also be categorized under this
    type.

    There SHOULD only be at most one non-system member of the chat apart from
    the User Themself, otherwise it might lead to unintended behavior.

    This object is by default initialized with the other participant as its
    member.

    If the ``with_self`` argument is ``True`` (which is the default setting),
    the User Themself would also be initialized as a member of the chat.

    Args:
        other: the other participant of the chat as a member

    Note:
        ``PrivateChat`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.
    """
    other: ChatMember

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, id: ChatID = ChatID(""), uid: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True, other_is_self: bool = False):
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, uid=uid, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)
        if other_is_self and with_self:
            assert self.self is not None
            self.other = self.self
        else:
            self.other = self.add_member(name=name, alias=alias, uid=uid, vendor_specific=vendor_specific,
                                         description=description)
        self.verify()

    def verify(self):
        super().verify()
        assert all(isinstance(member, ChatMember) for member in self.members), \
            f"Some members of this chat is not a valid one: {self.members!r}"


class SystemChat(Chat):
    """A system chat, where usually only the User Themself and the other
    participant (system chat member) are in the chat. This object is used to
    represent system chat where the other participant is neither a user nor a
    chat bot of the remote IM.

    Middlewares are RECOMMENDED to create chats with this type when they want
    to send messages in this type.

    This object is by default initialized with the system participant as its
    member.

    If the ``with_self`` argument is ``True`` (which is the default setting),
    the User Themself would also be initialized as a member of the chat.

    Args:
        other: the other participant of the chat as a member

    Note:
        ``SystemChat`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.
    """

    other: SystemChatMember

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, id: ChatID = ChatID(""), uid: ChatID = ChatID(""),
                 vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, uid=uid, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)
        self.other = self.add_system_member(name=name, alias=alias, id=id, uid=uid, vendor_specific=vendor_specific,
                                            description=description)
        self.verify()

    def verify(self):
        super().verify()
        assert all(isinstance(member, ChatMember) for member in self.members)


class GroupChat(Chat):
    """A group chat, where there are usually multiple members present.

    Members can be added with the :meth:`.add_member` method.

    If the ``with_self`` argument is ``True`` (which is the default setting),
    the User Themself would also be initialized as a member of the chat.

    Examples:

        >>> group = GroupChat(channel=slave_channel, name="Wonderland", uid=ChatID("wonderland001"))
        >>> group.add_member(name="Alice", uid=ChatID("alice"))
        ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='Alice', alias=None, uid='alice', vendor_specific={}, description='')
        >>> group.add_member(name="bob", alias="Bob James", uid=ChatID("bob"))
        ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='bob', alias='Bob James', uid='bob', vendor_specific={}, description='')
        >>> from pprint import pprint
        >>> pprint(group.members)
        [SelfChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='You', alias=None, uid='__self__', vendor_specific={}, description=''),
         ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='Alice', alias=None, uid='alice', vendor_specific={}, description=''),
         ChatMember(chat=<GroupChat: Wonderland (wonderland001) @ Example slave channel>, name='bob', alias='Bob James', uid='bob', vendor_specific={}, description='')]

    Note:
        ``GroupChat`` objects are picklable, thus it is RECOMMENDED
        to keep any object of its subclass also picklable.
    """

    def __init__(self, *, channel: Optional[SlaveChannel] = None, middleware: Optional[Middleware] = None,
                 module_name: str = "", channel_emoji: str = "", module_id: ModuleID = ModuleID(""), name: str = "",
                 alias: Optional[str] = None, id: ChatID = ChatID(""), uid: ChatID = ChatID(""), vendor_specific: Dict[str, Any] = None,
                 description: str = "", notification: ChatNotificationState = ChatNotificationState.ALL,
                 with_self: bool = True):
        super().__init__(channel=channel, middleware=middleware, module_name=module_name, channel_emoji=channel_emoji,
                         module_id=module_id, name=name, alias=alias, id=id, uid=uid, vendor_specific=vendor_specific,
                         description=description, notification=notification, with_self=with_self)
        self.verify()

    def verify(self):
        super().verify()
        assert all(isinstance(member, ChatMember) for member in self.members)
