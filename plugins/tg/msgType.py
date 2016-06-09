class TGMsgType:
    Text = "Text"
    Audio = "Audio"
    Document = "Document"
    Photo = "Photo"
    Sticker = "Sticker"
    Video = "Video"
    Voice = "Voice"
    Contact = "Contact"
    Location = "Location"
    Venue = "Venue"
    System = "System"


def get_msg_type(msg):
    sys = ['new_chat_member',
           'left_chat_member',
           'new_chat_title',
           'new_chat_photo',
           'delete_chat_photo',
           'group_chat_created',
           'supergroup_chat_created',
           'migrate_to_chat_id',
           'migrate_from_chat_id',
           'channel_chat_created',
           'pinned_message']
    for i in sys:
        if getattr(msg, i, False):
            return TGMsgType.System
    types = ['audio',
             'document',
             'photo',
             'sticker',
             'video',
             'voice',
             'contact',
             'location',
             'venue']
    for i in types:
        if getattr(msg, i, False):
            return getattr(TGMsgType, i.capitalize())
    return TGMsgType.Text
