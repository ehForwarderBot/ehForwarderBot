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
        coordinator (EFBCoordinator): The global EFB Coordinator.
    """
    @abstractmethod
    def __init__(self):
        """
        Initialize a middleware.
        """
        self.middleware_id: str = self.__name__
        self.middleware_name: str = "Dummy Middleware"

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
