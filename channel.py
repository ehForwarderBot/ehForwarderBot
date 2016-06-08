# Constants Objects

class MsgType:
    Text = "Text"
    Image = "Image"
    Audio = "Audio"
    File = "File"
    Location = "Location"
    Video = "Video"
    Link = "Link"
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

    extra_fn = []

    def __init__(self, queue):
        self.queue = queue

    def get_extra_functions(self):
        """Get a list of extra functions

        Returns:
            dict: A dict of functions marked as extra functions. `methods[methodName]()`
        """
        methods = {}
        for mName in dir(self):
            m = getattr(self, mName)
            if getattr(m, "extra_fn", False):
                methods[mName](getattr(self, m))
        return methods

    def send_message(self, *arg, **kwarg):
        return "Not implemented"

    def poll(self, *arg, **kward):
        return "Not implemented"

    def get_chats(self, *arg, **kward):
        return "Not implemented"

    def get_group_members(self, *arg, **kward):
        return "Not implemented"


class EFBMsg:
    """A message

    Attributes:
        attributes (dict): Attributes used for a specific message type
        channel_emoji (str): Emoji Icon for the source Channel
        channel_id (str): ID for the source channel
        channel_name (str): Name of the source channel
        destination (dict): Destination (may be a user or a group)
        member (dict): Author of this msg in a group. `None` for priv msgs.
        origin (dict): Origin (may be a user or a group)
        source (MsgSource): Source of message: User/Group/System
        target (dict): Target (refers to @ messages and "reply to" messages.)
        text (str): text of the message
        type (MsgType): Type of message
        uid (str): Unique ID of message
        url (str): URL of multimedia file/Link share. `None` if N/A
        file (file): File object to multimedia object. `None` if N/A
        mime (str): MIME type of the file. `None` if N/A
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
        "channel": "channel_id"
        "name": "Destination name",
        'alias': 'Destination alias',
        'uid': 'Destination UID',
    }
    target = None
    #
    # TargetType: Member
    #
    # target = {
    #    'type': TargetType.Member,
    #    'target': {
    #        "name": "Target name",
    #        'alias': 'Target alias',
    #        'uid': 'Target UID',
    #    }
    # }
    #
    # TargetType: Message
    #
    # target = {
    #    'type': TargetType.Message,
    #    'target': EFBMsg()
    # }
    #
    # TargetType: Substitution
    #
    # target = {
    #    'type': TargetType.Substitution,
    #    'target': {
    #       '@alice': {
    #           'name': "Alice",
    #           'alias': 'Alisi',
    #           'uid': 123456
    #       },
    #       '@bob': {
    #           'name': "Bob",
    #           'alias': 'Baobu',
    #           'uid': 654321
    #       }
    #    }
    # }
    uid = "Message UID"
    text = "Message"
    url = None
    file = None
    mime = None
    attributes = {}

    def __init__(self, channel=None):
        if isinstance(channel, EFBChannel):
            self.channel_name = channel.channel_name
            self.channel_emoji = channel.channel_emoji
            self.channel_id = channel.channel_id
