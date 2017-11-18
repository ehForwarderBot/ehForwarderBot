Getting started
===============

A few simple steps to get started with EFB.

A good network environment
--------------------------

Since most of our channels are using polling for message retrieval,
a good network environment is necessary for the bot to run smoothly.
A poor network environment may lead to slow response,
or loss of messages.

Choose, install and enable channel
----------------------------------

.. TODO, link to channel repository

.. TODO, where to download channel

To enable a channel, list the unique identifier of the channel in
profile's configuration file. The default path is ``~/.ehforwarderbot/default/config.yaml``.
Details about locations of configuration files is described in :doc:`directories.rst`.

.. note:: "Example"
    To enable the following channels:

    * Master channel
        * DemoMaster (``ehforwarderbot.channels.master.foo.demo``)
    * Slave channels
        * DemoSlave (``ehforwarderbot.channels.slave.foo.demo``)
        * RandomSlave (``ehforwarderbot.channels.slave.bar.random``)
        * DummySlave (``ehforwarderbot.channels.slave.bar.dummy``)

    In the ``config.yaml`` it should have the following lines::

        master_channel: ehforwarderbot.channels.master.foo.demo
        slave_channels:
        - ehforwarderbot.channels.slave.foo.demo
        - ehforwarderbot.channels.slave.bar.random
        - ehforwarderbot.channels.slave.bar.dummy

.. old_content
    ## Configure your channels
    Some channels, regardless of its type, may require you to provide some details for it to operate, such as API key/secret, login credentials, preferences, etc. Different modules may put their configuration in different ways, but the values should always be put a variable in `config.py`, where its variable name is the "unique ID" of the channel.
    For more details about how to configure your channel, please consult the respective documentation of the channels.
    ## Get it up and running
    Most of the time, you can just run `python3 daemon.py start` and it should be ready to go.
    .. tip:: "Run it as a normal process"
        Besides, you can still use the classic `python3 main.py` to launch EFB. If you want to keep it running in the background when daemon process is not working on your machine, you can use tools like `screen` or `nohup` to prevent it from being terminated during disconnection.
    However, some channels may require one-time credentials (e.g. Dynamic QR code scanning for WeChat Web Protocol). When you run the module, you may be required to take some actions before the bot goes online.
    If the channel does require you to take actions at run-time, it should state in the documentation.
    ## Keep it up at all times
    You can use any supervisor tool of your preference to keep EFB up at all times. However, this may not always work when you have channels that requires user interactions during initialization.
