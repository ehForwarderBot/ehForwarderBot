import threading
from typing import Set, Optional, List
from logging import getLogger

from ehforwarderbot import EFBChannel, EFBMsg, EFBStatus, ChannelType, MsgType, EFBChat, ChatType
from ehforwarderbot.exceptions import EFBChatNotFound
from ehforwarderbot.utils import extra


class MockSlaveChannel(EFBChannel):

    channel_name: str = "Mock Slave"
    channel_emoji: str = "➖"
    channel_id: str = "tests.mocks.slave.MockSlaveChannel"
    channel_type: ChannelType = ChannelType.Slave
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
        alice = EFBChat(self)
        alice.chat_name = "Alice"
        alice.chat_uid = "alice"
        alice.chat_type = ChatType.User
        bob = EFBChat(self)
        bob.chat_name = "Bob"
        bob.chat_alias = "Little bobby"
        bob.chat_uid = "bob"
        bob.chat_type = ChatType.User
        carol = EFBChat(self)
        carol.chat_name = "Carol"
        carol.chat_uid = "carol"
        carol.chat_type = ChatType.User
        dave = EFBChat(self)
        dave.chat_name = "デブ"  # Nah, that's a joke
        dave.chat_uid = "dave"
        dave.chat_type = ChatType.User
        wonderland = EFBChat(self)
        wonderland.chat_name = "Wonderland"
        wonderland.chat_uid = "wonderland001"
        wonderland.chat_type = ChatType.Group
        wonderland.members = [bob.copy(), carol.copy(), dave.copy()]
        for i in wonderland.members:
            i.group = wonderland
        self.chats: List[EFBChat] = [alice, bob, wonderland]

    def poll(self):
        self.polling.wait()

    def send_status(self, status: EFBStatus):
        self.logger.debug("Received status: %r", status)

    def send_message(self, msg: EFBMsg) -> EFBMsg:
        self.logger.debug("Received message: %r", msg)
        return msg

    def stop_polling(self):
        self.polling.set()

    def get_chat(self, chat_uid: str, member_uid: Optional[str] = None) -> EFBChat:
        for i in self.chats:
            if chat_uid == i.chat_uid:
                if member_uid:
                    if i.chat_type == ChatType.Group:
                        for j in i.members:
                            if j.chat_uid == member_uid:
                                return j
                        raise EFBChatNotFound()
                    else:
                        raise EFBChatNotFound()
                return i
        raise EFBChatNotFound()

    def get_chats(self) -> List[EFBChat]:
        return self.chats.copy()

    def get_chat_picture(self, chat: EFBChat):
        if chat.chat_uid in self.__picture_dict:
            return open('tests/mocks/' + self.__picture_dict[chat.chat_uid], 'rb')

    @extra(name="Echo",
           desc="Echo back the input.\n"
                "Usage:\n"
                "    {function_name} text")
    def echo(self, args):
        return args

    def get_message_by_id(self, msg_id: str) -> Optional['EFBMsg']:
        pass

    # TODO: Send types of messages and statuses to slave channels
