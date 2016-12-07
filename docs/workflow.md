# Walk-through — How EFB works

## `main.py`
`main.py` first defines a queue `q` for processing any message from slave channels to master channel (The "global message queue").

Then, loading from `config.py`, it gets a list of activated slave channels and master channel. Channels objects are initiated one by one, with `q` as the parameter, and stored to a list named `slaves`. Right after that, object for master channel is also created.

At this point of time, all channels should be initialized and logged in (Additional actions may be required for logging in).

### Polling
Right after all channels are initialized, the `poll` method of each channel is called, and assigned to different threads. From this point onwards, channels start to poll for messages from their respective chat platforms.

#### Slave thread
The polling thread of slave channels continues to poll for messages from their platform, preprocess it, and then enqueue it to the global message queue.

#### Master thread
The polling method from the master thread not only needs to poll for message from the user, but also check consistently for incoming messages in the global message queue.

## Master channel
Roughly speaking, a master channel has mainly 2 jobs:
* Process message from user
* Process message from channel  
  _(Keep an infinite loop alongside the polling thread and pull new message from the global message queue to process)_

Since for this part it's your own plugin interacting with the user, you may use __any possible way__ to process it. Here I'd talk about how my Telegram channel, "EH Telegram Master" (ETM), does it.

### Feature 1: Chat Binding
In order to get commonly used chat organized, ETM assign a slave chat to any other group. You can even create a new group for a remote chat.

Then the user can directly send messages into the group for ETM to forward it. When you "direct reply" to a message, the reply will also be sent to the remote channel.

### Feature 2: Chat head
For any message come from a chat not binded, EFB will deliver to user in the "bot chat". Then if you want to reply to the user, you need to "direct reply" to the message. However, when you want to send a message to a new remote chat when you have no where to reply to, there's where chat head comes in.

Send `/chat` command, and ETM will send you a list of available remote chats to choose from. When choosing a chat, you will see a message, for message to the chat you've chosen previously, to reply to it.
> Note that directly reply in remote channel is not available to unbind chat.

### Deliver user's message to a slave channel
To deliver user's message to a slave channel, you should first gather all the information of the message, including: the target channel, target chat, message type, etc. Then compile it into an `EFBMsg` object and call the `sendMessage` method of the slave channel with the message.

## Slave Channel
Slave channel has rather less things to do, get and enqueue incoming message, and send message to the platform. Also you may need to generate a list of possible recipients for the Master channel. That should be most of it.

## Commands
Once there's any message from a slave channel that allows the user to take action, the slave channel will enclose details of actions (namely method names and arguments) into an `EFBMsg` object and send them to the master channel.

Master channel uses its own method to ask the user to make a decision. With the decision, the master channel will call the respective method of the slave channel with the argument given.

The method of slave channel returns a string as the result which is then reflected back to the user.

## Media processing
In order to suit the requirement of each chat platform API, it's often necessary to preprocess media files, such as encoding, converting formats, etc. The usual procedure of delivering message with media file is as follows:

1. Sender channel downloads the media file to `storage/<channel_id>` directory.
2. Sender channel compiles details (MIME type, file path, etc) to an `EFBMsg` object.
3. Recipient channel gets the object and analyze the file.
4. Recipient channel pre-process the media file (encoding, resizing, etc.)
5. Recipient channel send out the message to remote server, and then remove all files related to the message.

Despite no requirement on the module or external library used by a channel, it is recommended to utilize one of the following external libraries, in order to minimize the number of the external libraries to be installed by the end-user.
* `ffmpeg`
* `imagick`
* `libmagic`
