import pickle

import pytest
from typing import Type

from ehforwarderbot import Chat
from ehforwarderbot.chat import PrivateChat, SelfChatMember, SystemChat, GroupChat, ChatMember, SystemChatMember


def test_generate_with_channel(slave_channel):
    chat = PrivateChat(channel=slave_channel, uid="chat_id")
    assert chat.module_id == slave_channel.channel_id
    assert chat.module_name == slave_channel.channel_name
    assert chat.channel_emoji == slave_channel.channel_emoji


def test_generate_with_middleware(middleware):
    chat = PrivateChat(middleware=middleware, uid="chat_id")
    assert chat.module_id == middleware.middleware_id
    assert chat.module_name == middleware.middleware_name


def test_copy(slave_channel):
    chat = PrivateChat(
        channel=slave_channel,
        uid="00001",
        name="Chat",
        alias="chaT"
    )
    copy = chat.copy()
    assert chat == copy
    assert chat is not copy


def test_verify_valid_chat(slave_channel):
    chat = PrivateChat(
        channel=slave_channel,
        uid="00001",
        name="Chat",
        alias="chaT"
    )
    chat.verify()


def test_verify_valid_chat_middleware(middleware):
    chat = PrivateChat(
        middleware=middleware,
        uid="00001",
        name="Chat",
        alias="chaT"
    )
    chat.verify()


def test_verify_missing_uid(slave_channel):
    with pytest.raises(AssertionError):
        chat = PrivateChat(
            channel=slave_channel,
            name="Chat")
        chat.verify()


def test_pickle(slave_channel):
    chat = PrivateChat(
        channel=slave_channel,
        uid="00001",
        name="Chat",
        alias="chaT"
    )
    chat_dup = pickle.loads(pickle.dumps(chat))
    for attr in ("module_name", "module_id", "channel_emoji", "name",
                 "alias", "uid"):
        assert getattr(chat, attr) == getattr(chat_dup, attr)


def test_properties(slave_channel):
    chat = PrivateChat(
        channel=slave_channel,
        uid="__id__",
        name="__name__"
    )
    assert chat.display_name == chat.name
    assert chat.long_name == chat.name
    chat.alias = "__alias__"
    assert chat.display_name == chat.alias
    assert chat.name in chat.long_name
    assert chat.alias in chat.long_name


@pytest.mark.parametrize("constructor", [PrivateChat, SystemChat, GroupChat])
def test_with_self(slave_channel, constructor: Type[Chat]):
    with_self = constructor(channel=slave_channel, name="__name__", uid="__id__")
    assert with_self.self
    assert with_self.self in with_self.members
    without_self = constructor(channel=slave_channel, name="__name__", uid="__id__", with_self=False)
    assert without_self.self is None
    assert not any(isinstance(i, SelfChatMember) for i in without_self.members)


def test_private_other(slave_channel):
    chat = PrivateChat(channel=slave_channel, name="__name__", alias="__alias__", uid="__id__")
    assert isinstance(chat.other, ChatMember)
    assert not isinstance(chat.other, SelfChatMember)
    assert not isinstance(chat.other, SystemChatMember)
    assert chat.other in chat.members
    assert chat.name == chat.other.name
    assert chat.alias == chat.other.alias
    assert chat.uid == chat.other.uid


def test_system_other(slave_channel):
    chat = SystemChat(channel=slave_channel, name="__name__", alias="__alias__", uid="__id__")
    assert isinstance(chat.other, SystemChatMember)
    assert chat.other in chat.members
    assert chat.name == chat.other.name
    assert chat.alias == chat.other.alias
    assert chat.uid == chat.other.uid


def test_add_member(slave_channel):
    chat = GroupChat(channel=slave_channel, name="__name__", alias="__alias__", uid="__id__")
    member = chat.add_member(name="__member_name__", uid="__member_id__")
    assert isinstance(member, ChatMember)
    assert not isinstance(member, SelfChatMember)
    assert member.name == "__member_name__"
    assert member.uid == "__member_id__"
    assert member.chat is chat
    assert member in chat.members


def test_add_system_member(slave_channel):
    chat = GroupChat(channel=slave_channel, name="__name__", alias="__alias__", uid="__id__")
    member = chat.add_system_member(name="__member_name__", uid="__member_id__")
    assert isinstance(member, SystemChatMember)
    assert member.name == "__member_name__"
    assert member.uid == "__member_id__"
    assert member.chat is chat
    assert member in chat.members
