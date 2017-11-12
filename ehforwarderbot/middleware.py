from abc import ABC, abstractmethod
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

    @staticmethod
    def process_message(message: EFBMsg) -> Optional[EFBMsg]:
        """
        Process a message with middleware

        Args:
            message (EFBMsg): Message object to process

        Returns:
            EFBMsg | None: Processed message or None if stopped.
        """
        return message

    @staticmethod
    def process_status(status: EFBStatus) -> Optional[EFBStatus]:
        """
        Process a status update with middleware

        Args:
            status (EFBStatus): Message object to process

        Returns:
            EFBMsg | None: Processed status or None if stopped.
        """
        return status
