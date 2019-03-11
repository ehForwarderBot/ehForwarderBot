import pickle

import pytest

from ehforwarderbot import EFBChat, ChatType

from .mocks.master import MockMasterChannel
from .mocks.middleware import MockMiddleware

channel = MockMasterChannel()


def test_generate_with_channel():
    chat = EFBChat(channel)
    assert chat.module_id == channel.channel_id
    assert chat.module_name == channel.channel_name
    assert chat.channel_emoji == channel.channel_emoji


def test_generate_with_middleware():
    middleware = MockMiddleware()
    chat = EFBChat(middleware=middleware)
    assert chat.module_id == middleware.middleware_id
    assert chat.module_name == middleware.middleware_name


def test_is_system():
    chat = EFBChat().system()
    assert chat.is_system


def test_is_self():
    chat = EFBChat().self()
    assert chat.is_self


def test_normal_chat():
    chat = EFBChat()
    assert not chat.is_self
    assert not chat.is_system


def test_copy():
    chat = EFBChat(channel)
    chat.chat_uid = "00001"
    chat.chat_name = "Chat"
    chat.chat_alias = "chaT"
    chat.chat_type = ChatType.User
    copy = chat.copy()
    assert chat == copy
    assert chat is not copy


def test_verify_valid_chat():
    chat = EFBChat(channel)
    chat.chat_uid = "00001"
    chat.chat_name = "Chat"
    chat.chat_alias = "chaT"
    chat.chat_type = ChatType.User
    chat.verify()


def test_verify_missing_uid():
    chat = EFBChat(channel)
    chat.chat_name = "Chat"
    chat.chat_type = ChatType.User
    with pytest.raises(ValueError):
        chat.verify()


def test_verify_wrong_chat_type():
    chat = EFBChat(channel)
    chat.chat_uid = "00001"
    chat.chat_name = "Chat"
    chat.chat_type = "user"
    with pytest.raises(ValueError):
        chat.verify()


def test_pickle():
    chat = EFBChat(channel)
    chat.chat_uid = "00001"
    chat.chat_name = "Chat"
    chat.chat_alias = "chaT"
    chat.chat_type = ChatType.User
    chat_dup = pickle.loads(pickle.dumps(chat))
    for attr in ("module_name", "module_id", "channel_emoji", "chat_name",
                 "chat_type", "chat_alias", "chat_uid", "is_chat"):
        assert getattr(chat, attr) == getattr(chat_dup, attr)
