# coding=utf-8

from abc import ABC, abstractmethod
from typing import Optional, Dict, Set, Callable, TYPE_CHECKING, Sequence, BinaryIO, Collection

from .constants import MsgType
from .types import ModuleID, InstanceID, ExtraCommandName, ReactionName, ChatID, MessageID

if TYPE_CHECKING:
    from .chat import Chat
    from .message import Message
    from .status import Status

__all__ = ["Channel", "MasterChannel", "SlaveChannel"]


class Channel(ABC):
    """
    The abstract channel class.

    Attributes:
        channel_name (str):
            A human-friendly name of the channel.
        channel_emoji (str):
            Emoji icon of the channel. Recommended to use a
            visually-length-one (i.e. a single `grapheme cluster`_) emoji or
            other symbol that represents the channel best.
        channel_id (:obj:`.ModuleID` (str)):
            Unique identifier of the channel.
            Convention of IDs is specified in :doc:`/guide/packaging`.
            This ID will be appended with its instance ID when available.
        instance_id (str):
            The instance ID if available.

    .. _grapheme cluster: http://unicode.org/reports/tr29/
    """

    channel_name: str = "Empty channel"
    channel_emoji: str = "�"
    channel_id: ModuleID = ModuleID("efb.empty_channel")
    instance_id: Optional[InstanceID] = None
    __version__: str = 'undefined version'

    def __init__(self, instance_id: InstanceID = None):
        """
        Initialize the channel.
        Inherited initializer MUST call the "super init" method
        at the beginning.

        Args:
            instance_id: Instance ID of the channel.
        """
        if instance_id:
            self.instance_id = InstanceID(instance_id)
            self.channel_id = ModuleID(self.channel_id + "#" + instance_id)

    @abstractmethod
    def send_message(self, msg: 'Message') -> 'Message':
        """Process a message that is sent to, or edited in this channel.

        Notes:
            Master channel MUST take care of the returned object that contains
            the updated message ID. Depends on the implementation of slave
            channels, the message ID MAY change even after being edited. The old
            message ID MAY be disregarded for the new one.

        Args:
            msg (:obj:`~.message.Message`): Message object to be processed.

        Returns:
            :obj:`~.message.Message`:
                The same message object. Message ID of the object MAY be
                changed by the slave channel once sent. This can happen even
                when the message sent is an edited message.

        Raises:
            EFBChatNotFound:
                Raised when a chat required is not found.

            EFBMessageTypeNotSupported:
                Raised when the message type sent is not supported by the
                channel.

            EFBOperationNotSupported:
                Raised when an message edit request is sent, but not
                supported by the channel.

            EFBMessageNotFound:
                Raised when an existing message indicated is not found.
                E.g.: The message to be edited, the message referred
                in the :attr:`msg.target <.Message.target>`
                attribute.

            EFBMessageError:
                Raised when other error occurred while sending or editing the
                message.
        """
        raise NotImplementedError()

    @abstractmethod
    def poll(self):
        """
        Method to poll for messages. This method is called when
        the framework is initialized. This method SHOULD be blocking.
        """
        raise NotImplementedError()

    @abstractmethod
    def send_status(self, status: 'Status'):
        """
        Process a status that is sent to this channel.

        Args:
            status (:obj:`~.status.Status`): the status object.

        Raises:
            EFBChatNotFound:
                Raised when a chat required is not found.

            EFBMessageNotFound:
                Raised when an existing message indicated is not found.
                E.g.: The message to be removed.

            EFBOperationNotSupported:
                Raised when the channel does not support message removal.

            EFBMessageError:
                Raised when other error occurred while removing the message.

        Note:
            Exceptions SHOULD NOT be raised from this method
            by master channels as it would be hard for a slave channel
            to process the exception.

            This method is not applicable to Slave Channels.
        """
        raise NotImplementedError()

    def stop_polling(self):
        """
        When EFB framework is asked to stop gracefully,
        this method is called to each channel object to
        stop all processes in the channel, save all
        status if necessary, and terminate polling.

        When the channel is ready to stop, the polling
        function MUST stop blocking. EFB framework will
        quit completely when all polling threads end.
        """
        raise NotImplementedError()

    def get_message_by_id(self, chat: 'Chat', msg_id: MessageID) -> Optional['Message']:
        """
        Get message entity by its ID.
        Applicable to both master channels and slave channels.
        Return ``None`` when message not found.

        Override this method and raise
        :exc:`~.exceptions.EFBOperationNotSupported`
        if it is not feasible to perform this for your platform.

        Args:
            chat: Chat in slave channel / middleware.
            msg_id: ID of message from the chat in slave channel / middleware.
        """
        raise NotImplementedError()


