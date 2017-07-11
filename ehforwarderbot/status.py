__all__ = ["EFBChatUpdates", "EFBMemberUpdates"]


class EFBStatus:
    def __init__(self):
        raise Exception("Do not use EFBStatus directly.")


class EFBChatUpdates(EFBStatus):
    """
    Inform the master channel on updates of slave chats.
        
    Attributes:
        channel_id (str): ID of the issuing channel.
        new_chats (list of str): Unique ID of new chats
        removed_chats (list of str): Unique ID of removed chats
        modified_chats (list of str): Unique ID of modified chats
    """
    def __init__(self, channel, new_chats=tuple(), removed_chats=tuple(), modified_chats=tuple()):
        """
        Args:
            channel (ehforwarderbot.EFBChannel): Slave channel that issues the update
            new_chats (list of str): Unique ID of new chats
            removed_chats (list of str): Unique ID of removed chats
            modified_chats (list of str): Unique ID of modified chats
        """
        self.channel_id = channel.channel_id
        self.new_chats = new_chats
        self.removed_chats = removed_chats
        self.modified_chats = modified_chats


class EFBMemberUpdates(EFBStatus):
    """
    Inform the master channel on updates of members in a slave chat.

    Attributes:
        channel_id (str): ID of the issuing channel.
        chat_id (str): Unique ID of the chat.
        new_members (list of str): Unique ID of new members
        removed_members (list of str): Unique ID of removed members
        modified_members (list of str): Unique ID of modified members
    """

    def __init__(self, channel, chat_id, new_members=tuple(), removed_members=tuple(), modified_members=tuple()):
        """
        Args:
            channel (ehforwarderbot.EFBChannel): Slave channel that issues the update
            chat_id (str): Unique ID of the chat.
            new_members (list of str): Unique ID of new members
            removed_members (list of str): Unique ID of removed members
            modified_members (list of str): Unique ID of modified members
        """
        self.channel_id = channel.channel_id
        self.chat_id = chat_id
        self.new_members = new_members
        self.removed_members = removed_members
        self.modified_members = modified_members
