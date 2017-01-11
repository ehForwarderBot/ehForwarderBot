# Getting started

A few simple steps to get started with EFB.

## A good network environment
Since most of our channels are using polling for message retrieval, a good network environment is necessary for the bot to run smoothly. A poor network environment may lead to slow response, or loss of messages.

## Choose, install and enable channel
From the [channels repository](channels-repository.md), you can choose among a range of different channels that fit your need. If you have completed all the steps in [Installation instruction](installation.md), you are ready to proceed with **official channels** (i.e. channels maintained by the framework author). For other channels, you may need to look up into their respective instructions.

To install a channel, download or clone their project, and save it in the `/plugins` folder.

To enable a channel, you should first obtain its "import path" and "class name" which can be found in the channels repository.
As of now, you must enable one and *only* one master channel, and *at least* one slave channel in order for EFB to work.

To enable a channel, add its "import path" and "class name" to the `config.py` file.

The variable `master_channel` is a tuple of 2 strings where first string is its import path and the other is its class name.

The variable `slave_channels` is a list of tuples of 2 strings where each of the tuples is formatted in the same way described above.

A sample of config file is available at `config.sample.py`.

!!! note "Example"
    When enabling the following channels:

    * Master channel
        * DemoMaster  
          Import path: `plugins.eh_demo_master`  
          Class name: `DemoMasterChannel`
    * Slave channels
        * DemoSlave  
          Import path: `plugins.eh_demo_slave`  
          Class name: `DemoSlaveChannel`
        * RandomSlave  
          Import path: `plugins.eh_random_slave`  
          Class name: `RandomSlaveChannel`
        * MyChatSlave  
          Import path: `plugins.eh_mychat_slave`  
          Class name: `MyChatSlaveChannel`

    You should have the `master_channel` and `slave_channels` variable defined as follow:

        master_channel = "plugins.eh_demo_master", "DemoMasterChannel"
        slave_channels = [
            ("plugins.eh_demo_slave", "DemoSlaveChannel"),
            ("plugins.eh_random_slave", "RandomSlaveChannel"),
            ("plugins.eh_mychat_slave", "MyChatSlaveChannel")
        ]

!!! tip "Technical details"
    The "import path" and "class name" of the module is actually used to import the channel class at root level.  
    It can be understood as `from <import_path> import <class_name>`.

## Permissions
`storage` directory should be given read and write access for media processing.

## Configure your channels
Some channels, regardless of its type, may require you to provide some details for it to operate, such as API key/secret, login credentials, preferences, etc. Different modules may put their configuration in different ways, but the values should always be put a variable in `config.py`, where its variable name is the "unique ID" of the channel.

For more details about how to configure your channel, please consult the respective documentation of the channels.

## Get it up and running
Most of the time, you can just run `python3 daemon.py start` and it should be ready to go.

!!! tip "Run it as a normal process"
    Besides, you can still use the classic `python3 main.py` to launch EFB. If you want to keep it running in the background when daemon process is not working on your machine, you can use tools like `screen` or `nohup` to prevent it from being terminated during disconnection.

However, some channels may require one-time credentials (e.g. Dynamic QR code scanning for WeChat Web Protocol). When you run the module, you may be required to take some actions before the bot goes online.

If the channel does require you to take actions at run-time, it should state in the documentation.

## Keep it up at all times
You can use any supervisor tool of your preference to keep EFB up at all times. However, this may not always work when you have channels that requires user interactions during initialization.
