# Walk-through — How EFB works

## `main.py`
`main.py` first defines a queue `q` for processing any message from slave channels to master channel (The "global message queue").

Then, loads from `config.py`, it gets a list of activated slave channels and master channel. Channels objects are initiated one by one, with `q` as the parameter, and stored to a list named `slaves`. Right after that, object for master channel is also created.

At this point of time, all channels should be initialized and logged in (Additional actions may be required for logging in).

### Polling
Right after all channels are initialized, the `poll` method of each channel is called, and assigned to different threads. From this point onwards, channels are starting to poll for messages from their respective chat platforms.

#### Slave thread
The polling thread of slave channels continues to poll for messages from their platform, preprocess it, and then enqueue it to the global message queue.

#### Master thread
The polling method from the master thread not only need to poll for message from the user, but also need to check consistently for incoming messages in the global message queue.

## Master channel
Roughly speaking, a master channel has mainly 2 jobs:
* Process message from user
* Process message from channel  
  _(Keep an infinite loop alongside the polling thread and pull new message from the global message queue to process)_

Since for this part it's your own plugin interact with the user, you use __any possible way__ to process it. Here I'd talk about how my Telegram channel, "EH Telegram Master" (ETM), does it.

### Feature 1: Chat Binding
In order to get commonly used chat organized, ETM is able to assign a slave chat to any other group. You can even create a new group for a remote chat.

Then the user can directly send message into the group for ETM to forward it. When you direct reply to a message, a direct reply will also be sent to the remote channel.

### Feature 2: Chat head
For any messages come from a chat not in bind, EFB will directly to user in the "bot chat". Then if you want to reply to the user, you need to "direct reply" to the message. However, when you want to send a message to a new remote chat when you have no where to reply to, there's where chat head comes in.

Send `/chat` command, and ETM will send you a list of available remote chats to choose from. When choosing a chat, you will se a message that instruct you to reply to it for message to the chat you've chosen previously.
> Note that directly reply in remote channel is not available to unbind chat.

### Deliver user's message to a slave channel
To deliver user's message to a slave channel, you should first gather all the information of the message, including: the target channel, target chat, message type, etc. Then compile it into an `EFBMsg` object and call the `sendMessage` method of the slave channel with the message.

## Slave Channel
Slave channel has rather less things to do, get and enqueue incoming message, and send message to the platform. Also you may need to generate a list of possible recipients for the Master channel. That should be most of it.

> In the future, I may also come out with a protocol for command delivery. This includes some common ones like adding or accepting new contacts to slave channel, or even customizable ones. See when can I finish it. :P
