"""A list of type aliases when no separate class is defined for some types of
values. Types for user-facing values (display names, descriptions, message text,
etc.) are not otherwise defined.

Most of types listed here are defined under the "NewType" syntax in order to
clarify some ambiguous values not covered by simple type checking. This is only
useful if you are using static type checking in your development. If you are
not using type checking of any kind, you can simply ignore values in this
module.
"""
from typing import Collection, TYPE_CHECKING, Mapping
from typing_extensions import NewType

if TYPE_CHECKING:
    from .chat import ChatMember


ReactionName = NewType('ReactionName', str)
"""Canonical representation of a reaction, usually an emoji."""

Reactions = Mapping[ReactionName, Collection['ChatMember']]
"""Reactions to a message."""

ModuleID = NewType('ModuleID', str)
"Module ID, including instance ID after ``#`` if available."

InstanceID = NewType('InstanceID', str)
"Instance ID of a module."

ChatID = NewType('ChatID', str)
"Chat ID from slave channel or middleware, applicable to both chat and chat members."

MessageID = NewType('MessageID', str)
"Message ID from slave channel or middleware."

ExtraCommandName = NewType('ExtraCommandName', str)
"""Command name of additional features, in the format of
``^[A-Za-z][A-Za-z0-9_]{0,19}$``.
"""
