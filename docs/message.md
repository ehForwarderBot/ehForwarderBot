# Message Object (`EFBMsg`)
Message objects is one of the key concept in EFB. It's an universal standard to carry message, media, file and all other information between master and slave channels. It's critical for plugin makers to understand the message concept, and follow it as far as possible so as to ensure a smooth workflow between channels.

## Initialization
You can initialize a message object with your channel as the argument. This allows the object to automatically obtain name, ID and icon from the channel.

```python
msg = EFBMsg(self)
```

## Basic properties
* `channel_name`, `channel_emoji`, `channel_id` should be set during the initialization process.
* `source`: the type of sender of the message, a `MsgSource` object.  
  Possible values: `MsgSource.User`, `MsgSource.Group`, `MsgSource.System`
* `type`: Type of message, a `MsgType` object, default to `MsgType.Text`. Will introduce it in later part.
* `member`: The member in a group who sent the message. A "User dict" or `None`. Only available when `msg.source == MsgSource.Group`.
* `origin`: The sender, a user or a group who sent the message. A "User dict".
* `destination`: The destination user/group of the message. A "User dict", `"channel"` property is required, and shall not equal to the `channel_id` of the message.
* `target`: A "Target dict" or none. Used when the message is reply to or refering to another message or user.
* `uid`: String. A unique ID of the message. If your platform did not offer one, you may use the concatnation of the channel ID and a random GUID.
* `text`: String. The text content of the message.

### "User dict"
A user dict is used to represent a specific user or chat from a specific channel. It should looks like:
```python
{
    "channel": "<channel_id>",
    # The unique channel ID where the user is from.
    # Optional if it's the same channel as the message sender.
    "name": "Eana Hufwe",
    # Name of the User/Chat, as set by itself.
    "alias": "Bossy",
    # Alias/nickname/alternative name set by the user. Keep same as "name" if not available.
    "UID": "13245768"
    # Unique ID of the user/chat in the channel.
    # Must be unique and consistent within the channel.
}
```

### "Target dict"
Target dict is used when a message is reply to another message, or referring to other user(s).

There are 3 types of targets: `Member`, `Message`, and `Substitution`

**TargetType: Member**  
This is for the case where the message is targeting to a specific member in the group. `target['target']` here is a "User dict".

Example:
```python
target = {
   'type': TargetType.Member,
   'target': {
       "name": "Target name",
       'alias': 'Target alias',
       'uid': 'Target UID',
   }
}
```

**TargetType: Message**  
This is for the case where the message is directly replying to another message. `target['target']` here is an `EFBMsg` object.

> Tip: Depends on the need of the other channel, you may need to include at least:
> * User dict for sender and recipient
> * Message type and text
> * Message unique ID
>
> But try to include as much detail as possible.
>
> **Notice**: You should not include further Target dict in this `EFBMsg` object.


Example:
```python
target = {
   'type': TargetType.Message,
   'target': EFBMsg()
}
```

**TargetType: Substitution**  
This is for the case when user "@-ed" a list of users in the message. `target['target']` here is a dict of correspondence between the string, or start and end point of the substring (in Python index) used to refer to the user in the message and a user dict.

Example:
```python
target = {
   'type': TargetType.Substitution,
   'target': {
      '@alice': {
          'name': "Megpoid",
          'alias': 'Gumi',
          'uid': "123456"
      },
      '@bob': {
          'name': "Gackpoid",
          'alias': 'Gakupo',
          'uid': "654321"
      },
      (13, 18): {
          'name': "Cyber Songman",
          'alias': "Cyman",
          'uid': "162534"
      }
      # Here (13, 18) refers to msg.text[13:18]
   }
}
```

## Media storage

Any media should be saved into the local storage path. The standard path should be `./storage/<channel id>/<filename>`. File should at least have read permission for all users. File may be unlink (deleted) by the target channel.

## Message types
### Text message
**Type**: MsgType.Text  
**Additional Parameters**: None

Pretty simple, just put the text into `msg.text` attribute.

### Image/Pictures
**Type**: MsgType.Image  
**Additional Parameters**: path, mime, file

Picture type, may include GIF images. Stickers are not included. `text` for captions. The image should be saved into local storage, with:

* `path`: Relative path to the image, e.g. `storage/my_slave_channel/picture_1234567890.png`
* `mime`: MIME type string of the file, e.g. `image/png`
* `file`: File object of the image, done by `open(msg.path, 'rb')`

> Definition for `path`, `mime`, `file` is similar for other multimedia files.

### Stickers
**Type**: MsgType.Sticker  
**Additional Parameters**: path, mime, file

Sticker messages.
Specification for `path`, `mime`, `file` refer to `MsgType.Image`.

### Audio/Music/Voice
**Type**: MsgType.Audio  
**Additional Parameters**: path, mime, file

Audio message, including music file and voice message.
Specification for `path`, `mime`, `file` refer to `MsgType.Image`.

### Video
**Type**: MsgType.Video  
**Additional Parameters**: path, mime, file

Video message.
Specification for `path`, `mime`, `file` refer to `MsgType.Image`.

### File
**Type**: MsgType.File  
**Additional Parameters**: path, mime, file

File message.
Specification for `path`, `mime`, `file` refer to `MsgType.Image`.

### Location
**Type**: MsgType.Location  
**Additional Parameters**: attributes

Location messages.

* `text`: Description, such as Name of place, address, etc.
* `attributes`: a `dict` with 2 items:  
  "latitude": Latitude value in float,  
  "longitude": Longitude value in float.

### Link
**Type**: MsgType.Link  
**Additional Parameters**: attributes

Shared links.

* `text`: Structured text with at least the URL in the message.
* `attributes`: a `dict` with 4 items: _(None if not available)_  
  "title": Title of the linked article,  
  "description": Brief description of the article,  
  "image": Thumbnail URL or local file path,  
  "url": URL in the message.

### Command
**Type**: MsgType.Command
**Additional Parameters**: attributes

This message is sent when a message from **slave** channel provides action options to the user. E.g.: Friend request,
money transfer, etc.

`text` should include all necessary information for the user understand the situation and take action.

`attributes` is a dict with one item: `commands`, whose value is a list of commands with structure described below:

```python
msg.attributes = {
    "commands": [
        {
            "name": "A human-readable name for the command",
            "callable": "name to the callable function in your channel object",
            "args": [
                "a list of positional parameters passed to your function"
            ],
            "kwargs": {
                "desc": "a dict of keyword parameters passed to your function"
            }
        },
        {
            "name": "Greet @blueset on Telegram",
            "callable": "send_message_by_username",
            "args": [
                "blueset",
                "Hello!"
            ],
            "kwargs": {}
        }
    ]
}
```

### Unsupported message
> TODO: Unsupported message documentation.
