Getting started
===============

A few simple steps to get started with EFB.

Install EH Forwarder Bot
------------------------

EH Forwarder Bot can be installed in the following ways:

.. note::

    The following instructions may not work properly
    until a stable release is uploaded. As you are in
    the beta version documentation, I assume you know
    what to do.

Install from PyPI
~~~~~~~~~~~~~~~~~

``pip`` will by default install the latest stable version
from PyPI, but development versions are available at PyPI
as well.

.. code-block:: shell

    pip3 install ehforwarderbot


Install from GitHub
~~~~~~~~~~~~~~~~~~~

This will install the latest commit from GitHub. It might not be
stable, so proceed with caution.

.. code-block:: shell

    pip3 install git+https://github.com/blueset/ehforwarderbot.git


Alternative installation methods
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can find a list of alternative installation methods contributed
by the community in the `project wiki`_.

For scripts, containers (e.g. Docker), etc. that may include one or
more external modules, please visit the `modules repository`_.

.. note::

    These alternative installation methods are maintained by the
    community, please consult their respective author or maintainer
    for help related to those methods.

.. _project wiki: https://github.com/blueset/ehForwarderBot/wiki/Alternative-installation-methods


A stable internet connection
----------------------------

Since the majority of our channels are using polling for message retrieval,
a stable internet connection is necessary for channels to run smoothly.
An unstable connection may lead to slow response, or loss of messages.


Create local directories
------------------------

EFB uses a \*nix user configuration style, which is described in
details in :doc:`directories`. In short, if you are using the
default configuration, you need to create ``~/.ehforwarderbot``,
and give read and write permission to the user running EFB.

Choose, install and enable modules
----------------------------------

Currently, all modules that was submitted to us are recorded in
the `modules repository`_.
You can choose the channels that fits your need the best.

Instructions about installing each channel is available at
their respective documentations.

When you have successfully installed a channel, you can enable
it by listing its Channel ID in the :doc:`configuration file <config>`.
The default path is ``~/.ehforwarderbot/profiles/default/config.yaml``.
Please refer to :doc:`directories` if you have configured otherwise.

Please note that although you can have more than one slaves channels
running at the same time, you can only have exactly one master channels
running in one profile. Meanwhile, middlewares are completely optional.

.. admonition:: Example
    :class: tip

    To enable the following modules:

    * Master channel
        * Demo Master (``foo.demo_master``)
    * Slave channels
        * Demo Slave (``foo.demo_slave``)
        * Dummy Slave (``bar.dummy``)
    * Middlewares
        * Null Middleware (``foo.null``)

    In the ``config.yaml`` it should have the following lines:

    .. code-block:: yaml

        master_channel: foo.demo_master
        slave_channels:
        - foo.demo_slave
        - bar.dummy
        middlewares:
        - foo.null

.. _modules repository: https://github.com/blueset/ehForwarderBot/wiki/Channels-Repository

Launch EFB
----------

.. code-block:: shell

    ehforwarderbot

This will launch EFB directly in the current environment. The default
:doc:`profile` is named ``default``, to launch EFB in a different
profile, append ``--profile <profile-name>`` to the command.

For more command line options, use ``--help`` option.

Use EFB in another language
~~~~~~~~~~~~~~~~~~~~~~~~~~~

TODO: talk about language env var, and crowdin.

Launch EFB as a daemon process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since version 2, EH Forwarder Bot has removed the daemon helper as
it is unstable to use.  We recommend you to use mature solutions for
daemon management, such as systemd_, upstart_, or pm2_.

.. _systemd: https://www.freedesktop.org/wiki/Software/systemd/
.. _upstart: http://upstart.ubuntu.com/
.. _pm2: http://pm2.keymetrics.io/

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
