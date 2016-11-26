# Slave Channels
A _Slave channel_ is a channel that delivers messages between a chat platform
and the master channel.

## Structure
A slave channel class should inherit from the `EFBChannel` class, with some properties set as follows:
```python
class MySlaveChannel(EFBChannel):
    channel_name = "My Slave Channel"
    # Name of channel
    channel_emoji = "⭐"
    # Icon for the channel, better to choose an emoji similar to the original
    # logo of your platform.
    channel_id = "eh_random_slave"
    # Unique ID for the channel. Recommended format:
    # <author unique name>_<platform name>_slave
    channel_type = ChannelType.Slave
```

### Message queue
In the beginning, each channel is initialized with the common queue, namely a Python `queue.Queue()` queue. This is where your slave channel delivers messages to the master channel. Whenever there is a new message came from the slave channel, it should be processed to a `EFBMsg` object and then put in to the queue with `self.queue.put(mobj)` method.

A few methods are required to be implemented for every slave channel.

### `__init__(self, queue)`
`super().__init__(queue)` should be called in the beginning. The "super" `__init__` method assigns the message `queue` to `self.queue`. Any other authorization steps are recommended to be done is this method.

> Try to avoid user interaction as far as possible, if there is a way to login the platform using any fixed credentials, please avoid using dynamical verification.

If your platform requires user to provide any tokens (API key, secret, Username, Password, etc), you may ask your user to save those information to `config.py`, in a `dict` variable named with your channel unique ID. You can import it with `from config import <channel ID> as config`.

Definition of config keys and values should be written in the class docstring, and your channel support page (if applicable).

### `poll(self)`
This method should start polling for new message and prepare for pushing it to the queue. This method is put in a thread so you may not need to make another thread for your polling.

### `send_message(self, msg)`
This method sends a message from the master channel to your channel. `msg` is an `EFBMsg` object, delivered out from the master channel.

Some exceptions you may need to raise while processing an incoming message:
* `EFBChatNotFound`:  
  When the target chat/user is not found, or not reachable from the current user.
* `EFBMessageNotFound`:  
  When the message is replying to another message that is not found, or not reply-able.
* `EFBMessageTypeNotSupported`:  
  When the incoming message is in a type not supported by your platform.

You can also use any other existing exceptions or write your own exceptions.

### `get_chats(self)`
This method returns a `list` of `dict`s, where each item represents a chat session. It can be:
* A "user", a "group", or a "bot" in Telegram, Messenger, WhatsApp, Line, WeChat, etc.
* A "channel" in IRC, Slack
* Any possible "Direct Message" conversations in Twitter, Slack, etc.
* A "channel" in Telegram _(cuz it's different from that "channel")_

To simplify the categorization process, we name that:
* __"User"__ type is for those we send and get messages to one person.  
(Telegram _Channels_ with Admin access falls under here).
* __"Group"__ type is for those we send and get message to more than one person.

> __Note:__ You may not include chats that you can't send a message to, e.g. Telegram Channels with no admin access.

Each `dict` item should have:
```python
{
    'channel_name': self.channel_name,
    # Channel name
    'channel_id': self.channel_id,
    # Channel's unique ID
    'name': "Eana Hufwe",
    # Display name of the chat
    'alias': "Bossy",
    # Alternative name set by the user,
    # keep as same as "name" if not available
    'uid': "13245768",
    # Unique ID of the chat, keep it as unique and consistent as possible
    'type': "User"
    # "User" or "Group"
}
```

### `get_group_members(self, group_uid)`

> TODO: Documentation for `get_group_members`

## Command message
Slave channels can send messages that offer the user options to take action. This can be used in situations such as friend request, fund transfer and Telegram Inline Buttons.

Aside from sending a message with "Command" type (refer to the specification in "Message" documentation), the slave channel have to also provide a method for the command to be issued.

The method can take any argument of Python's standard data structure, and returns a string which is shown to the user as the result of the action.

## Extra functions

In some cases, your slave channel may allow the user to achieve extra functionality, such as creating groups, managing group members, etc.

You can receive such commands issued in a CLI-like style. An "extra function" method should only take one string parameter aside from `self`, and wrap it with `@extra` decorator from `utils` module. The extra decorator takes 2 arguments: `name`, a short name of the function, and `desc` a description of the function and its usage.

> **More on `desc`**  
`desc` should describe what the function does and how to use it. It's more like the help text for an CLI program. Since method of calling an extra function depends on the implementation of the master channel, you should use `{function_name}` as the function name in `desc`, and master channel will replace it with respective name.

The method should in the end return a string, which will be shown to the user as the result. Depends on the functionality of the function, it may be just a simple success message, or a long chunk of results.

Example:
```python
@extra(name="New group",
       desc="Create a new group.\n" +
            "Usage:\n" +
            "    {function_name} group_name|member_id_1|member_id_2|...\n" +
            "    e.g.: {function_name} My Group|123456|654321|393901"
            "    group_name: Name of new group, \"|\" is not allowed.\n" +
            "    member_id_n: ID of group members, you should fill at least one.")
def new_group(self, param):
    param = param.split('|')
    if len(param) < 2:
        return "Group name and at least one member ID should be provided."
    group_name = param[0]
    members = param[1:]
    try:
        self.myChat.create_group(group_name, members)
    except Exception as e:
        return repr(e)
    return "Group %s created with members %s." % (group_name, members).
```

## Media processing
Please refer to the _Media Processing_ section in the [Workflow](workflow.md) page.
