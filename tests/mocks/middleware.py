import logging
from typing import Optional

from ehforwarderbot import Middleware, Message, Status, MsgType
from ehforwarderbot.types import ModuleID, InstanceID
from ehforwarderbot.utils import extra


class MockMiddleware(Middleware):
    """
    Attributes:
        mode:
            * Default "log": Logging only
            * "append_text": Append to the text attribute of the message
            * "interrupt": Interrupt and stop all messages from delivering.
            * "interrupt_non_text": Interrupt only non-text messages.
    """

    middleware_id: ModuleID = ModuleID("tests.mocks.middleware.MockMiddleware")
    middleware_name: str = "Mock Middleware"
    __version__: str = '0.0.1'

    logger = logging.getLogger(middleware_id)

    def __init__(self, instance_id: Optional[InstanceID] = None, mode: str = "log"):
        super().__init__(instance_id=instance_id)
        self.mode: str = mode

    def process_message(self, message: Message) -> Optional[Message]:
        self.logger.debug("Processing Message %s", message)
        if self.mode == "append_text":
            message.text += " (Processed by " + self.middleware_id + ")"
        elif self.mode == "interrupt":
            return None
        elif self.mode == "interrupt_non_text" and message.type != MsgType.Text:
            return None
        return message

    def process_status(self, status: Status) -> Optional[Status]:
        if self.mode == "interrupt":
            return None
        return status

    @extra(name="Echo",
           desc="Echo back the input.\n"
                "Usage:\n"
                "    {function_name} text")
    def echo(self, args):
        return args
