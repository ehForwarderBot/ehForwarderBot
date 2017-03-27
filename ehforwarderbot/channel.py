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
        channel_type (:obj:`ehforwarderbot`): Type of the channel.
        queue (queue.Queue): Global message queue.
        mutex (threading.Lock): Global interaction thread lock.
    """
    __metaclass__ = ABCMeta

    channel_name = "Empty Channel"
    channel_emoji = "?"
    channel_id = "emptyChannel"
    channel_type = ChannelType.Slave
    queue = None
    supported_message_types = set()
    stop_polling = False

    def __init__(self, queue, mutex, slaves=None):
        """
        Initialize a channel.

        Args:
            queue (queue.Queue): Global message queue.
            mutex (threading.Lock): Global interaction thread lock.
            slaves (`obj`:dict:, optional): List of slave channels. Only
                offered to master channel.
        """
        self.queue = queue
        self.mutex = mutex
        self.slaves = slaves

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
        Send message to slave channels.

        Args:
            msg (:obj:`ehforwarderbot.EFBMsg`): Message object to be sent.

        Returns:
            :obj:`ehforwarderbot.EFBMsg`: The same message object with message ID.
        """
        raise NotImplementedError()

    @abstractmethod
    def poll(self):
        raise NotImplementedError()

    @abstractmethod
    def get_chats(self):
        """
        Return a list of available chats in the channel.

        Returns:
            list[:obj:`ehforwarderbot.EFBChat`]: a list of available chats in the channel.
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
        """
        raise NotImplementedError()
