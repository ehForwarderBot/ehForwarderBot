# coding=utf-8

from abc import ABC, abstractmethod
from collections.abc import Collection as CCollection
from collections.abc import Mapping as CMapping
from contextlib import suppress
from os import PathLike
from pathlib import Path
from typing import IO, Dict, Optional, List, Any, Tuple, Mapping, Collection, Union

from . import coordinator
from .constants import *
from .chat import EFBChat
from .channel import EFBChannel
from .types import Reactions, MessageID


class EFBMsgAttribute(ABC):
    """Abstract class of a message attribute."""

    @abstractmethod
    def __init__(self):
        raise NotImplementedError("Do not use the abstract class EFBMsgAttribute")

    @abstractmethod
    def verify(self):
        raise NotImplementedError()


class EFBMsgLinkAttribute(EFBMsgAttribute):
    """
    EFB link message attribute.

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
        return "<EFBMsgLinkAttribute, {attr.title}: {attr.description} " \
               "({attr.image}) @ {attr.url}>".format(attr=self)

    def verify(self):
        if not self.url:
            raise ValueError("URL does not exist")
        if not self.title:
            raise ValueError("Title does not exist")


class EFBMsgLocationAttribute(EFBMsgAttribute):
    """
    EFB location message attribute.

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
        return "<EFBMsgLocationAttribute: {attr.latitude}, {attr.longitude}>".format(attr=self)

    def verify(self):
        if self.latitude is None or not isinstance(self.latitude, float):
            raise ValueError("Latitude is invalid.")
        if self.longitude is None or not isinstance(self.longitude, float):
            raise ValueError("Longitude is invalid.")


class EFBMsgCommand:
    """
    EFB message command.
    This object records a way to call a method in the module object.
    In case where the message has an ``author`` from a different module
    from the ``chat``, this function should be called on the ``author``'s
    module.

    The method specified must return either a ``str`` as result or ``None``
    if this message will be further edited or deleted for interactions.

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
        return "<EFBMsgCommand: {name}, {callable_name}({params})>".format(
            name=self.name,
            callable_name=self.callable_name,
            params=", ".join(self.args + tuple("%r=%r" % i for i in self.kwargs.items()))
        )

    def verify(self):
        if not isinstance(self.name, str) or not self.name:
            raise TypeError("name must be a non-empty string.")
        if not isinstance(self.callable_name, str) or not self.callable_name:
            raise TypeError("callable must be a non-empty string.")
        if not isinstance(self.args, CCollection):
            raise TypeError("args must be a collection.")
        if not isinstance(self.kwargs, CMapping):
            raise TypeError("kwargs must be a mapping.")


class EFBMsgCommands:
    """
    EFB message commands.
    Message commands allow user to take action to
    a specific message, including vote, add friends, etc.

    Attributes:
        commands (list of :obj:`EFBMsgCommand`): Commands for the message.
    """

    commands: List[EFBMsgCommand] = []

    def __init__(self, commands: List[EFBMsgCommand]):
        """
        Args:
            commands (list of :obj:`EFBMsgCommand`): Commands for the message.
        """
        self.commands = commands.copy()
        self.verify()

    def __str__(self):
        return str(self.commands)

    def verify(self):
        if not isinstance(self.commands, list):
            raise TypeError(f"Commands must be a list, but {type(self.commands)} is found.")
        if not len(self.commands) > 0:
            raise ValueError("There must be at least one command in the list.")
        for i in self.commands:
            if not isinstance(i, EFBMsgCommand):
                raise ValueError(f"{i} is not in EFBMsgCommand type.")
            i.verify()


class EFBMsgStatusAttribute(EFBMsgAttribute):
    """
    EFB Message status attribute.
    Message with type ``Status`` notifies the other end to update a chat-specific
    status, such as typing, send files, etc.

    Attributes:
        status_type: Type of status, possible values are defined in the
            ``EFBMsgStatusAttribute``.
        timeout (Optional[int]):
                Number of milliseconds for this status to expire.
                Default to 5 seconds.
        Types: List of status types supported
    """

    class Types(Enum):
        """
        Attributes:
            TYPING:
                Used in :attr:`~.ehforwarderbot.message.EFBMsgStatusAttribute.status_type`,
                represent the status of typing.
            UPLOADING_FILE:
                Used in :attr:`~.ehforwarderbot.message.EFBMsgStatusAttribute.status_type`,
                represent the status of uploading file.
            UPLOADING_IMAGE:
                Used in :attr:`~.ehforwarderbot.message.EFBMsgStatusAttribute.status_type`,
                represent the status of uploading image.
            UPLOADING_VOICE:
                Used in :attr:`~.ehforwarderbot.message.EFBMsgStatusAttribute.status_type`,
                represent the status of uploading voice.
            UPLOADING_VIDEO:
                Used in :attr:`~.ehforwarderbot.message.EFBMsgStatusAttribute.status_type`,
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
        self.status_type: 'EFBMsgStatusAttribute.Types' = status_type
        self.timeout: int = timeout
        self.verify()

    def __str__(self):
        return "<EFBMsgStatusAttribute: {attr.status_type} @ {attr.timeout}ms>".format(attr=self)

    def verify(self):
        if self.status_type is None or not isinstance(self.status_type, self.Types):
            raise ValueError("Status type is invalid.")
        if not isinstance(self.timeout, int) or self.timeout < 0:
            raise ValueError("Timeout must be a non-negative integer.")


