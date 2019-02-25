import unittest

from ehforwarderbot import EFBChat, ChatType

from .mocks.master import MockMasterChannel
from .mocks.middleware import MockMiddleware


class ChatTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_generate_with_channel(self):
        channel = MockMasterChannel()
        chat = EFBChat(channel)
        assert chat.module_id == channel.channel_id
        assert chat.module_name == channel.channel_name
        assert chat.channel_emoji == channel.channel_emoji

    def test_generate_with_middleware(self):
        middleware = MockMiddleware()
        chat = EFBChat(middleware=middleware)
        assert chat.module_id == middleware.middleware_id
        assert chat.module_name == middleware.middleware_name

    def test_is_system(self):
        chat = EFBChat().system()
        assert chat.is_system

    def test_is_self(self):
        chat = EFBChat().self()
        assert chat.is_self

    def test_normal_chat(self):
        chat = EFBChat()
        assert not chat.is_self
        assert not chat.is_system

    def test_copy(self):
        channel = MockMasterChannel()
        chat = EFBChat(channel)
        chat.chat_uid = "00001"
        chat.chat_name = "Chat"
        chat.chat_alias = "chaT"
        chat.chat_type = ChatType.User
        copy = chat.copy()
        assert chat == copy
        assert chat is not copy

    def test_verify(self):
        channel = MockMasterChannel()

        with self.subTest("Valid chat"):
            chat = EFBChat(channel)
            chat.chat_uid = "00001"
            chat.chat_name = "Chat"
            chat.chat_alias = "chaT"
            chat.chat_type = ChatType.User
            chat.verify()

        with self.subTest("Missing UID"):
            chat = EFBChat(channel)
            chat.chat_name = "Chat"
            chat.chat_type = ChatType.User
            with self.assertRaises(ValueError):
                chat.verify()

        with self.subTest("Wrong chat type"):
            chat = EFBChat(channel)
            chat.chat_uid = "00001"
            chat.chat_name = "Chat"
            chat.chat_type = "user"
            with self.assertRaises(ValueError):
                chat.verify()
