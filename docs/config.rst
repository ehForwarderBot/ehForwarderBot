Configuration File
==================

EFB has an overall configuration file to manage all enabled modules.
It is located under the :doc:`directory <directories>` of current
profile, and named :file:`config.yaml`.

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
regular expressions :regexp:`[a-zA-Z0-9_]+`. When instance ID is not defined,
the channel will run in the "default" instance with no instance ID.

To indicate the instance ID of an instance, append ``#`` following by the
instance ID to the module ID. For example, slave channel ``bar.dummy``
running with instance ID ``alice`` should be written as ``bar.dummy#alice``.
If the channel requires configurations, it should be done in the directory
with the same name (e.g. :file:`EFB_DATA_PATH/profiles/{PROFILE}/bar.dummy#alice`),
so as to isolate instances.

Please avoid having two modules with the same set of module ID and instance ID
as it may leads to unexpected results.

For example, to enable the following modules:

* Master channel
    * Demo Master (``foo.demo_master``)
* Slave channels
    * Demo Slave (``foo.demo_slave``)
    * Dummy Slave (``bar.dummy``)
    * Dummy Slave (``bar.dummy``) at ``alt`` instance
* Middlewares
    * Message Archiver (``foo.msg_archiver``)
    * Null Middleware (``foo.null``)

``config.yaml`` should have the following lines:

.. code-block:: yaml

    master_channel: foo.demo_master
    slave_channels:
    - foo.demo_slave
    - bar.dummy
    - bar.dummy#alt
    middlewares:
    - foo.msg_archiver
    - foo.null

Granulated logging control
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have special needs on processing and controlling the log produced
by the framework and running modules, you can use specify the log
configuration with `Python's configuration dictionary schema`_ under
section ``logging``.

An example of logging control settings:

.. code-block:: yaml

    logging:
        version: 1
        disable_existing_loggers: false
        formatters:
            standard:
                format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        handlers:
            default:
                level: INFO
                formatter: standard
                class: logging.StreamHandler
                stream: ext://sys.stdout
        loggers:
              '':
                    handlers: [default,]
                    level: INFO
                    propagate: true
              AliceIRCChannel:
                    handlers: [default, ]
                    level: WARN
                    propagate: false


.. _Python's configuration dictionary schema: https://docs.python.org/3.7/library/logging.config.html#logging-config-dictschema
