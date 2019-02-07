# coding=utf-8

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Set, Callable, IO, TYPE_CHECKING
from .constants import *

if TYPE_CHECKING:
    from .chat import EFBChat
    from .message import EFBMsg
    from .status import EFBStatus

__all__ = ["EFBChannel"]


class EFBChannel(ABC):
    """
    The abstract channel class.

    Attributes:
        channel_name (str):
            A human-friendly name of the channel.
        channel_emoji (str):
            Emoji icon of the channel. Recommended to use a
            visually-length-one emoji that represents
            the channel best.
        channel_type (:obj:`.ChannelType`): Type of the channel.
        supported_message_types (Set[:obj:`.MsgType`]):
            Types of messages that the channel accepts as incoming messages.
        channel_id (str):
            Unique identifier of the channel.
            Convention of IDs is specified in :doc:`/guide/packaging`.
            This ID will be appended with its instance ID when available.
        instance_id (str):
            The instance ID if available.
    """

    channel_name: str = "Empty channel"
    channel_emoji: str = "�"
    channel_id: str = "efb.empty_channel"
    channel_type: ChannelType
    instance_id: Optional[str] = None
    supported_message_types: Set[MsgType] = set()
    __version__: str = 'undefined version'

    def __init__(self, instance_id: str = None):
        """
        Initialize the channel.
        Inherited initializer must call the "super init" method
        at the beginning.

        Args:
            instance_id: Instance ID of the channel.
        """
        self.instance_id = instance_id
        if instance_id:
            self.channel_id += "#" + instance_id

    def get_extra_functions(self) -> Dict[str, Callable]:
        """Get a list of additional features

        Returns:
            Dict[str, Callable]: A dict of methods marked as additional features.
            Method can be called with ``get_extra_functions()["methodName"]()``.
        """
        if self.channel_type == ChannelType.Master:
            raise NameError("get_extra_function is not available on master channels.")
        methods = {}
        for mName in dir(self):
            m = getattr(self, mName)
            if callable(m) and getattr(m, "extra_fn", False):
                methods[mName] = m
        return methods

    @abstractmethod
    def send_message(self, msg: 'EFBMsg') -> 'EFBMsg':
        """send_message(msg: EFBMsg) -> EFBMsg

        Send a message to, or edit a sent message in
        the channel.

        Args:
            msg (:obj:`.EFBMsg`): Message object to be processed.

        Returns:
            :obj:`.EFBMsg`:
                The same message object with message ID from the
                recipient.

        Raises:
            :exc:`~.exceptions.EFBChatNotFound`: Raised when a chat
                required is not found.
            :exc:`~.exceptions.EFBMessageTypeNotSupported`: Raised
                when the message type sent is not supported by the
                channel.
            :exc:`~.exceptions.EFBOperationNotSupported`: Raised
                when an message edit request is sent, but not
                supported by the channel.
            :exc:`~.exceptions.EFBMessageNotFound`: Raised when
                an existing message indicated is not found.
                E.g.: The message to be edited, the message referred
                in the :attr:`msg.target <.EFBMsg.target>`
                attribute.
            :exc:`~.exceptions.EFBMessageError`: Raised when other
                error occurred while sending or editing the
                message.
        """
        raise NotImplementedError()

    @abstractmethod
    def poll(self):
        """
        Method to poll for messages. This method is called when
        the framework is initialized. This method should be blocking.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chats(self) -> List['EFBChat']:
        """get_chats() -> List[EFBChat]

        Return a list of available chats in the channel.

        Returns:
            List[.EFBChat]: a list of available chats in the channel.
        
        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None) -> 'EFBChat':
        """get_chat(self, chat_uid: str, member_uid: Optional[str] = None) -> EFBChat

        Get the chat object from a slave channel.
        
        Args:
            chat_uid (str): UID of the chat.
            member_uid (Optional[str]): UID of group member,
                only when the selected chat is a group.

        Returns:
           .EFBChat: The chat found.

        Raises:
            :exc:`~.exceptions.EFBChatNotFound`: Raised when a chat
                required is not found.

        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def send_status(self, status: 'EFBStatus'):
        """
        Send a status to the channel.

        Args:
            status (:obj:`.EFBStatus`): the status

        Raises:
            :exc:`~.exceptions.EFBChatNotFound`: Raised when a chat
                required is not found.
            :exc:`~.exceptions.EFBMessageNotFound`: Raised when
                an existing message indicated is not found.
                E.g.: The message to be removed.
            :exc:`~.exceptions.EFBOperationNotSupported`: Raised
                when the channel does not support message removal.
            :exc:`~.exceptions.EFBMessageError`: Raised when other
                error occurred while removing the message.

                .. note::
                    Avoid raising exceptions from this method
                    in Master Channels as it would be hard
                    for a Slave Channel to process the
                    exception.

        Note:
            This is not applicable to Slave Channels
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat_picture(self, chat: 'EFBChat') -> IO[bytes]:
        """get_chat_picture(chat: EFBChat) -> IO[bytes]

        Get the profile picture of a chat. Profile picture is
        also referred as profile photo, avatar, "head image"
        sometimes.
        
        Args:
            chat (.EFBChat): Chat to get picture from.

        Returns:
            IO[bytes]: Opened temporary file object.
            The file object must have appropriate extension name
            that matches to the format of picture sent,
            and seek to position 0.

            It can be deleted when closed if not required otherwise.

        Raises:
            :exc:`~.exceptions.EFBChatNotFound`: Raised when a chat
                required is not found.
            :exc:`~.exceptions.EFBOperationNotSupported`: Raised
                when the chat does not offer a profile picture.
            
        Examples:
            .. code:: Python
            
                if chat.channel_uid != self.channel_uid:
                    raise EFBChannelNotFound()
                file = tempfile.NamedTemporaryFile(suffix=".png")
                response = requests.post("https://api.example.com/get_profile_picture/png",
                                         data={"uid": chat.chat_uid})
                if response.status_code == 404:
                    raise EFBChatNotFound()
                file.write(response.content)
                file.seek(0)
                return file
                
        Note:
            This is not required by Master Channels
        """
        raise NotImplementedError()

    def stop_polling(self):
        """
        When EFB framework is asked to stop gracefully,
        this method is called to each channel object to
        stop all processes in the channel, save all
        status if necessary, and terminate polling.

        When the channel is ready to stop, the polling
        function must stop blocking. EFB framework will
        quit completely when all polling threads end.
        """
        raise NotImplementedError()

    def get_message_by_id(self, msg_id: str) -> Optional['EFBMsg']:
        """
        Get message entity by its ID.
        Applicable to both master channels and slave channels.
        Return ``None`` when message not found.

        Override this method and raise
        :exc:`~.exceptions.EFBOperationNotSupported`
        if it is not feasible to perform this for your platform.
        """
        raise NotImplementedError()
