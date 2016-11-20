# Getting started

A few simple steps to get started with EFB.

## Choose, install and enable plugins
From the [Plugins repository]() _(TODO)_, you can choose among a range of different channels that fits your need. If you have completed all the steps in [Installation instruction](installation.md), you are ready to proceed with **official channels** (i.e. channels maintained by the framework author). For other channels, you may need to check up with their respective instructions.

To install plugins, download or clone their project, and save it in the `/plugins` folder.

To enable a plugin, you should first obtain its "import path" and "class name". You can find it in the Plugins repository.
As of now, you must enable one and *only* one master channel, and *at least* one slave channel in order for EFB to work.

To enable a channel, add its "import path" and "class name" to the `config.py` file.

The variable `master_channel` is a tuple of 2 strings where first string is its import path and the other is its class name.

The variable `slave_channels` is a list of tuples of 2 strings where each of the tuples is formatted in the same way described above.

> **Example**
>
> When enabling the following channels:
> * Master channel
>     * DemoMaster  
>       Import path: `plugins.eh_demo_master`  
>       Class name: `DemoMasterChannel`
> * Slave channels
>     * DemoSlave  
>       Import path: `plugins.eh_demo_slave`  
>       Class name: `DemoSlaveChannel`
>     * RandomSlave  
>       Import path: `plugins.eh_random_slave`  
>       Class name: `RandomSlaveChannel`
>     * MyChatSlave  
>       Import path: `plugins.eh_mychat_slave`  
>       Class name: `MyChatSlaveChannel`
>
> You should have the `master_channel` and `slave_channels` variable defined as follow:
>
> ```python
> master_channel = "plugins.eh_demo_master", "DemoMasterChannel"
> slave_channels = [
>     ("plugins.eh_demo_slave", "DemoSlaveChannel"),
>     ("plugins.eh_random_slave", "RandomSlaveChannel"),
>     ("plugins.eh_mychat_slave", "MyChatSlaveChannel")
> ]
> ```

> **Technical details**  
The "import path" and "class name" of the module is actually used to import the channel class at root level.  
It can be understood as `from <import_path> import <class_name>`.

## Configure your channels
Some channels, regardless of its type, may require you to provide some details for it to operate, such as API key/secret, login credentials, preferences, etc. Different modules may put the configuration in different way, but it should always be a variable in `config.py`, where its variable name is the "unique ID" of the channel.

For more details on how do configure your channel, please consult respective documentation of the channels.

## Get it up and running
Most of the times, you can just run `python3 main.py -d start` _(TODO: Daemon in plan)_ and it should be ready to go.

> **Daemon process is in plan**  
> As of now, you can still use the classic `python3 main.py` to launch EFB. If you want to keep it running in the background when accessing the machine via SSH, you can use tools like `screen` to prevent it from being terminated during disconnection.

However, some channels may require one-time credentials (e.g. Dynamic QR code scanning for WeChat Web Protocol). When you run the module, you may be required to take some actions before the bot goes online.

If the channel do require you to take action at run-time, it should be stated in the documentation.

## Keep it up at all times
You can use any supervisor tool of your preference to keep EFB up at all times. However, this may not always work when you enables channels that requires interactive initialization.
