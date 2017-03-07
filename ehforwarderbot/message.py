from .constants import *
from .channel import EFBChannel


class EFBMsg:
    """A message.

    Attributes:
        attributes (dict): Attributes used for a specific message type
    
            A dict of attributes can be attached for some specific message types.
            Please specify ``None`` for values not available.
    
            Link::
    
                attributes = {
                    "title": "Title of the article",
                    "description": "Description of the article",
                    "image": "URL to the thumbnail/featured image of the article",
                    "url": "URL to the article"
                }
    
            Location::
    
                text = "Name of the location"
                attributes = {
                    "longitude": float("A float number indicating longitude"),
                    "latitude": float("A float number indicating latitude")
                }
    
            Command:
                Messages with type ``Command`` allow user to take action to
                a specific message, including vote, add friends, etc.
    
                Example::
    
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

        channel_emoji (str): Emoji Icon for the source Channel
        channel_id (str): ID for the source channel
        channel_name (str): Name of the source channel
        destination (:obj:`ehforwarderbot.chat.EFBChat`): Destination (may be a user or a group)
        member (:obj:`ehforwarderbot.chat.EFBMember`): Author of this msg in a group. ``None`` for private messages.
        origin (:obj:`ehforwarderbot.chat.EFBChat`): Origin (may be a user or a group)
        source (:class:`ehforwarderbot.constants.ChatType`): Source of message: User/Group/System
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
        type (:obj:`ehforwarderbot.constants.MsgType`): Type of message
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
    attributes = {}

    def __init__(self, channel=None):
        """
        Initialize an EFB Message.
        
        Args:
            channel (:obj:`ehforwarderbot.channel.EFBChannel`, optional):
                Sender channel used to initialize the message.
                This will set the ``channel_name``, ``channel_emoji``, and 
                ``channel_id`` for the message object.
        """
        if isinstance(channel, EFBChannel):
            self.channel_name = channel.channel_name
            self.channel_emoji = channel.channel_emoji
            self.channel_id = channel.channel_id
