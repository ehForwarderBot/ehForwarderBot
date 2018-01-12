Configurations and storage
==========================

Configurations and Permanent Storage
------------------------------------

As described in :doc:`/directories`, each module has
been allocated with a folder per profile for configurations
and other storage. The path can be obtained using
:meth:`~.ehforwarderbot.utils.get_data_path` with your
module ID. All such storage is specific to only one
profile.

For configurations, we recommend to use ``<module_data_path>/config.yaml``.
Similarly, we prepared :meth:`~.ehforwarderbot.utils.get_config_path`
to get the path for default config file. Again, you
are not forced to use this name or YAML as the
format of your config file.

Usually in the storage folder lives:

- Configuration files
- User credentials / Session storage
- Databases

Temporary Storage
-----------------

While processing multimedia messages, we inevitably need
to store certain files temporarily, either within the channel
or across channels. Usually, temporary files can be handled
with Python's ``tempfile`` library.