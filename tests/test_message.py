import pickle
from tempfile import NamedTemporaryFile
from unittest import mock

import pytest

from ehforwarderbot import EFBMsg, EFBChat, MsgType, coordinator
from ehforwarderbot.message import EFBMsgLinkAttribute, EFBMsgLocationAttribute, EFBMsgStatusAttribute, EFBMsgCommands, \
    EFBMsgCommand, EFBMsgSubstitutions


@pytest.fixture(scope="module")
def chat(slave_channel):
    chat = slave_channel.alice.copy()
    return chat


media_types = (MsgType.Image, MsgType.Audio, MsgType.File, MsgType.Sticker)


def test_verify_text_msg(chat):
    msg = EFBMsg()
    msg.deliver_to = coordinator.master
    msg.author = chat
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    msg.verify()


@pytest.mark.parametrize("media_type", media_types, ids=str)
def test_verify_media_msg(chat, master_channel, media_type):
    with NamedTemporaryFile() as f:
        msg = EFBMsg()
        msg.deliver_to = master_channel
        msg.author = chat
        msg.chat = chat
        msg.type = media_type
        msg.file = f
        msg.filename = "test.bin"
        msg.path = f.name
        msg.mime = "application/octet-stream"
        msg.verify()


def test_verify_missing_deliver_to(chat):
    msg = EFBMsg()
    msg.author = chat
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    with pytest.raises(ValueError):
        msg.verify()


def test_verify_missing_author(chat, master_channel):
    msg = EFBMsg()
    msg.deliver_to = master_channel
    msg.chat = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    with pytest.raises(ValueError):
        msg.verify()


def test_verify_missing_chat(chat):
    msg = EFBMsg()
    msg.deliver_to = coordinator.master
    msg.author = chat
    msg.type = MsgType.Text
    msg.text = "Message"
    with pytest.raises(ValueError):
        msg.verify()


@pytest.fixture()
def patch_chat_0(slave_channel):
    mocked_chat = slave_channel.alice.copy()
    mocked_chat.verify = mock.Mock()
    return mocked_chat


@pytest.fixture()
def patch_chat_1(slave_channel):
    mocked_chat = EFBChat(slave_channel).self()
    mocked_chat.verify = mock.Mock()
    return mocked_chat


def test_verify_different_author_and_chat(patch_chat_0, patch_chat_1, master_channel):
    msg = EFBMsg()
    msg.deliver_to = master_channel

    msg.author = patch_chat_0
    msg.chat = patch_chat_1
    msg.text = "Message"
    msg.verify()

    patch_chat_0.verify.assert_called_once()
    patch_chat_1.verify.assert_called_once()


def test_verify_same_author_and_chat(patch_chat_0, master_channel):
    msg = EFBMsg()
    msg.deliver_to = master_channel

    msg.author = patch_chat_0
    msg.chat = patch_chat_0
    msg.text = "Message"
    msg.verify()

    patch_chat_0.verify.assert_called_once()


@pytest.fixture()
def base_message(chat, master_channel):
    msg = EFBMsg()
    msg.deliver_to = master_channel

    msg.author = chat
    msg.chat = chat
    msg.text = "Message"
    msg.uid = "0"

    return msg


def test_verify_link_message(base_message):
    msg = base_message

    msg.type = MsgType.Link
    msg.attributes = EFBMsgLinkAttribute(title='Title', url='URL')
    msg.verify()

    with pytest.raises(ValueError) as exec_info:
        msg.attributes = EFBMsgLinkAttribute(title="Title")
    assert "URL" in exec_info.value.args[0]


def test_verify_location_message(base_message):
    msg = base_message

    msg.type = MsgType.Location
    msg.attributes = EFBMsgLocationAttribute(latitude=0.0, longitude=0.0)
    msg.verify()

    with pytest.raises(ValueError) as exec_info:
        msg.attributes = EFBMsgLocationAttribute(latitude='0.0', longitude=1.0)
        msg.verify()
    assert 'Latitude' in exec_info.value.args[0]

    with pytest.raises(ValueError) as exec_info:
        msg.attributes = EFBMsgLocationAttribute(latitude=1.0, longitude=10)
        msg.verify()
    assert 'Longitude' in exec_info.value.args[0]


def test_verify_status_message(base_message):
    msg = base_message

    msg.type = MsgType.Status
    msg.attributes = EFBMsgStatusAttribute(status_type=EFBMsgStatusAttribute.Types.TYPING)
    msg.verify()

    with pytest.raises(ValueError):
        EFBMsgStatusAttribute(status_type=EFBMsgStatusAttribute.Types.UPLOADING_FILE, timeout=-1)


def test_verify_message_command(base_message):
    msg = base_message

    msg.type = MsgType.Text
    command = EFBMsgCommand(name="Command 1", callable_name="command_1")

    msg.commands = EFBMsgCommands([command])
    msg.verify()

    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        EFBMsgCommand("name", "callable_name", args="args", kwargs="kwargs")  # type: ignore


def test_substitution(base_message, chat):
    base_message.substitutions = EFBMsgSubstitutions({(0, 3): chat})
    base_message.verify()

    with pytest.raises(TypeError):
        EFBMsgSubstitutions([chat])

    with pytest.raises(TypeError):
        EFBMsgSubstitutions({(1, 2, 3): chat})

    with pytest.raises(TypeError):
        EFBMsgSubstitutions({(1, 2, 3): chat.chat_uid})

    with pytest.raises(TypeError):
        EFBMsgSubstitutions({(2, 1): chat})

    with pytest.raises(ValueError):
        EFBMsgSubstitutions({(1, 3): chat, (2, 4): chat})


def test_pickle_minimum_text_message(base_message):
    msg = base_message
    msg_dup = pickle.loads(pickle.dumps(msg))
    for i in ("deliver_to", "author", "chat", "type", "text", "uid"):
        assert getattr(msg, i) == getattr(msg_dup, i)


@pytest.mark.parametrize("media_type", media_types, ids=str)
def test_pickle_media_message(media_type, base_message):
    with NamedTemporaryFile() as f:
        msg = base_message
        msg.type = media_type
        msg.file = f
        msg.filename = "test.bin"
        msg.path = f.name
        msg.mime = "application/octet-stream"
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
