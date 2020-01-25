# coding=utf-8

from abc import ABC, abstractmethod
from collections.abc import Collection as CCollection
from collections.abc import Mapping as CMapping
from contextlib import suppress
from enum import Enum
from os import PathLike
from pathlib import Path
from typing import Dict, Optional, List, Any, Tuple, Mapping, Collection, Union, BinaryIO

from . import coordinator
from .channel import Channel
from .chat import Chat, ChatMember, SelfChatMember
from .constants import MsgType
from .types import Reactions, MessageID


class MessageAttribute(ABC):
    """Abstract class of a message attribute."""

    @abstractmethod
    def __init__(self):
        raise NotImplementedError("Do not use the abstract class MessageAttribute")

    @abstractmethod
    def verify(self):
        raise NotImplementedError()


class LinkAttribute(MessageAttribute):
    """
    Attributes for link messages.

    Attributes:
        title (str): Title of the link.
        description (str, optional): Description of the link.
        image (str, optional): Image/thumbnail URL of the link.
        url (str): URL of the link.
    """
    title: str = ""
    description: Optional[str] = None
    image: Optional[str] = None
    url: str = ""

    # noinspection PyMissingConstructor
    def __init__(self, title: str, description: Optional[str] = None,
                 image: Optional[str] = None, url: str = ""):
        """
        Args:
            title (str): Title of the link.
            description (str, optional): Description of the link.
            image (str, optional): Image/thumbnail URL of the link.
            url (str): URL of the link.
        """
        self.title = title
        self.description = description
        self.image = image
        self.url = url
        self.verify()

    def __str__(self):
        return "<LinkAttribute, {attr.title}: {attr.description} " \
               "({attr.image}) @ {attr.url}>".format(attr=self)

    def verify(self):
        assert self.url, "URL does is empty"
        assert self.title, "Title is empty"


class LocationAttribute(MessageAttribute):
    """
    Attributes for location messages.

    Attributes:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
    """
    latitude: float = 0
    longitude: float = 0

    # noinspection PyMissingConstructor
    def __init__(self, latitude: float, longitude: float):
        """
        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
        """
        self.latitude = latitude
        self.longitude = longitude
        self.verify()

    def __str__(self):
        return "<LocationAttribute: {attr.latitude}, {attr.longitude}>".format(attr=self)

    def verify(self):
        assert isinstance(self.latitude, float), f"Latitude {self.latitude!r} is not a float."
        assert isinstance(self.longitude, float), f"Longitude {self.longitude!r} is not a float."


class MessageCommand:
    """
    A message command.

    This object records a way to call a method in the module object.
    In case where the message has an :attr:`~.Message.author` from a different
    module from the :attr:`~.Message.chat`, this function MUST be called on
    the :attr:`~.Message.author`’s module.

    The method specified MUST return either a ``str`` as result or ``None``
    if this message will be edited or deleted for further interactions.

    Attributes:
        name (str): Human-friendly name of the command.
        callable_name (str): Callable name of the command.
        args (Collection[Any]): Arguments passed to the function.
        kwargs (Mapping[str, Any]): Keyword arguments passed to the function.
    """
    name: str = ""
    callable_name: str = ""
    args: Tuple = tuple()
    kwargs: Mapping[str, Any] = {}

    def __init__(self, name: str, callable_name: str, args: Collection[Any] = None,
                 kwargs: Optional[Mapping[str, Any]] = None):
        """
        Args:
            name (str): Human-friendly name of the command.
            callable_name (str): Callable name of the command.
            args (Optional[Collection[Any]]): Arguments passed to the function. Defaulted to empty list;
            kwargs (Optional[Mapping[str, Any]]): Keyword arguments passed to the function.
                Defaulted to empty dict.
        """
        self.name = name
        self.callable_name = callable_name
        if args is not None:
            self.args = tuple(args)
        if kwargs is not None:
            self.kwargs = dict(kwargs)
        self.verify()

    def __str__(self):
        return "<MessageCommand: {name}, {callable_name}({params})>".format(
            name=self.name,
            callable_name=self.callable_name,
            params=", ".join(self.args + tuple("%r=%r" % i for i in self.kwargs.items()))
        )

    def verify(self):
        assert isinstance(self.name, str) and self.name, \
            f"name {self.name!r} must be a non-empty string."
        assert isinstance(self.callable_name, str) and self.callable_name, \
            f"callable {self.callable_name!r} must be a non-empty string."
        assert isinstance(self.args, CCollection), \
            f"args {self.args!r} must be a collection."
        assert isinstance(self.kwargs, CMapping), \
            f"kwargs {self.kwargs!r} must be a mapping."


