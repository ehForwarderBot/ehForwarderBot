from abc import ABC, abstractmethod
from typing import IO, Dict, Optional, List, Any, Tuple

from .constants import *
from .chat import EFBChat
from .channel import EFBChannel


class EFBMsg:
    """A message.

    Attributes:
        attributes (Optional[:obj:`.EFBMsgAttribute`]):
            Attributes used for a specific message type.
            Only specific message type requires this attribute. Defaulted to
            ``None``.

            - Link: :obj:`.EFBMsgLinkAttribute`
            - Location: :obj:`.EFBMsgLocationAttribute`
            - Status: Typing/Sending files/etc.: :obj:`.EFBMsgStatusAttribute`

            .. Note::
                Do NOT use object the abstract class
                :class:`.EFBMsgAttribute` for
                ``attributes``, but object of specific class instead.


        author (:obj:`.EFBChat`): Author of this message.
        chat (:obj:`.EFBChat`): Sender of the message
        commands (Opitonal[:obj:`EFBMsgCommands`]): Commands attached to the message
        deliver_to (:obj:`.EFBChannel`): The channel that the message is to be delivered to
        edit (bool): Flag this up if the message is edited.
        file (IO[bytes]): File object to multimedia file, type "ra". ``None`` if N/A
            Recommended to use ``NamedTemporaryFile`` object, the file is recommended to be
            deleted when closed, if not used otherwise.
            All file object must be rewind back to 0 (``file.seek(0)``) before sending.
        filename (str): File name of the multimedia file. ``None`` if N/A
        is_system (bool): Mark as true if this message is a system message.
        mime (str): MIME type of the file. ``None`` if N/A
        path (str): Local path of multimedia file. ``None`` if N/A
        substitutions (Opitonal[:obj:`EFBMsgSubstitutions`]):
            Substitutions of messages, usually used when
            the some parts of the text of the message
            refers to another user or chat.
        target (Optional[:obj:`EFBMsg`]):
            Target message (usually for messages that "replies to" 
            another message).

            .. note::

                This message may be a "minimum message", with only required fields:

                - :attr:`.EFBMsg.chat`
                - :attr:`.EFBMsg.author`
                - :attr:`.EFBMsg.text`
                - :attr:`.EFBMsg.type`
                - :attr:`.EFBMsg.uid`

        text (str): text of the message
        type (:obj:`.MsgType`): Type of message
        uid (str): Unique ID of message.
            Usually stores the message ID from slave channel.
            This ID must be unique among all chats in the same channel.
        url (str): URL of multimedia file/Link share. ``None`` if N/A

            .. Note::
                Some channels may not support message editing.
                Some channels may issue a new uid for edited message.

        vendor_specific (Dict[str, Any]): 
            A series of vendor specific attributes attached. This can be
            used by any other channels or middlewares that is compatible
            with such information. Note that no guarentee is provided
            for information in this section.

    """
    def __init__(self):
        self.attributes: Optional[EFBMsgAttribute] = None
        self.author: EFBChat = None
        self.chat: EFBChat = None
        self.deliver_to: EFBChannel = None
        self.edit: bool = False
        self.file: Optional[IO[bytes]] = None
        self.filename: Optional[str] = None
        self.is_system: bool = False
        self.mime: Optional[str] = None
        self.path: Optional[str] = None
        self.substitutions: Optional[EFBMsgSubstitutions] = None
        self.target: Optional[EFBMsg] = None
        self.text: str = ""
        self.type: MsgType = MsgType.Text
        self.uid: Optional[str] = None
        self.url: Optional[str] = None
        self.vendor_specific: Dict[str, Any] = dict()

    # TODO: Add __str__


class EFBMsgAttribute(ABC):
    """Abstract class for a message attribute."""
    @abstractmethod
    def __init__(self):
        raise NotImplementedError("Do not use the abstract class EFBMsgAttribute")


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

    def __init__(self, title: str = None, description: Optional[str] = None,
                 image: Optional[str] = None, url: str = None):
        """
        Args:
            title (str): Title of the link.
            description (str, optional): Description of the link.
            image (str, optional): Image/thumbnail URL of the link.
            url (str): URL of the link.
        """
        if title is None or url is None:
            raise ValueError("Title and URL is required.")
        self.title = title
        self.description = description
        self.image = image
        self.url = url


class EFBMsgLocationAttribute(EFBMsgAttribute):
    """
    EFB location message attribute.

    Attributes:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.
    """
    latitude: float = 0
    longitude: float = 0

    def __init__(self, latitude: float, longitude: float):
        """
        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
        """
        self.latitude = latitude
        self.longitude = longitude


