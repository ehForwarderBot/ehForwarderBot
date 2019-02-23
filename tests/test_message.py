import unittest
from unittest import mock
from tempfile import NamedTemporaryFile

from ehforwarderbot import EFBMsg, EFBChat, ChatType, MsgType
from ehforwarderbot.message import EFBMsgLinkAttribute, EFBMsgLocationAttribute, EFBMsgStatusAttribute, EFBMsgCommands, \
    EFBMsgCommand

from .mocks.master import MockMasterChannel


class EFBMessageTest(unittest.TestCase):
    def setUp(self):
        self.channel = MockMasterChannel()
        self.chat = EFBChat(self.channel)
        self.chat.chat_name = "Chat 0"
        self.chat.chat_uid = "0"
        self.chat.chat_type = ChatType.User

    def test_basic_verify(self):
        with self.subTest("Valid text message"):
            msg = EFBMsg()
            msg.deliver_to = self.channel
            msg.author = self.chat
            msg.chat = self.chat
            msg.type = MsgType.Text
            msg.text = "Message"
            msg.verify()

        for i in (MsgType.Image, MsgType.Audio, MsgType.File, MsgType.Sticker):
            with self.subTest(f"Valid {i} message"), NamedTemporaryFile() as f:
                msg = EFBMsg()
                msg.deliver_to = self.channel
                msg.author = self.chat
                msg.chat = self.chat
                msg.type = i
                msg.file = f
                msg.filename = "test.bin"
                msg.path = f.name
                msg.mime = "application/octet-stream"
                msg.verify()

        with self.subTest("Missing deliver_to"), self.assertRaises(ValueError):
            msg = EFBMsg()
            msg.author = self.chat
            msg.chat = self.chat
            msg.type = MsgType.Text
            msg.text = "Message"
            msg.verify()

        with self.subTest("Missing author"), self.assertRaises(ValueError):
            msg = EFBMsg()
            msg.deliver_to = self.channel
            msg.chat = self.chat
            msg.type = MsgType.Text
            msg.text = "Message"
            msg.verify()

        with self.subTest("Missing chat"), self.assertRaises(ValueError):
            msg = EFBMsg()
            msg.deliver_to = self.channel
            msg.author = self.chat
            msg.type = MsgType.Text
            msg.text = "Message"
            msg.verify()

    def test_chain_verify(self):
        patch_chat_0 = self.chat.copy()
        patch_chat_1 = self.chat.copy()
        patch_chat_0.verify = mock.Mock()
        patch_chat_1.verify = mock.Mock()

        msg = EFBMsg()
        msg.deliver_to = self.channel

        with self.subTest("Different author and chat"):
            msg.author = patch_chat_0
            msg.chat = patch_chat_1
            msg.text = "Message"
            msg.verify()

            patch_chat_0.verify.assert_called_once()
            patch_chat_1.verify.assert_called_once()

        patch_chat_0.verify.reset_mock()

        with self.subTest("Same author and chat"):
            msg.author = patch_chat_0
            msg.chat = patch_chat_0
            msg.text = "Message"
            msg.verify()

            patch_chat_0.verify.assert_called_once()

        with self.subTest("Link message"):
            msg.type = MsgType.Link
            msg.attributes = EFBMsgLinkAttribute(title='Title', url='URL')
            msg.attributes.verify = mock.Mock()
            msg.verify()

            msg.attributes.verify.assert_called_once()

        with self.subTest("Location message"):
            msg.type = MsgType.Location
            msg.attributes = EFBMsgLocationAttribute(latitude=0.0, longitude=0.0)
            msg.attributes.verify = mock.Mock()
            msg.verify()

            msg.attributes.verify.assert_called_once()

        with self.subTest("Status message"):
            msg.type = MsgType.Status
            msg.attributes = EFBMsgStatusAttribute(status_type=EFBMsgStatusAttribute.Types.TYPING)
            msg.attributes.verify = mock.Mock()
            msg.verify()

            msg.attributes.verify.assert_called_once()

        with self.subTest("Message Command"):
            msg.type = MsgType.Text
            msg.attributes = None
            msg.commands = EFBMsgCommands([
                EFBMsgCommand(name="Command 1", callable_name="command_1")
            ])

            msg.commands.commands[0].verify = mock.Mock()

            msg.verify()

            msg.commands.commands[0].verify.assert_called_once()
