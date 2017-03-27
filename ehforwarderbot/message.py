from .constants import *
from .channel import EFBChannel

__all__ = ["EFBMsg"]


class EFBMsg:
    """A message.

    Attributes:
        attributes (instance of :obj:`ehforwarderbot.message.EFBMsgAttribute`, optional):
            Attributes used for a specific message type.
            Only specific message type requires this attribute. Defaulted to
            ``None``.

            - Link: :obj:`ehforwarderbot.EFBMsgLinkAttribute`
            - Location: :obj:`ehforwarderbot.EFBMsgLocationAttribute`
            - Command: :obj:`ehforwarderbot.EFBMsgLocationAttribute`

            Note:
                Do not use object the abstract class :class:`ehforwarderbot.message.EFBMsgAttribute`
                for ``attributes``, but object of specific class instead.

        channel_emoji (str): Emoji icon for the source channel
        channel_id (str): ID for the source channel
        channel_name (str): Name of the source channel
        destination (:obj:`ehforwarderbot.EFBChat`): Destination (may be a user or a group)
        is_system (bool): Indicate if this message is a system message.
        member (:obj:`ehforwarderbot.EFBMember`, optional): Author of this msg in a group.
            ``None`` for private messages.
        origin (:obj:`ehforwarderbot.EFBChat`): Sender of the message
        target (dict): Target (refers to @ messages and "reply to" messages.)

            There are 3 types of targets: ``Member``, ``Message``, and ``Substitution``

            TargetType: Member
                This is for the case where the message is targeting to a specific member in the group.
                ``target['target']`` here is a `user dict`.

                Example::

                    target = {
                       'type': TargetType.Member,
                       'target': {
                           "name": "Target name",
                           'alias': 'Target alias',
                           'uid': 'Target UID',
                       }
                    }


            TargetType: Message
                This is for the case where the message is directly replying to another message.
                ``target['target']`` here is an ``EFBMsg`` object.

                Example::

                    target = {
                       'type': TargetType.Message,
                       'target': EFBMsg()
                    }

            TargetType: Substitution
                This is for the case when user "@-ed" a list of users in the message.
                ``target['target']`` here is a dict of correspondence between
                the string used to refer to the user in the message
                and a user dict.

                Example::

                    target = {
                       'type': TargetType.Substitution,
                       'target': {
                          '@alice': {
                              'name': "Alice",
                              'alias': 'Arisu',
                              'uid': 123456
                          },
                          '@bob': {
                              'name': "Bob",
                              'alias': 'Boobu',
                              'uid': 654321
                          }
                       }
                    }

        text (str): text of the message
        type (:obj:`ehforwarderbot.MsgType`): Type of message
        uid (str): Unique ID of message
        url (str): URL of multimedia file/Link share. ``None`` if N/A
        path (str): Local path of multimedia file. ``None`` if N/A
        file (file): File object to multimedia file, type "ra". ``None`` if N/A
        mime (str): MIME type of the file. ``None`` if N/A
        filename (str): File name of the multimedia file. ``None`` if N/A

    """
    channel_name = "Empty Channel"
    channel_emoji = "?"
    channel_id = "emptyChannel"
    source = ChatType.User
    type = MsgType.Text
    member = None
    origin = None
    destination = None
    target = None
    uid = None
    text = ""
    url = None
    path = None
    file = None
    mime = None
    filename = None
    attributes = None
    is_system = False

    def __init__(self, channel=None):
        """
        Initialize an EFB message.

        Args:
            channel (:obj:`ehforwarderbot.EFBChannel`, optional):
                Sender channel used to initialize the message.
                This will set the ``channel_name``, ``channel_emoji``, and
                ``channel_id`` for the message object.
        """
        if isinstance(channel, EFBChannel):
            self.channel_name = channel.channel_name
            self.channel_emoji = channel.channel_emoji
            self.channel_id = channel.channel_id


class EFBMsgAttribute:
    def __init__(self):
        raise TypeError("Do not use the abstract class EFBMsgAttribute")


class EFBMsgLinkAttribute(EFBMsgAttribute):
    """
    EFB link message attribute.

    Attributes:
        title (str): Title of the link.
        description (str, optional): Description of the link.
        image (str, optional): Image/thumbnail URL of the link.
        url (str): URL of the link.
    """
    title = ""
    description = None
    image = None
    url = ""

    def __init__(self, title=None, description=None, image=None, url=None):
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
    EFB location message attirbute.

    Attributes:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the locaiton.
    """
    latitude = 0
    longitude = 0

    def __init__(self, latitude, longitude):
        """
        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the locaitonself.
        """
        self.latitude = latitude
        self.longitude = longitude


class EFBMsgCommandAttribute(EFBMsgAttribute):
    """
    EFB command message attribute.
    Messages with type ``Command`` allow user to take action to
    a specific message, including vote, add friends, etc.

    Attributes:
        commands (list of :obj:`EFBMsgCommand`): Commands for the message.
    """

    commands = []

    def __init__(self, commands):
        """
        Args:
            commands (list of :obj:`EFBMsgCommand`): Commands for the message.
        """
        if not (isinstance(commands, list) and len(commands) > 0 and all(isinstance(i, EFBMsgCommand) for i in commands)):
            raise ValueError("There must be one or more commands, all of them must be in type EFBMsgCommand.")
        self.commands = commands.copy()


class EFBMsgCommand:
    """
    EFB command message command.

    Attributes:
        name (str): Human-frindly name of the command.
        callable (str): Callable name of the command.
        args (list): Arguments passed to the funciton.
        kwargs (dict of str: anything): Keyword arguments passed to the function.
    """
    name = ""
    callable = ""
    args = []
    kwargs = {}

    def __init__(self, name, callable, args=[], kwargs={}):
        """
        Args:
            name (str): Human-frindly name of the command.
            callable (str): Callable name of the command.
            args (list, optional): Arguments passed to the funciton. Defaulted to empty list;
            kwargs (dict of str: anything, optional): Keyword arguments passed to the function.
                Defaulted to empty dict.
        """
        if not isinstance(name, str):
            raise TypeError("name must be a string.")
        if not isinstance(callable, str):
            raise TypeError("callable must be a string.")
        if not isinstance(args, list):
            raise TypeError("args must be a list.")
        if not isinstance(kwargs, dict):
            raise TypeError("kwargs must be a dict.")
        self.name = name
        self.callable = callable
        self.args = args.copy()
        self.kwargs = kwargs.copy()


class EFBMsgTarget:
    def __init__(self):
        raise TypeError("Do not use the abstract class EFBMsgTarget")


class EFBMsgTargetMessage(EFBMsgTarget):
    """
    EFB message target - message.

    Attributes:
        message (:obj:`ehforwarderbot.EFBMsg`): The message targeted to.

            Note:
                This message may be a "minimum message", with only required fields:
                - ``channel_id``
                - ``channel_name``
                - ``channel_emoji``
                - ``origin``
                - ``destination``
                - ``member`` (if available)
                - ``text``
                - ``type``
                - ``uid``
    """
    message = None

    def __init__(self, message):
        self.message = message