class MessageCommands(List[MessageCommand]):
    """Message commands.

    Message commands allow user to take action to
    a specific message, including vote, add friends, etc.

    Attributes:
        commands (list of :obj:`MessageCommand`): Commands for the message.
    """

    def __init__(self, commands: List[MessageCommand]):
        """
        Args:
            commands (list of :obj:`MessageCommand`): Commands for the message.
        """
        super().__init__(commands)
        self.verify()

    def verify(self):
        assert len(self) > 0, "There must be at least one command in the list."
        for i in self:
            assert isinstance(i, MessageCommand), f"{i!r} is not in MessageCommand type."
            i.verify()


class StatusAttribute(MessageAttribute):
    """Attributes for status messages.

    Message with type ``Status`` notifies the other end to update a chat-specific
    status, such as typing, send files, etc.

    Attributes:
        status_type: Type of status, possible values are defined in the
            ``StatusAttribute``.
        timeout (Optional[int]):
                Number of milliseconds for this status to expire.
                Default to 5 seconds.
        Types: List of status types supported
    """

    class Types(Enum):
        """
        Attributes:
            TYPING:
                Used in :attr:`~.ehforwarderbot.message.StatusAttribute.status_type`,
                represent the status of typing.
            UPLOADING_FILE:
                Used in :attr:`~.ehforwarderbot.message.StatusAttribute.status_type`,
                represent the status of uploading file.
            UPLOADING_IMAGE:
                Used in :attr:`~.ehforwarderbot.message.StatusAttribute.status_type`,
                represent the status of uploading image.
            UPLOADING_VOICE:
                Used in :attr:`~.ehforwarderbot.message.StatusAttribute.status_type`,
                represent the status of uploading voice.
            UPLOADING_VIDEO:
                Used in :attr:`~.ehforwarderbot.message.StatusAttribute.status_type`,
                represent the status of uploading video.
        """
        TYPING = "TYPING"
        UPLOADING_FILE = "UPLOADING_FILE"
        UPLOADING_IMAGE = "UPLOADING_IMAGE"
        UPLOADING_VOICE = "UPLOADING_VOICE"
        UPLOADING_VIDEO = "UPLOADING_VIDEO"

    # noinspection PyMissingConstructor
    def __init__(self, status_type: Types, timeout: int = 5000):
        """
        Args:
            status_type: Type of status.
            timeout (Optional[int]):
                Number of milliseconds for this status to expire.
                Default to 5 seconds.
        """
        self.status_type: 'StatusAttribute.Types' = status_type
        self.timeout: int = timeout
        self.verify()

    def __str__(self):
        return "<StatusAttribute: {attr.status_type} @ {attr.timeout}ms>".format(attr=self)

    def verify(self):
        assert isinstance(self.status_type, self.Types), \
            f"Status type is invalid."
        assert isinstance(self.timeout, int) and self.timeout >= 0, \
            "Timeout {self.timeout!r} must be a non-negative integer."


