import pickle

from .base_class import setup

from ehforwarderbot import coordinator, EFBMsg
from ehforwarderbot.status import EFBChatUpdates, EFBMemberUpdates, EFBMessageRemoval

setup_module = setup


def test_pickle_chat_updates():
    chat_update = EFBChatUpdates(
        channel=next(iter(coordinator.slaves.values())),
        new_chats=["1", "2"],
        removed_chats=["3", "4"],
        modified_chats=["5", "6"]
    )
    chat_update_dup = pickle.loads(pickle.dumps(chat_update))

    for i in ("channel", "new_chats", "removed_chats", "modified_chats", "destination_channel"):
        assert getattr(chat_update, i) == getattr(chat_update_dup, i)


def test_pickle_member_updates():
    member_updates = EFBMemberUpdates(
        channel=next(iter(coordinator.slaves.values())),
        chat_id="chat_id",
        new_members=["1", "2"],
        removed_members=["3", "4"],
        modified_members=["5", "6"]
    )
    member_updates_dup = pickle.loads(pickle.dumps(member_updates))

    for i in ("channel", "chat_id", "new_members", "removed_members", "modified_members", "destination_channel"):
        assert getattr(member_updates, i) == getattr(member_updates_dup, i)


def test_pickle_message_removal():
    msg = EFBMsg()
    slave = next(iter(coordinator.slaves.values()))
    msg.chat = slave.get_chat("alice")
    msg.uid = "uid"
    msg_removal = EFBMessageRemoval(
        source_channel=coordinator.master,
        destination_channel=slave,
        message=msg
    )
    msg_removal_dup = pickle.loads(pickle.dumps(msg_removal))

    # Assume EFBMsg is picklable
    for i in ("source_channel", "destination_channel"):
        assert getattr(msg_removal, i) == getattr(msg_removal_dup, i)
