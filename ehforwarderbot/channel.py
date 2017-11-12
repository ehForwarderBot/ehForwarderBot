from abc import ABC, abstractmethod
from tempfile import NamedTemporaryFile
from typing import Optional, Dict, List, Set, Callable

from .message import EFBMsg
from .constants import *
from .status import EFBStatus
from .chat import EFBChat

__all__ = ["EFBChannel"]


class EFBChannel(ABC):
    """
    The abstract channel class.
    
    Class Attributes:
        channel_name (str): Name of the channel.
        channel_emoji (str): Emoji icon of the channel.
        channel_id (str): Unique ID of the channel.
            Recommended to use the package ``__name__``.,
            e.g. ``ehforwarderbot.channels.master.blueset.telegram``.
        channel_type (:obj:`ehforwarderbot.constants.ChannelType`): Type of the channel.
        supported_message_types (Set[MsgType]): Types of messages that the channel accepts
            as incoming messages.
    """

    channel_name: str = "Empty channel"
    channel_emoji: str = "�"
    channel_id: str = "efb_empty_channel"
    channel_type: ChannelType = None
    supported_message_types: Set[MsgType] = set()
    stop_polling: bool = False
    __version__: str = 'undefined version'

    def get_extra_functions(self) -> Dict[str, Callable]:
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
    def send_message(self, msg: EFBMsg) -> EFBMsg:
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
    def get_chats(self) -> List[EFBChat]:
        """
        Return a list of available chats in the channel.

        Returns:
            list of :obj:`ehforwarderbot.EFBChat`: a list of available chats in the channel.
        
        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None) -> EFBChat:
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
    def send_status(self, status: EFBStatus):
        """
        Return the standard chat dict of the selected chat.

        Args:
            status (:obj:`ehforwarderbot.EFBStatus`): the status

        Note:
            This is not applicable to Slave Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat_picture(self, chat: EFBChat) -> NamedTemporaryFile:
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



