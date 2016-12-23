# `EFBChannel`

`EFBChannel` is the base class for EFB channels. All channel classes, master and slave, should extend this class. It can be defined in either a single file or a module folder with `__init__.py`.

## Attributes
**channel_name** (str)  
Name of the channel, usually includes the platform name.

**channel_emoji** (str)  
A short representation of the channel, symbols or pictographs (emojis) of visually length 1 is recommended.  
_(e.g. 👁‍🗨`"\U0001F441\u200D\U0001F5E8"` is considered visually in length 1 on most platforms, as it's usually rendered as one emoji)_

**channel_id** (str)  
A **unique** channel ID that is used to identify your channel. Usually named like `"<author>_<platform>_<type>"`, where type is either "master" or "slave".  
All channel IDs should matching the following RexEx:

```regex
^[A-Za-z][A-Za-z0-9_]+$
```

**channel_type** (`ChannelType` constant)  
Type of the channel, choose between
* `ChannelType.Master`
* `ChannelType.Slave`

**queue** (queue.Queue)  
Global message queue initialized by the parental `__init__` method. This queue is used to deliver messages from slave channels to the master channel.

## Methods
Methods below are required to be implemented for respective channel types noted, unless otherwise stated.

**__init__(self, queue)** _(for slave channels)_  
**__init__(self, queue, slaves)** _(for master channels)_  
Initialize the channel and log in the account (if necessary) with in this method. `super().__init__(queue)` must always be called in the beginning.

Args:

* `queue` (queue.Queue): Global message queue, used for message delivery from slave channels to the master channel.
* `slaves` (dict): All enabled slave channel objects. Format: `"channel_id": channel_object`.

**poll(self)** _(for both types)_  
Message polling from your chat platform should be done in this method. When all channels are initialized, `poll` from all enabled channels are called in separated threads, and run concurrently.

Method of getting messages which requires extra set up by the user or which may reduce compatibility, including Webhooks, shall be avoided or used as an alternative method.

**get_extra_functions(self)** _(ready implemented, for slave channels)_  
Returns a `dict` of all extra functions of the slave channel, in the format of `"callable_name": callable`.

**send_message(self, msg)** _(for slaves channels)_  
This method sends messages from master channel to slave channel. All related media files should be cleared when the message is sent.

Args:

* msg (EFBMsg): The message object.

Raises:

* `EFBChatNotFound`
* `EFBMessageNotFound`
* `EFBMessageTypeNotSupported`

**get_chats(self)** _(for slave channels)_
Returns a `list` of `dict`s for available chats in the channel. Each `dict` should be like:
```python
{
    "channel_name": self.channel_name,
    "channel_id": self.channel_id,
    "name": "Name of the chat",
    "alias": "Alternative name of the chat (alias, nickname, remark name, contact name, etc)", # None if N/A
    "uid": "Unique ID of the chat",
    "type": MsgSource.User # or MsgSource.Group
}
```

## Command methods (for slave channels)
In command messages (see EFBMsg docs), the callable should be a method in your channel class. Those methods should all return a string showing the result which is to be reflected to the user. There is no other restrictions other than this.

## Extra functions (for slave channels)
Extra functions are provided for user to remotely control their accounts in other platforms, aside form mere message delivery.

Extra function methods should be wrapped with the decorator `utils.extra`, which takes 2 arguments: `name` and `desc`.

Refer to the [slave channels guide](slave-channel.md) for more details.
