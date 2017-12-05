import threading
from typing import Set
from logging import getLogger

from ehforwarderbot import EFBChannel, EFBMsg, EFBStatus, ChannelType, MsgType


class MockMasterChannel(EFBChannel):

    channel_name: str = "Mock Master"
    channel_emoji: str = "➕"
    channel_id: str = "tests.mocks.master"
    channel_type: ChannelType = ChannelType.Master
    supported_message_types: Set[MsgType] = {MsgType.Text, MsgType.Audio}
    __version__: str = '0.0.1'

    # Slave-only methods
    get_chat = None
    get_chats = None
    get_chat_picture = None

    logger = getLogger("tests.mocks.master")

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

    # TODO: Send types of messages and statuses to slave channels
