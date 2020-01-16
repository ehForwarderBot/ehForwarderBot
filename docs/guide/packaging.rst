Packaging and Publish
=====================

Publish your module on PyPI
---------------------------

Publish modules on PyPI is one of the easiest way for
users to install your package.  Please refer to related
documentation and tutorials about PyPI and pip for
publishing packages.

For EFB modules, the package is RECOMMENDED to have
a name starts with ``efb-``, or in the format of
``efb-platform-type``, e.g. ``efb-irc-slave`` or
``efb-wechat-mp-filter-middleware``. If there is a
collision of name, you MAY adjust the package name
accordingly while keeping the package name starting
with ``efb-``.

When you are ready, you may also want to add your module to
the `Modules Repository`_ of EFB.

.. _Modules Repository: https://efb-modules.1a23.studio

Module discovery
----------------

EH Forwarder Bot uses `Setuptools' Entry Point feature`__
to discover and manage channels and middlewares. In your
``setup.py`` script or ``.egg-info/entry_points.txt``,
specify the group and object as follows:

.. __: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

* Group for master channels: ``ehforwarderbot.master``
* Group for slave channels: ``ehforwarderbot.slave``
* Group for middlewares: ``ehforwarderbot.middleware``

Convention for object names is ``<author>.<platform>``,
e.g. ``alice.irc``. This MUST also be your module's ID.

Object reference MUST point to your module's class,
which is a subclass of either :class:`.Channel` or :class:`.Middleware`.

Example
-------

``setup.py`` script

.. code-block:: python

    setup(
        # ...
        entry_points={
            "ehforwarderbot.slave": ['alice.irc = efb_irc_slave:IRCChannel']
        },
        # ...
    )

``.egg-info/entry_points.txt``

.. code-block:: ini

    [ehforwarderbot.slave]
    alice.irc = efb_irc_slave:IRCChannel

Private modules
---------------

If you want to extend from, or make changes on existing
modules for your own use, you can have your modules in
the private modules :doc:`directory <../directories>`.

For such modules, your channel ID MUST be the fully-qualified
name of the class. For example, if your class is located
at ``<EFB_BASE_PATH>/modules/bob_irc_mod/__init__.py:IRCChannel``,
the channel MUST have ID ``bob_ric_mod.IRCChannel`` for the
framework to recognise it.
