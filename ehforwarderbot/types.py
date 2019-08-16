"""A list of type aliases when no separate class is defined for some types of values.
User-facing types (display names, descriptions, message text, etc.) shall not be included here,
"""
from typing import Collection, Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from . import EFBChat


ReactionName = str
"""Canonical representation of a reaction, usually an emoji."""

Reactions = Dict[ReactionName, Collection['EFBChat']]
"""Reactions to a message."""

ModuleID = str
"Module ID, including instance ID after ``#`` if available."

InstanceID = str
"Instance ID of a module."

ChatID = str
"Chat ID from slave channel or middleware."

MessageID = str
"Message ID from slave channel or middleware."

ExtraCommandName = str
"""Command name of additional features, in the format of
``^[A-Za-z][A-Za-z0-9_]{0,19}$``.
"""