class EFBMsgSubstitutions(Dict[Tuple[int, int], EFBChat]):
    """
    EFB message substitutions.

    This is for the case when user "@-referred" a list of users in the message.
    Substitutions here is a dict of correspondence between the index of
    substring used to refer to a user/chat in the message and the chat object
    it referred to.

    Values of the dictionary shall be either a member of the chat (``self`` or
    the opponent for private chats, group members for group chats) or another
    chat of the slave channel.

    A key in this dictionary shall be a tuple of two :obj:`int`\\ s, where first
    of it is the starting position in the string, and the second is the
    ending position defined similar to Python's substring. A tuple of
    ``(3, 15)`` corresponds to ``msg.text[3:15]``.
    The value of the tuple ``(a, b)`` must lie within ``a ∈ [0, l)``,
    ``b ∈ (a, l]``, where ``l`` is the length of the message text.

    Value of the dict may be any user of the chat, or a member of a
    group. Notice that the :obj:`EFBChat` object here must NOT be a
    group.

    Type:
        Dict[Tuple[int, int], :obj:`.EFBChat`]
    """

    def __init__(self, substitutions: Dict[Tuple[int, int], EFBChat]):
        if not isinstance(substitutions, dict):
            raise TypeError("Substitutions must be a dict.")
        super().__init__(substitutions)
        self.verify()

    @property
    def is_mentioned(self) -> bool:
        """Returns ``True`` if you are mentioned in this message.

        In the case where a chat (private or group) is mentioned in this
        message instead of a group member, you would also be considered
        mentioned if you are a member of the chat.
        """
        return any(
            (i.is_self or (i.is_chat and i.has_self))
            for i in self.values()
        )

    def verify(self):
        for i in self:
            if not isinstance(i, tuple) or not len(i) == 2 or not isinstance(i[0], int) or not isinstance(i[1], int) \
                    or not i[0] < i[1]:
                raise TypeError(f"Index of substitution {i} must be a tuple of 2 integers where the first one is less "
                                "than the second one.")
            if not isinstance(self[i], EFBChat):
                raise TypeError(f"Substitution {i} is not a chat object.")
            if self[i].is_chat and \
                    self[i].chat_type == ChatType.Group:
                raise ValueError(f"Substitution {i} is a group.")
        ranges = sorted(self.keys())
        if ranges and (ranges[0][0] < 0 or ranges[0][1] < ranges[0][0]):
            raise ValueError(f"Index {ranges[0]} is invalid.")
        for i in range(1, len(ranges)):
            if ranges[i][0] < 0 or ranges[i][1] < ranges[i][0]:
                raise ValueError(f"Index {ranges[i]} is invalid.")
            if ranges[i][0] < ranges[i - 1][1]:
                raise ValueError(f"Index {ranges[i]} overlaps with {ranges[i - 1]}.")
        for i in self.values():
            i.verify()