class Substitutions(Dict[Tuple[int, int], Union[Chat, ChatMember]]):
    """
    Message text substitutions, or “@-references”.

    This is for the case when user "@-referred" a list of users in the message.
    Substitutions here is a dict of correspondence between the index of
    substring used to refer to a user/chat in the message and the chat object
    it referred to.

    Values of the dictionary MUST be either a member of the chat (``self`` or
    the other for private chats, group members for group chats) or another
    chat of the slave channel.

    A key in this dictionary is a tuple of two :obj:`int`\\ s, where first
    of it is the starting position in the string, and the second is the
    ending position defined similar to Python's substring. A tuple of
    ``(3, 15)`` corresponds to ``msg.text[3:15]``.
    The value of the tuple ``(a, b)`` MUST satisfy :math:`0 ≤ a < b ≤ l`,
    where :math:`l` is the length of the message text.

    Type:
        Dict[Tuple[int, int], :obj:`.Chat`]
    """

    def __init__(self, substitutions: Mapping[Tuple[int, int], Union[Chat, ChatMember]]):
        assert isinstance(substitutions, dict), "Substitutions must be a dict."
        super().__init__(substitutions)
        self.verify()

    @staticmethod
    def _is_has_self(i: Union[Chat, ChatMember]) -> bool:
        """Check if a chat / chat member is/has the User Themself."""
        if isinstance(i, Chat):
            return i.has_self
        return isinstance(i, SelfChatMember)

    @property
    def is_mentioned(self) -> bool:
        """Returns ``True`` if you are mentioned in this message.

        In the case where a chat (private or group) is mentioned in this
        message instead of a group member, you will also be considered
        mentioned if you are a member of the chat.
        """
        return any(self._is_has_self(i) for i in self.values())

    def verify(self):
        for i in self:
            assert isinstance(i, tuple) and len(i) == 2, f"Index {i!r} must be a tuple of length 2"
            assert all(isinstance(j, int) for j in i), f"Index {i!r} must consist of 2 ints"
            assert i[0] < i[1], f"First number {i[0]} must be less than the second number {i[1]}"
            assert isinstance(self[i], (Chat, ChatMember)), f"Substitution {i} is neither a chat member not a chat."
        ranges = sorted(self.keys())
        if not ranges:
            return
        assert 0 <= ranges[0][0] < ranges[0][1], f"Index {ranges[0]} is invalid."
        for i in range(1, len(ranges)):
            assert 0 <= ranges[i][0] < ranges[i][1], f"Index {ranges[i]} is invalid."
            assert ranges[i][0] >= ranges[i - 1][1], f"Index {ranges[i]} overlaps with {ranges[i - 1]}."
        for i in self.values():
            i.verify()


