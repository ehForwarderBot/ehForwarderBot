import threading
from logging import getLogger
from typing import Set, Optional, IO, List

from ehforwarderbot import Message, Status, MsgType, coordinator, Chat
from ehforwarderbot.channel import MasterChannel
from ehforwarderbot.message import LinkAttribute, LocationAttribute
from ehforwarderbot.status import MessageRemoval
from ehforwarderbot.types import ChatID
from ehforwarderbot.types import ModuleID, MessageID


class MockMasterChannel(MasterChannel):
    channel_name: str = "Mock Master"
    channel_emoji: str = "➕"
    channel_id: ModuleID = ModuleID("tests.mocks.master.MockMasterChannel")
    supported_message_types: Set[MsgType] = {MsgType.Text, MsgType.Link}
    __version__: str = '0.0.1'

    logger = getLogger(channel_id)

    polling = threading.Event()

    def poll(self):
        self.polling.wait()

    def send_status(self, status: Status):
        self.logger.debug("Received status: %r", status)

    def send_message(self, msg: Message) -> Message:
        self.logger.debug("Received message: %r", msg)
        return msg

    def stop_polling(self):
        self.polling.set()

    def send_text_msg(self):
        slave = next(iter(coordinator.slaves.values()))
        wonderland = slave.get_chat('wonderland001')
        msg = Message(
            deliver_to=slave,
            chat=wonderland,
            author=wonderland.self,
            type=MsgType.Text,
            text="Hello, world.",
        )
        return coordinator.send_message(msg)

    def send_link_msg(self):
        slave = next(iter(coordinator.slaves.values()))
        alice = slave.get_chat('alice')
        msg = Message(
            deliver_to=slave,
            chat=alice,
            author=alice.self,
            type=MsgType.Link,
            text="Check it out.",
            attributes=LinkAttribute(
                title="Example",
                url="https://example.com"
            )
        )
        return coordinator.send_message(msg)

    def send_location_msg(self):
        slave = next(iter(coordinator.slaves.values()))
        alice = slave.get_chat('alice')
        msg = Message(
            deliver_to=slave,
            chat=alice,
            author=alice.self,
            type=MsgType.Location,
            text="I'm not here.",
            attributes=LocationAttribute(latitude=0.1, longitude=1.0),
        )
        return coordinator.send_message(msg)

    def send_message_recall_status(self):
        slave = next(iter(coordinator.slaves.values()))
        alice = slave.get_chat('alice')
        msg = Message(
            deliver_to=slave,
            chat=alice,
            author=alice.self,
            uid="1"
        )
        status = MessageRemoval(self, slave, msg)
        return coordinator.send_status(status)

    def get_message_by_id(self, chat: Chat, msg_id: MessageID) -> Optional['Message']:
        pass
