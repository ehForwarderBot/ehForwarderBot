from abc import ABC
from typing import Optional

from .message import EFBMsg
from .status import EFBStatus

__all__ = ['EFBMiddleware']


class EFBMiddleware(ABC):
    """
    Middleware class.

    Attributes:
        middleware_id (str): Unique ID of the middleware
        middleware_name (str): Human-readable name of the middleware.
    """
    middleware_id: str = __name__
    middleware_name: str = "Dummy Middleware"
    __version__: str = 'undefined version'

    def process_message(self, message: EFBMsg) -> Optional[EFBMsg]:
        """
        Process a message with middleware

        Args:
            message (EFBMsg): Message object to process

        Returns:
            EFBMsg | None: Processed message or None if stopped.
        """
        return message

    def process_status(self, status: EFBStatus) -> Optional[EFBStatus]:
        """
        Process a status update with middleware

        Args:
            status (EFBStatus): Message object to process

        Returns:
            EFBMsg | None: Processed status or None if stopped.
        """
        return status
