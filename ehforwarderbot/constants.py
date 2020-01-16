# coding=utf-8

from enum import Enum

__all__ = ["MsgType"]


class MsgType(Enum):
    Text = "Text"
    """Text message"""

    Image = "Image"
    """
    Image (picture) message.

    Notes:
        Animated GIF images must use :attr:`Animation` type instead.
    """

    Voice = "Voice"
    """Voice messages, usually recorded right before sending."""

    Audio = Voice
    """Audio messages (deprecated).

    .. deprecated::
        Use :attr:`.Voice` if the message has a voice message (usually recorded).
        Use :attr:`.File` if the message has a music file (usually uploaded).
    """

    Animation = "Animation"
    """
    Message with an animation, usually in the form of GIF or
    soundless video.
    """

    Video = "Video"
    """Video message"""

    File = "File"
    """File message."""

    Location = "Location"
    """Location message."""

    Link = "Link"
    """
    Message that is mainly one specific link, or a
    text message with one link preview.
    """

    Sticker = "Sticker"
    """
    Pictures sent with few text caption, usually a
    transparent background, and a limited number
    of options that is usually not from the user's
    photo gallery.
    """

    Status = "Status"
    """
    Status from a user in a chat, usually typing and
    uploading.
    """

    Unsupported = "Unsupported"
    """
    Any type of message that is not listed above.
    A text representation is required.
    """
