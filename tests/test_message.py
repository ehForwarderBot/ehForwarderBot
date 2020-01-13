import pickle
from tempfile import NamedTemporaryFile
from unittest import mock

import pytest

from ehforwarderbot import Message, Chat, MsgType, coordinator
from ehforwarderbot.chat import PrivateChat
from ehforwarderbot.message import LinkAttribute, LocationAttribute, StatusAttribute, MessageCommands, \
    MessageCommand, Substitutions


@pytest.fixture(scope="module")
def chat(slave_channel) -> PrivateChat:
    chat = slave_channel.alice.copy()
    return chat


media_types = (MsgType.Image, MsgType.Audio, MsgType.File, MsgType.Sticker)


def test_verify_text_msg(chat):
    msg = Message(
        deliver_to=coordinator.master,
        author=chat.other,
        chat=chat,
        type=MsgType.Text,
        text="Message",
    )
    msg.verify()


@pytest.mark.parametrize("media_type", media_types, ids=str)
def test_verify_media_msg(chat, master_channel, media_type):
    with NamedTemporaryFile() as f:
        msg = Message(
            deliver_to=master_channel,
            author=chat.other,
            chat=chat,
            type=media_type,
            file=f,
            filename="test.bin",
            path=f.name,
            mime="application/octet-stream",
        )
        msg.verify()


def test_verify_missing_deliver_to(chat):
    msg = Message(
        author=chat.other,
        chat=chat,
        type=MsgType.Text,
        text="Message",
    )
    with pytest.raises(AssertionError):
        msg.verify()


def test_verify_missing_author(chat, master_channel):
    with pytest.raises(AssertionError):
        msg = Message(
            deliver_to=master_channel,
            chat=chat,
            type=MsgType.Text,
            text="Message",
        )
        msg.verify()


def test_verify_missing_chat(chat):
    with pytest.raises(AssertionError):
        msg = Message(
            deliver_to=coordinator.master,
            author=chat.other,
            type=MsgType.Text,
            text="Message",
        )
        msg.verify()


@pytest.fixture()
def patch_chat(slave_channel) -> PrivateChat:
    mocked_chat = slave_channel.alice.copy()
    mocked_chat.verify = mock.Mock()
    return mocked_chat


@pytest.fixture()
def patch_chat_member(patch_chat):
    mocked_chat = patch_chat.self.copy()
    mocked_chat.verify = mock.Mock()
    return mocked_chat


def test_verify_different_author_and_chat(patch_chat, patch_chat_member, master_channel):
    msg = Message(
        chat=patch_chat,
        author=patch_chat_member,
        text="Message",
        deliver_to=master_channel
    )
    msg.verify()

    patch_chat.verify.assert_called_once()
    patch_chat_member.verify.assert_called_once()


@pytest.fixture()
def base_message(chat, master_channel):
    msg = Message(
        deliver_to=master_channel,
        author=chat.other,
        chat=chat,
        text="Message",
        uid="0",
    )
    return msg


def test_verify_link_message(base_message):
    msg = base_message

    msg.type = MsgType.Link
    msg.attributes = LinkAttribute(title='Title', url='URL')
    msg.verify()

    with pytest.raises(AssertionError) as exec_info:
        msg.attributes = LinkAttribute(title="Title")
    assert "URL" in exec_info.value.args[0]


def test_verify_location_message(base_message):
    msg = base_message

    msg.type = MsgType.Location
    msg.attributes = LocationAttribute(latitude=0.0, longitude=0.0)
    msg.verify()

    with pytest.raises(AssertionError) as exec_info:
        msg.attributes = LocationAttribute(latitude='0.0', longitude=1.0)
        msg.verify()
    assert 'Latitude' in exec_info.value.args[0]

    with pytest.raises(AssertionError) as exec_info:
        msg.attributes = LocationAttribute(latitude=1.0, longitude=10)
        msg.verify()
    assert 'Longitude' in exec_info.value.args[0]


def test_verify_status_message(base_message):
    msg = base_message

    msg.type = MsgType.Status
    msg.attributes = StatusAttribute(status_type=StatusAttribute.Types.TYPING)
    msg.verify()

    with pytest.raises(AssertionError):
        StatusAttribute(status_type=StatusAttribute.Types.UPLOADING_FILE, timeout=-1)


def test_verify_message_command(base_message):
    msg = base_message

    msg.type = MsgType.Text
    command = MessageCommand(name="Command 1", callable_name="command_1")

    msg.commands = MessageCommands([command])
    msg.verify()

    with pytest.raises(ValueError):
        # noinspection PyTypeChecker
        MessageCommand("name", "callable_name", args="args", kwargs="kwargs")  # type: ignore


def test_substitution(base_message, chat):
    base_message.substitutions = Substitutions({(0, 3): chat})
    base_message.verify()

    with pytest.raises(AssertionError):
        Substitutions([chat])

    with pytest.raises(AssertionError):
        Substitutions({(1, 2, 3): chat})

    with pytest.raises(AssertionError):
        Substitutions({(1, 2, 3): chat.uid})

    with pytest.raises(AssertionError):
        Substitutions({(2, 1): chat})

    with pytest.raises(AssertionError):
        Substitutions({(1, 3): chat, (2, 4): chat})


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
    link = LinkAttribute(title="a", description="b", image="c", url="d")
    link_dup = pickle.loads(pickle.dumps(link))
    for attr in ("title", "description", "image", "url"):
        assert getattr(link, attr) == getattr(link_dup, attr)


def test_pickle_location_attribute():
    location = LocationAttribute(latitude=1.0, longitude=-1.0)
    location_dup = pickle.loads(pickle.dumps(location))
    for attr in ("latitude", "longitude"):
        assert getattr(location, attr) == getattr(location_dup, attr)


def test_pickle_commands_attribute():
    commands = MessageCommands([
        MessageCommand(name="Command 1", callable_name="command_1",
                       args=(1, 2, 3), kwargs={"four": 4, "five": 5}),
        MessageCommand(name="Command 2", callable_name="command_2",
                       args=("1", "2", "3"), kwargs={"four": "4", "five": "5"})
    ])
    commands_dup = pickle.loads(pickle.dumps(commands))
    for cmd in range(len(commands)):
        for attr in ("name", "callable_name", "args", "kwargs"):
            assert getattr(commands[cmd], attr) == \
                   getattr(commands_dup[cmd], attr)


def test_pickle_status():
    for t in StatusAttribute.Types:
        status = StatusAttribute(t, 1234)
        status_dup = pickle.loads(pickle.dumps(status))
        assert status.status_type == status_dup.status_type
        assert status.timeout == status_dup.timeout
