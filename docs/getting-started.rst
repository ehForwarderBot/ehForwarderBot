Getting started
===============

A few simple steps to get started with EFB.

Install EH Forwarder Bot
------------------------

EH Forwarder Bot can be installed in the following ways:

Install from PIP
~~~~~~~~~~~~~~~~

.. code-block:: shell

    pip3 install ehforwarderbot


Install manually
~~~~~~~~~~~~~~~~

Clone the project to local, and install with the install script.

.. code-block:: shell

    git clone https://github.com/blueset/ehforwarderbot
    cd ehforwarderbot
    python3 setup.py

.. todo: remove this block in final release

.. attention::

    Those instructions are not directly available until a stable
    release of this version.  If you are already here in the
    alpha/beta version docs, you should know what to do.

A good network environment
--------------------------

Since most of our channels are using polling for message retrieval,
a good network environment is necessary for the bot to run smoothly.
A poor network environment may lead to slow response,
or loss of messages.


Create local directories
------------------------

EFB uses a \*nix user configuration style, which is described in
details in :doc:`directories`. In short, if you are using the
default configuration, you need to create ``~/.ehforwarderbot``,
and give read and write permission to the user running EFB.

Choose, install and enable channel
----------------------------------

Currently, all channels that submitted to us are recorded in
the `channels repository <https://github.com/blueset/ehForwarderBot/wiki/Channels-Repository>`_.
You can choose the channels that fits your need the best.

Instructions about installing each channel is available at
their respective documentations.

When you have successfully installed a channel, you can enable
it by listing its Channel ID in the configuration file.
The default path is ``~/.ehforwarderbot/profiles/default/config.yaml``.
Please refer to :doc:`directories` if you have configured otherwise.

Please note that although you can have more than one slaves channels
running at the same time, you can only have exactly one master channels
running in one profile.

.. admonition:: Example
    :class: tip

    To enable the following channels:

    * Master channel
        * DemoMaster (``ehforwarderbot.channels.master.foo.demo``)
    * Slave channels
        * DemoSlave (``ehforwarderbot.channels.slave.foo.demo``)
        * RandomSlave (``ehforwarderbot.channels.slave.bar.random``)
        * DummySlave (``ehforwarderbot.channels.slave.bar.dummy``)

    In the ``config.yaml`` it should have the following lines:

    .. code-block:: yaml

        master_channel: ehforwarderbot.channels.master.foo.demo
        slave_channels:
        - ehforwarderbot.channels.slave.foo.demo
        - ehforwarderbot.channels.slave.bar.random
        - ehforwarderbot.channels.slave.bar.dummy

Launch EFB
----------

.. code-block:: shell

    python3 -m ehforwarderbot

This will launch EFB directly in the current environment. The default
:doc:`profile` is named ``profile``, to launch EFB in a different
profile, append ``--profile <profile-name>`` to the command.

For more command line options, use ``--help`` option.

Launch EFB as a daemon process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since version 2, EH Forwarder Bot has removed the daemon helper as
it is unstable to use.  We recommend you to use mature solutions for
daemon management, such as systemd, upstart, SysV or pm2.



.. todo: Insert more daemon managers

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
