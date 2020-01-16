# coding=utf-8

from abc import ABC
from typing import Optional, Dict, Callable, TYPE_CHECKING
from .types import ModuleID, InstanceID, ExtraCommandName

if TYPE_CHECKING:
    from .message import Message
    from .status import Status

__all__ = ['Middleware']


class Middleware(ABC):
    """
    Middleware class.

    Attributes:
        middleware_id (str):
            Unique ID of the middleware.
            Convention of IDs is specified in :doc:`/guide/packaging`.
            This ID will be appended with its instance ID when available.
        middleware_name (str): Human-readable name of the middleware.
        instance_id (str):
            The instance ID if available.
    """
    middleware_id: ModuleID = ModuleID("efb.empty_middleware")
    middleware_name: str = "Empty Middleware"
    instance_id: Optional[InstanceID] = None
    __version__: str = 'undefined version'

    def __init__(self, instance_id: Optional[InstanceID] = None):
        """
        Initialize the middleware.
        Inherited initializer MUST call the "super init" method
        at the beginning.

        Args:
            instance_id: Instance ID of the middleware.
        """
        if instance_id:
            self.instance_id = InstanceID(instance_id)
            self.middleware_id = ModuleID(self.middleware_id + "#" + instance_id)

    def get_extra_functions(self) -> Dict[ExtraCommandName, Callable]:
        """Get a list of additional features

        Returns:
            Dict[str, Callable]: A dict of methods marked as additional features.
            Method can be called with ``get_extra_functions()["methodName"]()``.
        """
        methods = {}
        for mName in dir(self):
            m = getattr(self, mName)
            if callable(m) and getattr(m, "extra_fn", False):
                methods[ExtraCommandName(mName)] = m
        return methods

    def process_message(self, message: 'Message') -> Optional['Message']:
        """
        Process a message with middleware

        Args:
            message (:obj:`~.message.Message`): Message object to process

        Returns:
            Optional[:obj:`~.message.Message`]: Processed message or None if discarded.
        """
        return message

    def process_status(self, status: 'Status') -> Optional['Status']:
        """
        Process a status update with middleware

        Args:
            status (:obj:`~.status.Status`): Message object to process

        Returns:
            Optional[:obj:`~.status.Status`]: Processed status or None if discarded.
        """
        return status
