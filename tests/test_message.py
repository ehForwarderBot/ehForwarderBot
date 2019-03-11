import unittest
import pickle
from unittest import mock
from tempfile import NamedTemporaryFile

import pytest

from ehforwarderbot import EFBMsg, EFBChat, ChatType, MsgType, coordinator
from ehforwarderbot.message import EFBMsgLinkAttribute, EFBMsgLocationAttribute, EFBMsgStatusAttribute, EFBMsgCommands, \
    EFBMsgCommand

from .mocks.master import MockMasterChannel

coordinator.master = MockMasterChannel()
chat = EFBChat(channel=coordinator.master)
chat.chat_name = "Chat 0"
chat.chat_uid = "0"
chat.chat_type = ChatType.User

media_types = (MsgType.Image, MsgType.Audio, MsgType.File, MsgType.Sticker)


def test_verify_text_msg():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master
    msg.author = chat
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    msg.verify()


@pytest.mark.parametrize("media_type", media_types, ids=str)
def test_verify_media_msg(media_type):
    with NamedTemporaryFile() as f:
        msg = EFBMsg()
        msg.deliver_to = coordinator.master
        msg.author = chat
        msg.chat = chat
        msg.type = media_type
        msg.file = f
        msg.filename = "test.bin"
        msg.path = f.name
        msg.mime = "application/octet-stream"
        msg.verify()


def test_verify_missing_deliver_to():
    msg = EFBMsg()
    msg.author = chat
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    with pytest.raises(ValueError):
        msg.verify()


def test_verify_missing_author():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    with pytest.raises(ValueError):
        msg.verify()


def test_verify_missing_chat():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master
    msg.author = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    with pytest.raises(ValueError):
        msg.verify()


patch_chat_0 = chat.copy()
patch_chat_1 = chat.copy()
patch_chat_0.verify = mock.Mock()
patch_chat_1.verify = mock.Mock()


def test_verify_different_author_and_chat():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master

    msg.author = patch_chat_0
    msg.chat = patch_chat_1
    msg.text = "Message"
    msg.verify()

    patch_chat_0.verify.assert_called_once()
    patch_chat_1.verify.assert_called_once()

    patch_chat_0.verify.reset_mock()
    patch_chat_1.verify.reset_mock()


def test_verify_same_author_and_chat():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master

    msg.author = patch_chat_0
    msg.chat = patch_chat_0
    msg.text = "Message"
    msg.verify()

    patch_chat_0.verify.assert_called_once()


def test_verify_link_message():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master

    msg.author = patch_chat_0
    msg.chat = patch_chat_1
    msg.text = "Message"
    msg.verify()

    msg.type = MsgType.Link
    msg.attributes = EFBMsgLinkAttribute(title='Title', url='URL')
    msg.attributes.verify = mock.Mock()
    msg.verify()

    msg.attributes.verify.assert_called_once()


def test_verify_location_message():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master

    msg.author = patch_chat_0
    msg.chat = patch_chat_1
    msg.text = "Message"
    msg.verify()

    msg.type = MsgType.Location
    msg.attributes = EFBMsgLocationAttribute(latitude=0.0, longitude=0.0)
    msg.attributes.verify = mock.Mock()
    msg.verify()

    msg.attributes.verify.assert_called_once()


def test_verify_status_message():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master

    msg.author = patch_chat_0
    msg.chat = patch_chat_1
    msg.text = "Message"
    msg.verify()

    msg.type = MsgType.Status
    msg.attributes = EFBMsgStatusAttribute(status_type=EFBMsgStatusAttribute.Types.TYPING)
    msg.attributes.verify = mock.Mock()
    msg.verify()

    msg.attributes.verify.assert_called_once()


def test_verify_message_command():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master

    msg.author = patch_chat_0
    msg.chat = patch_chat_1
    msg.text = "Message"
    msg.verify()

    msg.type = MsgType.Text
    msg.attributes = None
    msg.commands = EFBMsgCommands([
        EFBMsgCommand(name="Command 1", callable_name="command_1")
    ])

    msg.commands.commands[0].verify = mock.Mock()

    msg.verify()

    msg.commands.commands[0].verify.assert_called_once()


def test_pickle_minimum_text_message():
    msg = EFBMsg()
    msg.deliver_to = coordinator.master
    msg.author = chat
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    msg.uid = "message_id"
    msg_dup = pickle.loads(pickle.dumps(msg))
    for i in ("deliver_to", "author", "chat", "type", "text", "uid"):
        assert getattr(msg, i) == getattr(msg_dup, i)


@pytest.mark.parametrize("media_type", media_types, ids=str)
def test_pickle_media_message(media_type):
    with NamedTemporaryFile() as f:
        msg = EFBMsg()
        msg.deliver_to = coordinator.master
        msg.author = chat
        msg.chat = chat
        msg.type = media_type
        msg.file = f
        msg.filename = "test.bin"
        msg.path = f.name
        msg.mime = "application/octet-stream"
        msg.uid = "message_id"
        msg.verify()
        msg_dup = pickle.loads(pickle.dumps(msg))
        for attr in ("deliver_to", "author", "chat", "type", "chat", "filename", "path", "mime", "text", "uid"):
            assert getattr(msg, attr) == getattr(msg_dup, attr)


def test_pickle_link_attribute():
    link = EFBMsgLinkAttribute(title="a", description="b", image="c", url="d")
    link_dup = pickle.loads(pickle.dumps(link))
    for attr in ("title", "description", "image", "url"):
        assert getattr(link, attr) == getattr(link_dup, attr)


def test_pickle_location_attribute():
    location = EFBMsgLocationAttribute(latitude=1.0, longitude=-1.0)
    location_dup = pickle.loads(pickle.dumps(location))
    for attr in ("latitude", "longitude"):
        assert getattr(location, attr) == getattr(location_dup, attr)


def test_pickle_commands_attribute():
    commands = EFBMsgCommands([
        EFBMsgCommand(name="Command 1", callable_name="command_1",
                      args=(1, 2, 3), kwargs={"four": 4, "five": 5}),
        EFBMsgCommand(name="Command 2", callable_name="command_2",
                      args=("1", "2", "3"), kwargs={"four": "4", "five": "5"})
    ])
    commands_dup = pickle.loads(pickle.dumps(commands))
    for cmd in range(len(commands.commands)):
        for attr in ("name", "callable_name", "args", "kwargs"):
            assert getattr(commands.commands[cmd], attr) == \
                   getattr(commands_dup.commands[cmd], attr)


def test_pickle_status():
    for t in EFBMsgStatusAttribute.Types:
        status = EFBMsgStatusAttribute(t, 1234)
        status_dup = pickle.loads(pickle.dumps(status))
        assert status.status_type == status_dup.status_type
        assert status.timeout == status_dup.timeout
