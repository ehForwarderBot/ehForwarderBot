# Constants Objects

class MsgType:
    Text = "Text"
    Image = "Image"
    Audio = "Audio"
    File = "File"
    Location = "Location"
    Video = "Video"
    Link = "Link"
    Sticker = "Sticker"
    Unsupported = "Unsupported"
    Command = "Command"


class MsgSource:
    User = "User"
    Group = "Group"
    System = "System"


class TargetType:
    Member = "Member"
    Message = "Message"
    Substitution = "Substitution"


class ChannelType:
    Master = "Master"
    Slave = "Slave"

# Objects


class EFBChannel:
    channel_name = "Empty Channel"
    channel_emoji = "?"
    channel_id = "emptyChannel"
    channel_type = ChannelType.Slave
    queue = None
    supported_message_types = set()
    stop_polling = False

    def __init__(self, queue, mutex):
        """
        Initialize a channel.

        Args:
            queue (queue.Queue): Global message queue.
            mutex (threading.Lock): Global interaction thread lock.
        """
        self.queue = queue
        self.mutex = mutex

    def get_extra_functions(self):
        """Get a list of extra functions

        Returns:
            dict: A dict of functions marked as extra functions. `methods[methodName]()`
        """
        if self.channel_type == ChannelType.Master:
            raise NameError("get_extra_function is not available on master channels.")
        methods = {}
        for mName in dir(self):
            m = getattr(self, mName)
            if getattr(m, "extra_fn", False):
                methods[mName] = m
        return methods

    def send_message(self, msg):
        """
        Send message to slave channels.

        Args:
            msg (EFBMsg): Message object to be sent.

        Returns:
            EFBMsg: The same message object with message ID.
        """
        return "Not implemented"

    def poll(self, *args, **kwargs):
        return "Not implemented"

    def get_chats(self):
        """
        Return a list of available chats in the channel.

        Returns:
            list of dict: a list of available chats in the channel.
        """
        return "Not implemented"


class EFBMsg:
    """A message.

    Attributes:
        attributes (dict): Attributes used for a specific message type
        channel_emoji (str): Emoji Icon for the source Channel
        channel_id (str): ID for the source channel
        channel_name (str): Name of the source channel
        destination (dict): Destination (may be a user or a group)
        member (dict): Author of this msg in a group. `None` for private messages.
        origin (dict): Origin (may be a user or a group)
        source (MsgSource): Source of message: User/Group/System
        target (dict): Target (refers to @ messages and "reply to" messages.)
        text (str): text of the message
        type (MsgType): Type of message
        uid (str): Unique ID of message
        url (str): URL of multimedia file/Link share. `None` if N/A
        path (str): Local path of multimedia file. `None` if N/A
        file (file): File object to multimedia file, type "ra". `None` if N/A
        mime (str): MIME type of the file. `None` if N/A
        filename (str): File name of the multimedia file. `None` if N/A

    `target`:
        There are 3 types of targets: `Member`, `Message`, and `Substitution`

        TargetType: Member
            This is for the case where the message is targeting to a specific member in the group.
            `target['target']` here is a `user dict`.

            Example:
            ```
            target = {
               'type': TargetType.Member,
               'target': {
                   "name": "Target name",
                   'alias': 'Target alias',
                   'uid': 'Target UID',
               }
            }
            ```

        TargetType: Message
            This is for the case where the message is directly replying to another message.
            `target['target']` here is an `EFBMsg` object.

            Example:
            ```
            target = {
               'type': TargetType.Message,
               'target': EFBMsg()
            }
            ```

        TargetType: Substitution
            This is for the case when user "@-ed" a list of users in the message.
            `target['target']` here is a dict of correspondence between
            the string used to refer to the user in the message
            and a user dict.

            Example:
            ```
            target = {
               'type': TargetType.Substitution,
               'target': {
                  '@alice': {
                      'name': "Alice",
                      'alias': 'Alisi',
                      'uid': 123456
                  },
                  '@bob': {
                      'name': "Bob",
                      'alias': 'Baobu',
                      'uid': 654321
                  }
               }
            }
            ```

    `attributes`:
        A dict of attributes can be attached for some specific message types.
        Please specify `None` for values not available.

        Link:
            ```
            attributes = {
                "title": "Title of the article",
                "description": "Description of the article",
                "image": "URL to the thumbnail/featured image of the article",
                "url": "URL to the article"
            }
            ```

        Location:
            ```
            text = "Name of the location"
            attributes = {
                "longitude": float("A float number indicating longitude"),
                "latitude": float("A float number indicating latitude")
            }
            ```

        Command:
            Messages with type `Command` allow user to take action to
            a specific message, including vote, add friends, etc.

            Example:
            ```
            attributes = {
                "commands": [
                    {
                        "name": "A human-readable name for the command",
                        "callable": "name to the callable function in your channel object",
                        "args": [
                            "a list of positional parameters passed to your function"
                        ],
                        "kwargs": {
                            "desc": "a dict of keyword parameters passed to your function"
                        }
                    },
                    {
                        "name": "Greet @blueset on Telegram",
                        "callable": "send_message_by_username",
                        "args": [
                            "blueset",
                            "Hello!"
                        ],
                        "kwargs": {}
                    }
                ]
            }
            ```
    """
    channel_name = "Empty Channel"
    channel_emoji = "?"
    channel_id = "emptyChannel"
    source = MsgSource.User
    type = MsgType.Text
    member = None
    origin = {
        "name": "Origin name",
        'alias': 'Origin alias',
        'uid': 'Origin UID',
    }
    destination = {
        "channel": "channel_id",
        "name": "Destination name",
        'alias': 'Destination alias',
        'uid': 'Destination UID',
    }
    target = None
    uid = None
    text = ""
    url = None
    path = None
    file = None
    mime = None
    filename = None
    attributes = {}

    def __init__(self, channel=None):
        if isinstance(channel, EFBChannel):
            self.channel_name = channel.channel_name
            self.channel_emoji = channel.channel_emoji
            self.channel_id = channel.channel_id