class MasterChannel(Channel, ABC):
    """The abstract master channel class. All master channels MUST inherit
    this class.
    """


class SlaveChannel(Channel, ABC):
    """The abstract slave channel class. All slave channels MUST inherit
    this class.

    Attributes:
        supported_message_types (Set[:class:`~.constants.MsgType`]):
            Types of messages that the slave channel accepts as incoming messages.
            Master channels may use this value to decide what type of messages
            to send to your slave channel.

            Leaving this empty may cause the master channel to refuse sending
            anything to your slave channel.
        suggested_reactions (Optional[Sequence[str]]):
            A list of suggested reactions to be applied to messages.

            Reactions SHOULD be ordered in a meaningful way, e.g., the order
            used by the IM platform, or frequency of usage. Note that it is
            not necessary to list all suggested reactions if that is too long,
            or not feasible.

            Set to ``None`` when it is known that no reaction is supported to
            ANY message in the channel. Set to empty list when it is not feasible
            to provide a list of suggested reactions, for example, the list of
            reactions is different for each chat or message.
    """

    supported_message_types: Set[MsgType] = set()
    suggested_reactions: Optional[Sequence[ReactionName]] = None

    def get_extra_functions(self) -> Dict[ExtraCommandName, Callable]:
        """Get a list of additional features

        Returns:
            A dict of methods marked as additional features.
            Method can be called with ``get_extra_functions()["methodName"]()``.
        """
        methods = {}
        for mName in dir(self):
            m = getattr(self, mName)
            if callable(m) and getattr(m, "extra_fn", False):
                methods[ExtraCommandName(mName)] = m
        return methods

    @abstractmethod
    def get_chat_picture(self, chat: 'Chat') -> BinaryIO:
        """get_chat_picture(chat: Chat) -> BinaryIO

        Get the profile picture of a chat. Profile picture is
        also referred as profile photo, avatar, "head image"
        sometimes.

        Args:
            chat (.Chat): Chat to get picture from.

        Returns:
            BinaryIO: Opened temporary file object.
            The file object MUST have appropriate extension name
            that matches to the format of picture sent,
            and seek to position 0.

            It MAY be deleted or discarded once closed, if not needed otherwise.

        Raises:
            EFBChatNotFound:
                Raised when a chat required is not found.
            EFBOperationNotSupported:
                Raised when the chat does not offer a profile picture.

        Examples:
            .. code-block:: Python

                if chat.channel_uid != self.channel_uid:
                    raise EFBChannelNotFound()
                file = tempfile.NamedTemporaryFile(suffix=".png")
                response = requests.post("https://api.example.com/get_profile_picture/png",
                                         data={"uid": chat.uid})
                if response.status_code == 404:
                    raise EFBChatNotFound()
                file.write(response.content)
                file.seek(0)
                return file
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chat(self, chat_uid: ChatID) -> 'Chat':
        """
        Get the chat object from a slave channel.

        Args:
            chat_uid: ID of the chat.

        Returns:
           .Chat: The chat found.

        Raises:
            EFBChatNotFound:
                Raised when a chat required is not found.
        """
        raise NotImplementedError()

    @abstractmethod
    def get_chats(self) -> Collection['Chat']:
        """
        Return a list of available chats in the channel.

        Returns:
            Collection[:class:`.Chat`]: a list of available chats in the channel.
        """
        raise NotImplementedError()
