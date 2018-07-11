import unittest

from ehforwarderbot import EFBChat, ChatType

from .mocks.master import MockMasterChannel


class ChannelLoadingTest(unittest.TestCase):
    def setUp(self):
        pass

    def test_generate_with_channel(self):
        channel = MockMasterChannel()
        chat = EFBChat(channel)
        self.assertEqual(chat.channel_id, channel.channel_id)
        self.assertEqual(chat.channel_name, channel.channel_name)
        self.assertEqual(chat.channel_emoji, channel.channel_emoji)

    def test_is_system(self):
        chat = EFBChat().system()
        self.assertTrue(chat.is_system)

    def test_is_self(self):
        chat = EFBChat().self()
        self.assertTrue(chat.is_self)

    def test_normal_chat(self):
        chat = EFBChat()
        self.assertFalse(chat.is_self)
        self.assertFalse(chat.is_system)

    def test_copy(self):
        channel = MockMasterChannel()
        chat = EFBChat(channel)
        chat.chat_uid = "00001"
        chat.chat_name = "Chat"
        chat.chat_alias = "chaT"
        chat.chat_type = ChatType.User
        copy = chat.copy()
        self.assertEqual(chat, copy)
        self.assertIsNot(chat, copy)

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

        with self.subTest("Missing name"):
            chat = EFBChat(channel)
            chat.chat_uid = "00001"
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
