from .channel import EFBChannel
from .constants import ChatType


class EFBChat:
    channel_id = None
    channel_emoji = None
    channel_name = None
    chat_name = None
    chat_type = None
    chat_alias = None
    chat_uid = None
    is_chat = True

    _members = []

    chat = None

    @property
    def members(self):
        return self._members.copy()

    @members.setter
    def members(self, value):
        self._members = value.copy()

    def __init__(self, channel=None):
        if isinstance(channel, EFBChannel):
            self.channel_name = channel.channel_name
            self.channel_emoji = channel.channel_emoji
            self.channel_id = channel.channel_id

    def self(self):
        """
        Set the chat as yourself.
        In this context, "yourself" means the user behind the master channel.
        Every channel should relate this to the corresponding target.  
        
        Returns:
            EFBChat: This object.
        """
        self.chat_name = "You"
        self.chat_alias = None
        self.chat_uid = "__self__"
        self.chat_type = ChatType.User
        return self

    def system(self):
        """
        Set the chat as a system chat. 
        Only set for channel-level and group-level system chats.
        
        Returns:
            EFBChat: This object.
        """
        self.chat_name = "System"
        self.chat_alias = None
        self.chat_uid = "__system__"
        self.chat_type = ChatType.User
        return self
