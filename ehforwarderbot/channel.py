from abc import ABCMeta, abstractmethod
from .constants import *

__all__ = ["EFBChannel"]


class EFBChannel:
    """
    The abstract channel class.
    
    Attributes:
        channel_name (str): Name of the channel.
        channel_emoji (str): Emoji icon of the channel.
        channel_id (str): Unique ID of the channel.
            Recommended format: ``"{author}_{name}_{type}"``, 
            e.g. ``"eh_telegram_master"``.
        channel_type (:obj:`ehforwarderbot.constants.ChannelType`): Type of the channel.
        coordinator (:obj:`ehforwarderbot.EFBCoordinator`): Channel coordinator.
    """
    __metaclass__ = ABCMeta

    channel_name = "Empty Channel"
    channel_emoji = "?"
    channel_id = "emptyChannel"
    channel_type = ChannelType.Slave
    coordinator = None
    supported_message_types = set()
    stop_polling = False

    def __init__(self, shared_data):
        """
        Initialize a channel.

        Args:
            shared_data (:obj:`ehforwarderbot.EFBCoordinator`): Shared data.
        """
        self.coordinator = shared_data

    def get_extra_functions(self):
        """Get a list of extra functions

        Returns:
            dict[str: callable]: A dict of functions marked as extra functions. 
            Method can be called with ``get_extra_functions()["methodName"]()``.
        """
        if self.channel_type == ChannelType.Master:
            raise NameError("get_extra_function is not available on master channels.")
        methods = {}
        for mName in dir(self):
            m = getattr(self, mName)
            if getattr(m, "extra_fn", False):
                methods[mName] = m
        return methods

    @abstractmethod
    def send_message(self, msg):
        """
        Send a message to the channel

        Args:
            msg (:obj:`ehforwarderbot.EFBMsg`): Message object to be sent.

        Returns:
            :obj:`ehforwarderbot.EFBMsg`: The same message object with message ID.
        """
        raise NotImplementedError()

    @abstractmethod
    def poll(self):
        """
        Method to poll for messages.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chats(self):
        """
        Return a list of available chats in the channel.

        Returns:
            list of :obj:`ehforwarderbot.EFBChat`: a list of available chats in the channel.
        
        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat(self, chat_uid, member_uid=None):
        """
        Return the standard chat dict of the selected chat.
        
        Args:
            chat_uid (str): UID of the chat.
            member_uid (:obj:`str`, optional): UID of group member, 
                only when the selected chat is a group. 

        Returns:
            :obj:`ehforwarderbot.EFBChat`: the standard chat dict of the chat.
        
        Raises:
            KeyError: Chat is not found in the channel.
            ValueError: ``member_uid`` is provided but chat indicated is
                not a group.
        
        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def send_status(self, status):
        """
        Return the standard chat dict of the selected chat.

        Args:
            status (:obj:`ehforwarderbot.EFBStatus`): the status

        Note:
            This is not required by Slave Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat_picture(self, chat):
        """
        Get the profile picture of a chat.
        
        Args:
            chat (EFBChat): Chat to get picture from.

        Returns:
            tempfile.NamedTemporaryFile: Opened temporary file object.
                The object must have appropriate suffix that correspond to 
                the format of picture sent, and seek to position 0.
        
        Raises:
            ValueError: the chat is not found in the channel.
            
        Examples:
            .. code:: Python
            
                if chat.channel_uid != self.channel_uid:
                    raise ValueError("Incorrect channel")
                file = tempfile.NamedTemporaryFile(suffix=".png")
                response = requests.post("https://api.example.com/get_profile_picture/png",
                                         data={"uid": chat.chat_uid})
                if response.status_code == 404:
                    raise ValueError("Chat not found")
                file.write(response.content)
                file.seek(0)
                return file
                
        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()
