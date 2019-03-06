from .base_class import setup

from ehforwarderbot import coordinator

from .mocks.master import MockMasterChannel
from .mocks.middleware import MockMiddleware

setup_module = setup


def test_append_text():
    master: MockMasterChannel = coordinator.master
    middleware: MockMiddleware = coordinator.middlewares[0]
    middleware.mode = "append_text"
    assert middleware.middleware_id in master.send_text_msg().text


def test_interrupt():
    master: MockMasterChannel = coordinator.master
    middleware: MockMiddleware = coordinator.middlewares[0]
    middleware.mode = "interrupt"
    assert master.send_text_msg() is None


def test_interrupt_non_text():
    master: MockMasterChannel = coordinator.master
    middleware: MockMiddleware = coordinator.middlewares[0]
    middleware.mode = "interrupt_non_text"
    assert master.send_text_msg() is not None
    assert master.send_link_msg() is None


def test_interrupt_status():
    master: MockMasterChannel = coordinator.master
    middleware: MockMiddleware = coordinator.middlewares[0]
    middleware.mode = "interrupt"
    assert master.send_message_recall_status() is None
