# Master Channel

Master channel in EFB directly communicates with the user through a chat platform. It's rather more complicated compare to slave channels, as it needs to coordinate and process messages and commands from a number of slave channels.

## Initialization and polling
Similarly to slave channels, master channels also need to initialize and poll for messages from the chat platform.

All log-in and initializing process are done `__init__(self, queue, slaves)` method, where:
* `queue` is the message queue (`queue.Queue`) from slave channels.
* `slaves` is the dict of all enabled channels, where the keys are channel UIDs, and values point to the channel objects.

`super().__init__(queue)` should be called in the beginning. The "super" `__init__` method assigns the message `queue` to `self.queue`.

If your platform requires extra interaction before polling, it should be done in the `__init__` method.

!!! note
    Try to avoid user interaction as far as possible, if there is a way to login the platform using any fixed credentials, please avoid using dynamical verification.

If your platform requires user to provide any tokens (API key, secret, username, password, etc), you may ask your user to save those information to `config.py`, in a `dict` variable named with your channel unique ID. You can import it with `import config`, and call it with `config.<channel_id>`.

Definition of config keys and values should be written in the class docstring, and your channel support page.

`poll(self)` is for polling message from the related chat platform, and also polling message from slave channels from the global message queue.

## Message delivery
### Design guideline
The implementation shall resemble the appearance as far as possible, and in the same time requires as less user involvement for set up as possible.

In the extremely ideal case, the master channel agent should:

* Have an independent chat "timeline" for each chat from slave channel, with indication of each slave channel. It should looks similar, if not identical to a normal chat in original platform.
* Identify all members in a group chat.
* Support all possible static message types (those defined in EFB, PRs are welcomed for extra type support).
* Utilize advanced features (interactive command, variable messages, etc.) for "commands", "extra functions" and other unique features you can bring for better usability.

### From slave channels
When messages are dequeued from the global message queue, it should be processed and delivered to the user. To poll for messages, you can simply:

```python
while True:
    msg = self.queue.get()
    self.process_msg(msg)
    self.queue.task_done()
```

The `m` you get from the queue should be a valid `EFBMsg` object. If there's any problem with it, it should most probably be the fault of the issuing slave channel.

For more details on `EFBMsg` format, check [the documentation of EFBMsg](message.md).

#### Command messages
Different from normal messages, command messages allows user to give response with options provided by the message. The message shown to the user should only have:

* Command description (usually `msg.text`)
* List of options (`name` of each command)
* How should the user choose an option. (button, command string, etc)

Channel should avoid exposing information including `channel_id`, `callable`, `args` and `kwargs` to the user (for security and user-friendliness).

When the response of user is received, you can use the information from the message from slave to run the command on slave channel.

```python
# self.slaves: the slave channels dict in __init__
# msg: the command message
# option_id: the option chosen by user
command = msg.attributes['commands'][option_id]
result = getattr(self.slaves[msg.channel_id], command['callable'])(*command['args'], **command['kwargs'])
```

A valid command callback should return a string, as the result of execution bring back to the user.

### To slave channels
Compile your message into a `EFBMsg` object, and pass it directly to the `send_message` respective channel. Each channel should have a standard `send_message(self, msg)` method for message delivery.

Possible message recipients can come from either incoming messages from slave channels, or the `get_chats(self)` method of each slave channel.

Notice that channels should first identify a user with their unique ID, before checking with other properties such as `name`, `alias`, `type`, etc.

!!! note
    Refer to the [Channel documentation](channel.md) for details on `get_chat(self)`.

When sending a message to a slave channel, you may encounter one of the following exceptions:

* `EFBMessageTypeNotSupported`:  
  Message type sent is not supported by the slave channel.
* `EFBChatNotFound`:  
  Recipient (user/chat) is not found, or invalid in the target channel.
* `EFBMessageNotFound`:  
  The message "target"ed is not found in the target channel. _(see [EFBMsg](message.md) for message targeting)_

## Extra functions
Some slave channels may provide a some "extra functions" that allows the user to control it apart from ordinary message deliveries. Every slave channel has a method `get_extra_functions(self)` that returns a dict of all extra functions it offers, in the format of `{"callable_name": callable}`.

All "extra function" methods, takes only one string parameter. You can pass argument to them like a linux/unix CLI software. An "extra function" method has 2 attributes:
* `name` (str): A short name of the "extra function"
* `desc` (str): Description and usage of it

In order to allow user to have an intuitive understanding of the usage instruction, you can replace the function name to the one the channel expose to the user. In the `desc` string, the part representing a string name is written as `"{function_name}"`, so that you can fit in your own function name with `my_fn.desc.format(function_name="my_fn_name")`.

Similar to command message methods, all "extra function" methods also returns a string which should be reflected back to the user as the result of execution.

## Media processing
Please refer to the "Media processing" section in [Walk through](workflow.md) for details.
 
