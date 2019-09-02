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

Alternatively, you can also use the :ref:`config:Configuration wizard` which
can also help you set up modules installed (if they also come with a wizard).

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

EFB supports translated user interface and prompts.
You can set your system language or locale environmental variables
(``LANGUAGE``, ``LC_ALL``, ``LC_MESSAGES`` or ``LANG``) to one of our
`supported languages`_ to switch language.

You can help to translate this project into your languages on
`our Crowdin page`_.

.. _supported languages: https://crowdin.com/project/ehforwarderbot/
.. _our Crowdin page: https://crowdin.com/project/ehforwarderbot/

.. note::

    If your are installing from source code, you will not get translations
    of the user interface without manual compile of message catalogs (``.mo``)
    prior to installation.

Launch EFB as a daemon process
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Since version 2, EH Forwarder Bot has removed the daemon helper as
it is unstable to use.  We recommend you to use mature solutions for
daemon management, such as systemd_, upstart_, or pm2_.

.. _systemd: https://www.freedesktop.org/wiki/Software/systemd/
.. _upstart: http://upstart.ubuntu.com/
.. _pm2: http://pm2.keymetrics.io/
