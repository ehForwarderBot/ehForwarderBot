Configuration File
==================

EFB has an overall configuration file to manage all enabled modules.
It is located under the :doc:`directory <directories>` of current
profile, and named ``config.yaml``.

Syntax
~~~~~~

The configuration file is in the YAML syntax. If you are not familiar
with its syntax, please check its documentations and tutorials for
details.

* The ID of the master channel enabled is under the key ``master_channel``
* The ID of slave channels enabled is listed under the key
  ``slave_channels``. It has to be a list even if just one channel is
  to be enabled.
* The ID of middlewares enabled are listed under the key ``middlewares``.
  It has to be a list even if just one middleware is to be enabled.
  However, if you don't want to enable any middleware, just omit the section
  completely.

Instance ID
~~~~~~~~~~~

To have multiple accounts running simultaneously, you can appoint an instance
ID to a module. Instance ID can be defined by the user, and if defined,
it must has nothing other than letters, numbers and underscores, i.e. in
regular expressions ``[a-zA-Z0-9_]+``. When instance ID is not defined,
the channel will run in the "default" instance with no instance ID.

To indicate the instance ID of an instance, append ``#`` following by the
instance ID to the module ID. For example, slave channel ``bar.dummy``
running with instance ID ``alice`` should be defined as ``bar.dummy#alice``.
If the channel requires configurations, it should be done in the directory
with the same name (e.g. ``EFB_DATA_PATH/profiles/PROFILE/bar.dummy#alice``),
so as to isolate instances.

Please avoid having two modules with the same set of module ID and instance ID
as it may leads to unexpected results.


.. admonition:: Example
    :class: tip

    To enable the following modules:

    * Master channel
        * Demo Master (``foo.demo_master``)
    * Slave channels
        * Demo Slave (``foo.demo_slave``)
        * Dummy Slave (``bar.dummy``)
        * Dummy Slave (``bar.dummy``) at ``alt`` instance
    * Middlewares
        * Message Archiver (``foo.msg_archiver``)
        * Null Middleware (``foo.null``)

    In the ``config.yaml`` it should have the following lines:

    .. code-block:: yaml

        master_channel: foo.demo_master
        slave_channels:
        - foo.demo_slave
        - bar.dummy
        - bar.dummy#alt
        middlewares:
        - foo.msg_archiver
        - foo.null