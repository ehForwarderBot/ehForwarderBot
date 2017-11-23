class MsgType:
    Text = "Text"
    Image = "Image"
    Audio = "Audio"
    File = "File"
    Location = "Location"
    Video = "Video"
    Link = "Link"
    Sticker = "Sticker"
    Unsupported = "Unsupported"
    Command = "Command"
    Delete = "Delete"
    Status = "Status"


class ChatType:
    User = "User"
    Group = "Group"
    System = "System"


class TargetType:
    Member = "Member"
    Message = "Message"
    Substitution = "Substitution"


class ChannelType:
    Master = "Master"
    Slave = "Slave"
