import threading
from typing import Set, Optional, IO, List
from logging import getLogger

from ehforwarderbot import EFBChannel, EFBMsg, EFBStatus, ChannelType, MsgType, coordinator, EFBChat
from ehforwarderbot.message import EFBMsgLinkAttribute, EFBMsgLocationAttribute
from ehforwarderbot.status import EFBMessageRemoval
from ehforwarderbot.types import ModuleID, MessageID
from ehforwarderbot.types import ChatID


class MockMasterChannel(EFBChannel):

    channel_name: str = "Mock Master"
    channel_emoji: str = "➕"
    channel_id: ModuleID = ModuleID("tests.mocks.master.MockMasterChannel")
    channel_type: ChannelType = ChannelType.Master
    supported_message_types: Set[MsgType] = {MsgType.Text, MsgType.Link}
    __version__: str = '0.0.1'

    logger = getLogger(channel_id)

    polling = threading.Event()

    def poll(self):
        self.polling.wait()

    def send_status(self, status: EFBStatus):
        self.logger.debug("Received status: %r", status)

    def send_message(self, msg: EFBMsg) -> EFBMsg:
        self.logger.debug("Received message: %r", msg)
        return msg

    def stop_polling(self):
        self.polling.set()

    def send_text_msg(self):
        slave = next(iter(coordinator.slaves.values()))
        wonderland = slave.get_chat('wonderland001')
        msg = EFBMsg()
        msg.deliver_to = slave
        msg.chat = wonderland
        msg.author = EFBChat(self).self()
        msg.type = MsgType.Text
        msg.text = "Hello, world."
        return coordinator.send_message(msg)

    def send_link_msg(self):
        slave = next(iter(coordinator.slaves.values()))
        alice = slave.get_chat('alice')
        msg = EFBMsg()
        msg.deliver_to = slave
        msg.chat = alice
        msg.author = EFBChat(self).self()
        msg.type = MsgType.Link
        msg.text = "Check it out."
        msg.attributes = EFBMsgLinkAttribute(
            title="Example",
            url="https://example.com"
        )
        return coordinator.send_message(msg)

    def send_location_msg(self):
        slave = next(iter(coordinator.slaves.values()))
        alice = slave.get_chat('alice')
        msg = EFBMsg()
        msg.deliver_to = slave
        msg.chat = alice
        msg.author = EFBChat(self).self()
        msg.type = MsgType.Location
        msg.text = "I'm not here."
        msg.attributes = EFBMsgLocationAttribute(latitude=0.1, longitude=1.0)
        return coordinator.send_message(msg)

    def send_message_recall_status(self):
        slave = next(iter(coordinator.slaves.values()))
        alice = slave.get_chat('alice')
        msg = EFBMsg()
        msg.deliver_to = slave
        msg.chat = alice
        msg.author = EFBChat(self).self()
        msg.uid = "1"
        status = EFBMessageRemoval(self, slave, msg)
        return coordinator.send_status(status)

    def get_message_by_id(self, chat: EFBChat, msg_id: MessageID) -> Optional['EFBMsg']:
        pass

    def get_chats(self) -> List['EFBChat']:
        raise NotImplementedError()

    def get_chat(self, chat_uid: ChatID, member_uid: Optional[ChatID] = None) -> 'EFBChat':
        raise NotImplementedError()

    def get_chat_picture(self, chat: 'EFBChat') -> IO[bytes]:
        raise NotImplementedError()