class EFBMsgCommand:
    """
    EFB command message command.

    Attributes:
        name (str): Human-friendly name of the command.
        callable_name (str): Callable name of the command.
        args (List[Any]): Arguments passed to the function.
        kwargs (Dict[str, Any]): Keyword arguments passed to the function.
    """
    name: str = ""
    callable_name: str = ""
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}

    def __init__(self, name: str, callable_name: str, args: List[Any]=None, kwargs: Optional[Dict[str, Any]]=None):
        """
        Args:
            name (str): Human-friendly name of the command.
            callable_name (str): Callable name of the command.
            args (Optional[List[Any]]): Arguments passed to the function. Defaulted to empty list;
            kwargs (Optional[Dict[str, Any]]): Keyword arguments passed to the function.
                Defaulted to empty dict.
        """
        if args is None:
            args = list()
        if kwargs is None:
            kwargs = dict()
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(callable_name, str):
            raise TypeError("callable must be a string.")
        if not isinstance(args, list):
            raise TypeError("args must be a list.")
        if not isinstance(kwargs, dict):
            raise TypeError("kwargs must be a dict.")
        self.name = name
        self.callable_name = callable_name
        self.args = args.copy()
        self.kwargs = kwargs.copy()


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
        if not (isinstance(commands, list) and len(commands) > 0 and all(
                isinstance(i, EFBMsgCommand) for i in commands)):
            raise ValueError("There must be one or more commands, "
                             "and all of them must be in type EFBMsgCommand.")
        self.commands = commands.copy()


class EFBMsgStatusAttribute(EFBMsgAttribute):
    """
    EFB Message status attribute.
    Message with type ``Status`` notifies the other end to update a chat-specific
    status, such as typing, send files, etc.

    Attributes:
        status_type: Type of status, possible values are defined in the
            ``EFBMsgStatusAttribute``.
        TYPING: Used in :attr:`status_type`, represent the status of typing.
        UPLOADING_FILE: Used in :attr:`status_type`, represent the status of uploading file.
        UPLOADING_IMAGE: Used in :attr:`status_type`, represent the status of uploading image.
        UPLOADING_AUDIO: Used in :attr:`status_type`, represent the status of uploading audio.
        UPLOADING_VIDEO: Used in :attr:`status_type`, represent the status of uploading video.

    """
    TYPING = "TYPING"
    UPLOADING_FILE = "UPLOADING_FILE"
    UPLOADING_IMAGE = "UPLOADING_IMAGE"
    UPLOADING_AUDIO = "UPLOADING_AUDIO"
    UPLOADING_VIDEO = "UPLOADING_VIDEO"

    def __init__(self, status_type, timeout=5000):
        """
        Args:
            status_type: Type of status.
            timeout (Opional[int]): 
                Number of milliseconds for this status to expire.
                Default to 5 seconds.
        """
        self.status_type = status_type


class EFBMsgSubstitutions:
    """
    EFB message substitutions.

    This is for the case when user "@-referred" a list of users in the message.
    Substitutions here is a dict of correspondence between
    the string used to refer to the user in the message
    and a user dict.

    Attributes:
        substitutions
            Dict[Tuple[int, int], :obj:`.EFBChat`]):
            Dictionary of text substitutions targeting to a user or member.

            The key of the dictionary is a tuple of two :obj:`int` s, where first
            of it is the starting position in the string, and the second is the
            ending position defined similar to Python's substring. A tuple of
            ``(3, 15)` corresponds to ``msg.text[3:15]``.
            The value of the tuple ``(a, b)`` must lie within ``a ∈ [0, l)``,
            ``b ∈ (a, l]``, where ``l`` is the length of the message text.

            Value of the dict may be any user of the chat, or a member of a
            group. Notice that the :obj:`EFBChat` object here must NOT be a
            group.
    """
    substitutions: Dict[Tuple[int, int], EFBChat] = None

    def __init__(self, substitutions: Dict[Tuple[int, int], EFBChat]):
        if not isinstance(substitutions, dict):
            raise TypeError("Substitutions must be a dict.")
        for i in substitutions:
            if not isinstance(i, tuple) or not len(i) == 2 or not isinstance(i[0], int) or not isinstance(i[1], int)\
                    or not i[0] < i[1]:
                raise TypeError("Substitution %s's index must be a tuple of 2 integers where the first one is less"
                                "than the second one." % i)
            if not isinstance(substitutions[i], EFBMsg):
                raise TypeError("Substitution %s is not a message object."
                                % i)
            if substitutions[i].is_chat and \
                    substitutions[i].chat_type == ChatType.Group:
                raise ValueError("Substitution %s is not a user." % i)
        self.substitutions = substitutions