class Message:
    """A message.

    Note:
        ``Message`` objects are picklable, thus it is strongly RECOMMENDED
        to keep any object of its subclass also picklable.

    Keyword Args:
        attributes (Optional[:obj:`.MessageAttribute`]):
            Attributes used for a specific message type.
            Only specific message type requires this attribute. Defaulted to
            ``None``.

            - Link: :obj:`.LinkAttribute`
            - Location: :obj:`.LocationAttribute`
            - Status: Typing/Sending files/etc.: :obj:`.StatusAttribute`

            .. Note::
                Do NOT use object of the abstract class
                :class:`.MessageAttribute` for
                ``attributes``, but object of specific class instead.

        chat (:obj:`.Chat`): Sender of the message.
        author (:obj:`.ChatMember`): Author of this message. Author of the message
            MUST be indicated as a part of the same :attr:`~.message.Message.chat`
            this message is from. If the message is sent from the User Themself,
            this MUST be an object of :class:`.SelfChatMember`.

            Note that the author MAY not be inside :attr:`~.Chat.members` of the
            chat of this message. The author MAY have a different
            :attr:`~.BaseChat.module_id` from the :attr:`~.Message.chat`, and
            could be unretrievable otherwise.
        commands (Optional[:obj:`MessageCommands`]): Commands attached to the message

            This attribute will be ignored in _Status_ messages.
        deliver_to (:obj:`.Channel`): The channel that the message is to be delivered to.
        edit (bool): Flag this up if the message is edited.
            Flag only this if no multimedia file is modified, otherwise flag up both
            this one and ``edit_media`` as well.

            If no media file is modified, the edited message MAY carry no information about
            the file.

            This attribute will be ignored in _Status_ messages.
        edit_media (bool): Flag this up if any file attached to the message is modified.
            If this value is true, ``edit`` MUST also be ``True``.
            This attribute is ignored if the message type is not supposed to contain any
            media file, e.g. :attr:`~MsgType.Text`, :attr:`~MsgType.Location`, etc.

            This attribute will be ignored in _Status_ messages.
        file (Optional[BinaryIO]): File object to multimedia file, type "rb". ``None`` if N/A.
            Recommended to use :class:`NamedTemporaryFile`.
            The file SHOULD be able to be safely deleted (or otherwise discarded)
            once closed. All file object MUST be sought back to 0
            (``file.seek(0)``) before sending.
        filename (Optional[str]): File name of the multimedia file. ``None`` if N/A
        is_system (bool): Mark as true if this message is a system message.
        mime (Optional[str]): MIME type of the file. ``None`` if N/A
        path (Optional[Path]): Local path of multimedia file. ``None`` if N/A
        reactions (Dict[str, Collection[:obj:`Chat`]]):
            Indicate reactions to the message. Dictionary key is the canonical name
            of reaction, usually an emoji. Value is a collection of users
            who reacted to the message with that certain emoji.
            All :obj:`Chat` objects in this dict MUST be members in the
            chat of this message.

            This attribute will be ignored in _Status_ messages.
        substitutions (Optional[:obj:`Substitutions`]):
            Substitutions of messages, usually used when
            the some parts of the text of the message
            refers to another user or chat.

            This attribute will be ignored in _Status_ messages.
        target (Optional[:obj:`Message`]):
            Target message (usually for messages that "replies to"
            another message).

            This attribute will be ignored in _Status_ messages.

            .. note::

                This message MAY be a "minimum message", with only required fields:

                - :attr:`.Message.chat`
                - :attr:`.Message.author`
                - :attr:`.Message.text`
                - :attr:`.Message.type`
                - :attr:`.Message.uid`

        text (str): Text of the message.

            This attribute will be ignored in _Status_ messages.
        type (:obj:`.MsgType`): Type of message
        uid (str): Unique ID of message.
            Usually stores the message ID from slave channel.
            This ID MUST be unique among all chats in the same channel.

            .. Note::
                Some channels may not support message editing.
                Some channels may issue a new uid for edited message.

        vendor_specific (Dict[str, Any]):
            A series of vendor specific attributes attached. This can be
            used by any other channels or middlewares that is compatible
            with such information. Note that no guarantee is provided
            for information in this section.
    """

    def __init__(self,
                 *,
                 attributes: Optional[MessageAttribute] = None,
                 chat: Chat = None,
                 author: ChatMember = None,
                 commands: Optional[MessageCommands] = None,
                 deliver_to: Channel = None,
                 edit: bool = False,
                 edit_media: bool = False,
                 file: Optional[BinaryIO] = None,
                 filename: Optional[str] = None,
                 is_system: bool = False,
                 mime: Optional[str] = None,
                 path: Optional[Union[str, Path]] = None,
                 reactions: Reactions = None,
                 substitutions: Optional[Substitutions] = None,
                 target: 'Optional[Message]' = None,
                 text: str = "",
                 type: MsgType = MsgType.Unsupported,
                 uid: Optional[MessageID] = None,
                 vendor_specific: Dict[str, Any] = None, ):
        self.attributes: Optional[MessageAttribute] = attributes
        self.chat: Chat = chat  # type: ignore
        self.author: ChatMember = author  # type: ignore
        self.commands: Optional[MessageCommands] = commands
        self.deliver_to: Channel = deliver_to  # type: ignore
        self.edit: bool = edit
        self.edit_media: bool = edit_media
        self.file: Optional[BinaryIO] = file
        self.filename: Optional[str] = filename
        self.is_system: bool = is_system
        self.mime: Optional[str] = mime
        self.path: Optional[Path]
        if isinstance(path, str):
            self.path = Path(path)
        else:
            self.path = path
        self.reactions: Reactions = reactions if reactions is not None else dict()
        self.substitutions: Optional[Substitutions] = substitutions
        self.target: Optional[Message] = target
        self.text: str = text
        self.type: MsgType = type
        self.uid: Optional[MessageID] = uid
        self.vendor_specific: Dict[str, Any] = vendor_specific if vendor_specific is not None else dict()

    @property
    def status(self) -> Optional[StatusAttribute]:
        """Get the status attributes of the current message, if available."""
        if isinstance(self.attributes, StatusAttribute):
            return self.attributes
        return None

    @property
    def link(self) -> Optional[LinkAttribute]:
        """Get the link attributes of the current message, if available."""
        if isinstance(self.attributes, LinkAttribute):
            return self.attributes
        return None

    @property
    def location(self) -> Optional[LocationAttribute]:
        """Get the location attributes of the current message, if available."""
        if isinstance(self.attributes, LocationAttribute):
            return self.attributes
        return None

    def __str__(self):
        return "<Message, {msg.author}@{msg.chat} [{msg.type.name}]: {msg.text}; {msg.uid}>".format(msg=self)

    def __repr__(self):
        return "<Message, {msg.author}@{msg.chat} [{msg.type.name}]: " \
               "{msg.text}; " \
               "Attributes: {msg.attributes}; " \
               "Delivering to: {msg.deliver_to}; " \
               "Edited: {msg.edit}; " \
               "System message: {msg.is_system}; " \
               "Substitutions: {msg.substitutions}; " \
               "Target messages: {msg.target}; " \
               "UID: {msg.uid}; " \
               "Reactions: {msg.reactions}; " \
               "File: {msg.file} ({msg.filename} @ {msg.path}), {msg.mime}; " \
               "Vendor: {msg.vendor_specific}>".format(msg=self)

    def verify(self):
        """
        Verify the validity of message.

        Raises:
            AssertionError: when the message is not valid
        """
        assert isinstance(self.author, ChatMember), f"Author ({self.author!r}) is not valid."
        self.author.verify()
        assert isinstance(self.chat, Chat), f"Chat ({self.chat!r}) is not valid."
        self.chat.verify()
        assert isinstance(self.type, MsgType), \
            f"Type ({self.type!r}) is not valid."
        assert isinstance(self.deliver_to, Channel), \
            f"deliver_to ({self.deliver_to!r}) is not valid."
        if self.type in (MsgType.Voice, MsgType.File, MsgType.Image, MsgType.Sticker, MsgType.Video) and \
                ((not self.edit) or (self.edit and self.edit_media)):
            assert hasattr(self.file, "read") or not hasattr(self.file, "close"), \
                f"File ({self.file!r}) is not valid."
            assert self.mime or not isinstance(self.mime, str), \
                f"MIME ({self.mime!r}) is not valid."
            assert self.path or not isinstance(self.path, (str, PathLike)), \
                f"Path ({self.path!r}) is not valid."
        assert self.type != MsgType.Location or isinstance(self.attributes, LocationAttribute), \
            f"Attribute of location message ({self.attributes!r}) is invalid."
        assert self.type != MsgType.Link or isinstance(self.attributes, LinkAttribute), \
            f"Attribute of link message ({self.attributes!r}) is invalid."
        assert self.type != MsgType.Status or isinstance(self.attributes, StatusAttribute), \
            f"Attribute of status message ({self.attributes!r}) is invalid."

        if self.attributes:
            self.attributes.verify()

        if self.commands:
            self.commands.verify()

        if self.substitutions:
            self.substitutions.verify()

    def __getstate__(self):
        state = self.__dict__.copy()
        # Remove file object
        if state.get('file', None) is not None:
            del state['file']

        # Convert channel object to channel ID
        if state['deliver_to'] is not None:
            state['deliver_to'] = state['deliver_to'].channel_id
        return state

    def __setstate__(self, state: Dict[str, Any]):
        self.__dict__.update(state)

        # Try to load "deliver_to" channel
        with suppress(NameError):
            dt = coordinator.get_module_by_id(state['deliver_to'])
            if isinstance(dt, Channel):
                self.deliver_to = dt

        # Try to load file from original path
        if self.path:
            with suppress(IOError):
                self.file = open(self.path, 'rb')
