import pickle

import pytest

from ehforwarderbot import Message
from ehforwarderbot.status import ChatUpdates, MemberUpdates, MessageRemoval, ReactToMessage, \
    MessageReactionsUpdate


def test_pickle_chat_updates(slave_channel):
    chat_update = ChatUpdates(
        channel=slave_channel,
        new_chats=["1", "2"],
        removed_chats=["3", "4"],
        modified_chats=["5", "6"]
    )
    chat_update_dup = pickle.loads(pickle.dumps(chat_update))

    for i in ("channel", "new_chats", "removed_chats", "modified_chats", "destination_channel"):
        assert getattr(chat_update, i) == getattr(chat_update_dup, i)


def test_pickle_member_updates(slave_channel):
    member_updates = MemberUpdates(
        channel=slave_channel,
        chat_id="chat_id",
        new_members=["1", "2"],
        removed_members=["3", "4"],
        modified_members=["5", "6"]
    )
    member_updates_dup = pickle.loads(pickle.dumps(member_updates))

    for i in ("channel", "chat_id", "new_members", "removed_members", "modified_members", "destination_channel"):
        assert getattr(member_updates, i) == getattr(member_updates_dup, i)


def test_pickle_message_removal(slave_channel, master_channel):
    msg = Message()
    msg.chat = slave_channel.alice
    msg.uid = "uid"
    msg_removal = MessageRemoval(
        source_channel=master_channel,
        destination_channel=slave_channel,
        message=msg
    )
    msg_removal_dup = pickle.loads(pickle.dumps(msg_removal))

    # Assume Message is picklable
    for i in ("source_channel", "destination_channel"):
        assert getattr(msg_removal, i) == getattr(msg_removal_dup, i)


def test_verify_react_to_message(slave_channel):
    ReactToMessage(slave_channel.alice, "message_id", ":)")

    with pytest.raises(AssertionError):
        ReactToMessage(None, "message_id", ":)")

    with pytest.raises(AssertionError):
        ReactToMessage(slave_channel.alice, "", ":)")


def test_pickle_react_to_message(slave_channel):
    status = ReactToMessage(slave_channel.alice, "message_id", ":)")
    d_status = pickle.loads(pickle.dumps(status))
    assert status.chat == d_status.chat
    assert status.msg_id == d_status.msg_id
    assert status.reaction == d_status.reaction


def test_verify_reactions_update(slave_channel):
    MessageReactionsUpdate(slave_channel.alice, "message_id", {
        ":)": [slave_channel.alice.other, slave_channel.bob.other]
    })

    with pytest.raises(AssertionError):
        MessageReactionsUpdate(None, "message_id", {
            ":)": [slave_channel.alice.other, slave_channel.bob.other]
        })

    with pytest.raises(AssertionError):
        MessageReactionsUpdate(slave_channel.alice, None, {
            ":)": [slave_channel.alice.other, slave_channel.bob.other]
        })

    with pytest.raises(AssertionError):
        MessageReactionsUpdate(slave_channel.alice, "message_id", {
            ":)": [slave_channel.alice.other, slave_channel.wonderland]
        })


def test_pickle_reactions_update(slave_channel):
    status = MessageReactionsUpdate(slave_channel.alice, "message_id", {
            ":)": [slave_channel.alice.other, slave_channel.bob.other]
        })
    d_status = pickle.loads(pickle.dumps(status))
    assert status.chat == d_status.chat
    assert status.msg_id == d_status.msg_id
    assert status.reactions == d_status.reactions
