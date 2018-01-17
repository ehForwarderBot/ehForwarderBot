from .base_test import StandardChannelTest

from ehforwarderbot import coordinator

from .mocks.master import MockMasterChannel
from .mocks.middleware import MockMiddleware


class MiddlewareTest(StandardChannelTest):
    def test_append_text(self):
        master: MockMasterChannel = coordinator.master
        middleware: MockMiddleware = coordinator.middlewares[0]
        middleware.mode = "append_text"
        self.assertIn(middleware.middleware_id, master.send_text_msg().text)

    def test_interrupt(self):
        master: MockMasterChannel = coordinator.master
        middleware: MockMiddleware = coordinator.middlewares[0]
        middleware.mode = "interrupt"
        self.assertIsNone(master.send_text_msg())

    def test_interrupt_non_text(self):
        master: MockMasterChannel = coordinator.master
        middleware: MockMiddleware = coordinator.middlewares[0]
        middleware.mode = "interrupt_non_text"
        self.assertIsNotNone(master.send_text_msg())
        self.assertIsNone(master.send_link_msg())

    def test_interrupt_status(self):
        master: MockMasterChannel = coordinator.master
        middleware: MockMiddleware = coordinator.middlewares[0]
        middleware.mode = "interrupt"
        self.assertIsNone(master.send_message_recall_status())
