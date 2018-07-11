# coding=utf-8

from enum import Enum


class MsgType(Enum):
    Text = "Text"
    """Text message"""

    Image = "Image"
    """Image (picture) message"""

    Audio = "Audio"
    """Audio message. Including music and voice message."""

    File = "File"
    """Messages sent as a file."""

    Location = "Location"
    """Location message."""

    Video = "Video"
    """Video message"""

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


class ChatType(Enum):
    User = "User"
    Group = "Group"
    System = "System"
    Unknown = "Unknown"


class TargetType(Enum):
    Member = "Member"
    Message = "Message"
    Substitution = "Substitution"


class ChannelType(Enum):
    Master = "Master"
    Slave = "Slave"
