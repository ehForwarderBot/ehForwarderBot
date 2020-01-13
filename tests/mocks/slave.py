import threading
from logging import getLogger
from typing import Set, Optional, List

from ehforwarderbot import Message, Status, MsgType, Chat
from ehforwarderbot.channel import SlaveChannel
from ehforwarderbot.chat import PrivateChat, GroupChat
from ehforwarderbot.exceptions import EFBChatNotFound
from ehforwarderbot.types import ModuleID, MessageID
from ehforwarderbot.utils import extra


class MockSlaveChannel(SlaveChannel):
    channel_name: str = "Mock Slave"
    channel_emoji: str = "➖"
    channel_id: ModuleID = ModuleID("tests.mocks.slave.MockSlaveChannel")
    supported_message_types: Set[MsgType] = {MsgType.Text, MsgType.Link}
    __version__: str = '0.0.1'

    logger = getLogger(channel_id)

    polling = threading.Event()

    __picture_dict = {
        "alice": "A.png",
        "bob": "B.png",
        "carol": "C.png",
        "dave": "D.png",
        "wonderland001": "W.png"
    }

    def __init__(self, instance_id=None):
        super().__init__(instance_id)
        self.alice = PrivateChat(channel=self, name="Alice", uid="alice")
        self.bob = PrivateChat(channel=self, name="Bob", alias="Little bobby", uid="bob")

        self.wonderland = GroupChat(channel=self, name="Wonderland", uid="wonderland001")
        self.wonderland.add_member(name="bob", alias="Bob James", uid="bob")
        self.carol = self.wonderland.add_member(name="Carol", uid="carol")
        self.dave = self.wonderland.add_member(name="デブ", uid="dave")  # Nah, that's a joke

        self.chats: List[Chat] = [self.alice, self.bob, self.wonderland]

    def poll(self):
        self.polling.wait()

    def send_status(self, status: Status):
        self.logger.debug("Received status: %r", status)

    def send_message(self, msg: Message) -> Message:
        self.logger.debug("Received message: %r", msg)
        return msg

    def stop_polling(self):
        self.polling.set()

    def get_chat(self, chat_uid: str) -> Chat:
        for i in self.chats:
            if chat_uid == i.uid:
                return i
        raise EFBChatNotFound()

    def get_chats(self) -> List[Chat]:
        return self.chats.copy()

    def get_chat_picture(self, chat: Chat):
        if chat.uid in self.__picture_dict:
            return open('tests/mocks/' + self.__picture_dict[chat.uid], 'rb')

    def get_message_by_id(self, chat: Chat, msg_id: MessageID) -> Optional['Message']:
        pass

    @extra(name="Echo",
           desc="Echo back the input.\n"
                "Usage:\n"
                "    {function_name} text")
    def echo(self, args):
        return args

    @extra(name="Extra function A", desc="Do something A.\nUsage: {function_name}")
    def function_a(self):
        return f"Value of function A from {self.channel_id}."

    @extra(name="Extra function B", desc="Do something B.\nUsage: {function_name}")
    def function_b(self):
        return f"Value of function B from {self.channel_name}."

    # TODO: Send types of messages and statuses to slave channels
