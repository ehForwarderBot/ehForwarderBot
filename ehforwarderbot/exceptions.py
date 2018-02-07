# coding=utf-8


class EFBException(Exception):
    """A general class to indicate that the exception is from EFB framework."""
    pass


class EFBChatNotFound(EFBException):
    """
    Raised by a slave channel when a chat indicated is not found.

    Can be raised by any method that involves a chat or a message.
    """
    pass


class EFBChannelNotFound(EFBException):
    """
    Raised by the coordinator when the message sent delivers to
    a missing channel.
    """
    pass


class EFBMessageError(EFBException):
    """
    Raised by slave channel for any other error occurred when sending
    a message or a status.

    Can be raised in :meth:`.EFBChannel.send_message` and :meth:`.EFBChannel.send_status`.
    """
    pass


class EFBMessageNotFound(EFBMessageError):
    """
    Raised by a slave channel when a message indicated is not found.

    Can be raised in :meth:`.EFBChannel.send_message` (edited message / target message not found)
    and in :meth:`.EFBChannel.send_status` (message to delete is not found).
    """
    pass


class EFBMessageTypeNotSupported(EFBMessageError):
    """
    Raised by a slave channel when the indicated message type is not supported.

    Can be raised in :meth:`.EFBChannel.send_message`.
    """
    pass


class EFBOperationNotSupported(EFBMessageError):
    """
    Raised by slave channels when a chat operation is not supported.
    E.g.: cannot edit message, cannot delete message.

    Can be raised in :meth:`.EFBChannel.send_message` and :meth:`.EFBChannel.send_status`.
    """
    pass