class EFBMsg:
    """A message.

    Note:
        ``EFBMsg`` objects are picklable, thus it is strongly recommended
        to keep any object of its subclass also picklable.

    Attributes:
        attributes (Optional[:obj:`.EFBMsgAttribute`]):
            Attributes used for a specific message type.
            Only specific message type requires this attribute. Defaulted to
            ``None``.

            - Link: :obj:`.EFBMsgLinkAttribute`
            - Location: :obj:`.EFBMsgLocationAttribute`
            - Status: Typing/Sending files/etc.: :obj:`.EFBMsgStatusAttribute`

            .. Note::
                Do NOT use object of the abstract class
                :class:`.EFBMsgAttribute` for
                ``attributes``, but object of specific class instead.

        author (:obj:`.EFBChat`): Author of this message.
        chat (:obj:`.EFBChat`): Sender of the message.
        commands (Optional[:obj:`EFBMsgCommands`]): Commands attached to the message

            This attribute will be ignored in _Status_ messages.
        deliver_to (:obj:`.EFBChannel`): The channel that the message is to be delivered to.
        edit (bool): Flag this up if the message is edited.
            Flag only this if no multimedia file is modified, otherwise flag up both
            this one and ``edit_media`` as well.

            If no media file is modified, the edited message may carry no information about
            the file.

            This attribute will be ignored in _Status_ messages.
        edit_media (bool): Flag this up if any file attached to the message is modified.
            If this value is true, ``edit`` must also be ``True``.
            This attribute is ignored if the message type is not supposed to contain any
            media file, e.g. :attr:`~MsgType.Text`, :attr:`~MsgType.Location`, etc.

            This attribute will be ignored in _Status_ messages.
        file (Optional[IO[bytes]]): File object to multimedia file, type "rb". ``None`` if N/A.
            recommended to use ``NamedTemporaryFile`` object, the file can be
            deleted when closed, if not used otherwise.
            All file object must be rewind back to 0 (``file.seek(0)``) before sending.
        filename (Optional[str]): File name of the multimedia file. ``None`` if N/A
        is_system (bool): Mark as true if this message is a system message.
        mime (Optional[str]): MIME type of the file. ``None`` if N/A
        path (Optional[Path]): Local path of multimedia file. ``None`` if N/A
        reactions (Dict[str, Collection[:obj:`EFBChat`]]):
            Indicate reactions to the message. Dictionary key is the canonical name
            of reaction, usually an emoji. Value is a collection of users
            who reacted to the message with that certain emoji.
            All :obj:`EFBChat` objects in this dict must be of a user or a
            group member.

            This attribute will be ignored in _Status_ messages.
        substitutions (Optional[:obj:`EFBMsgSubstitutions`]):
            Substitutions of messages, usually used when
            the some parts of the text of the message
            refers to another user or chat.

            This attribute will be ignored in _Status_ messages.
        target (Optional[:obj:`EFBMsg`]):
            Target message (usually for messages that "replies to"
            another message).

            This attribute will be ignored in _Status_ messages.

            .. note::

                This message may be a "minimum message", with only required fields:

                - :attr:`.EFBMsg.chat`
                - :attr:`.EFBMsg.author`
                - :attr:`.EFBMsg.text`
                - :attr:`.EFBMsg.type`
                - :attr:`.EFBMsg.uid`

        text (str): text of the message

            This attribute will be ignored in _Status_ messages.
        type (:obj:`.MsgType`): Type of message
        uid (str): Unique ID of message.
            Usually stores the message ID from slave channel.
            This ID must be unique among all chats in the same channel.

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
                 attributes: Optional[EFBMsgAttribute] = None,
                 author: EFBChat = None,
                 chat: EFBChat = None,
                 commands: Optional[EFBMsgCommands] = None,
                 deliver_to: EFBChannel = None,
                 edit: bool = False,
                 edit_media: bool = False,
                 file: Optional[IO[bytes]] = None,
                 filename: Optional[str] = None,
                 is_system: bool = False,
                 mime: Optional[str] = None,
                 path: Optional[Union[str, Path]] = None,
                 reactions: Reactions = None,
                 substitutions: Optional[EFBMsgSubstitutions] = None,
                 target: 'Optional[EFBMsg]' = None,
                 text: str = "",
                 type: MsgType = MsgType.Unsupported,
                 uid: Optional[MessageID] = None,
                 vendor_specific: Dict[str, Any] = None,):
        self.attributes: Optional[EFBMsgAttribute] = attributes
        self.author: EFBChat = author  # type: ignore
        self.chat: EFBChat = chat  # type: ignore
        self.commands: Optional[EFBMsgCommands] = commands
        self.deliver_to: EFBChannel = deliver_to  # type: ignore
        self.edit: bool = edit
        self.edit_media: bool = edit_media
        self.file: Optional[IO[bytes]] = file
        self.filename: Optional[str] = filename
        self.is_system: bool = is_system
        self.mime: Optional[str] = mime
        self.path: Optional[Path]
        if isinstance(path, str):
            self.path = Path(path)
        else:
            self.path = path
        self.reactions: Reactions = reactions if reactions is not None else dict()
        self.substitutions: Optional[EFBMsgSubstitutions] = substitutions
        self.target: Optional[EFBMsg] = target
        self.text: str = text
        self.type: MsgType = type
        self.uid: Optional[MessageID] = uid
        self.vendor_specific: Dict[str, Any] = vendor_specific if vendor_specific is not None else dict()

    def __str__(self):
        return "<EFBMsg, {msg.author}@{msg.chat} [{msg.type.name}]: {msg.text}; {msg.uid}>".format(msg=self)

    def __repr__(self):
        return "<EFBMsg, {msg.author}@{msg.chat} [{msg.type.name}]: " \
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
        """
        if self.author is None or not isinstance(self.author, EFBChat):
            raise ValueError("Author is not valid.")
        else:
            self.author.verify()
        if self.chat is None or not isinstance(self.chat, EFBChat):
            raise ValueError("Chat is not valid.")
        elif self.chat is not self.author:  # Prevent repetitive verification
            self.chat.verify()
        if self.type is None or not isinstance(self.type, MsgType):
            raise ValueError("Type is not valid.")
        if self.deliver_to is None or not isinstance(self.deliver_to, EFBChannel):
            raise ValueError("Deliver_to is not valid.")
        if self.type in (MsgType.Voice, MsgType.File, MsgType.Image, MsgType.Sticker, MsgType.Video) and \
                ((not self.edit) or (self.edit and self.edit_media)):
            if self.file is None or not hasattr(self.file, "read") or not hasattr(self.file, "close"):
                raise ValueError("File is not valid.")
            if self.mime is None or not self.mime or not isinstance(self.mime, str):
                raise ValueError("MIME is not valid.")
            if self.path is None or not self.path or not isinstance(self.path, (str, PathLike)):
                raise ValueError("Path is not valid.")
        if self.type == MsgType.Location and (self.attributes is None
                                              or not isinstance(self.attributes, EFBMsgLocationAttribute)):
            raise ValueError("Attribute of location message is invalid.")
        if self.type == MsgType.Link and (self.attributes is None
                                          or not isinstance(self.attributes, EFBMsgLinkAttribute)):
            raise ValueError("Attribute of link message is invalid.")
        if self.type == MsgType.Status and (self.attributes is None
                                            or not isinstance(self.attributes, EFBMsgStatusAttribute)):
            raise ValueError("Attribute of status message is invalid.")

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
            if isinstance(dt, EFBChannel):
                self.deliver_to = dt

        # Try to load file from original path
        if self.path:
            with suppress(IOError):
                self.file = open(self.path, 'rb')
