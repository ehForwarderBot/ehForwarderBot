import logging
from typing import Optional

from ehforwarderbot import EFBMiddleware, EFBMsg, EFBStatus, MsgType


class MockMiddleware(EFBMiddleware):
    """
    Attributes:
        mode:
            * Default "log": Logging only
            * "append_text": Append to the text attribute of the message
            * "interrupt": Interrupt and stop all messages from delivering.
            * "interrupt_non_text": Interrupt only non-text messages.
    """

    middleware_id: str = "tests.mocks.middleware.MockMiddleware"
    middleware_name: str = "Mock Middleware"
    __version__: str = '0.0.1a'

    logger = logging.getLogger(middleware_id)

    def __init__(self, instance_id: str = None, mode: str="log"):
        super().__init__(instance_id=instance_id)
        self.mode: str = mode

    def process_message(self, message: EFBMsg) -> Optional[EFBMsg]:
        self.logger.debug("Processing Message %s", message)
        if self.mode == "append_text":
            message.text += " (Processed by " + self.middleware_id + ")"
        elif self.mode == "interrupt":
            return
        elif self.mode == "interrupt_non_text" and message.type != MsgType.Text:
            return
        return message

    def process_status(self, status: EFBStatus) -> Optional[EFBStatus]:
        if self.mode == "interrupt":
            return
        return status
