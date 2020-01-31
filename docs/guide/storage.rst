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

Wizard
------

If your module requires relatively complicated configuration, 
it would be helpful to provide users with a wizard to 
*check prerequisites of your module* and *guide them to setup your module for use*.

From version 2, EFB introduced a centralised wizard program
to allow users to enable or disable modules in a text-based user 
interface (TUI). If you want to include your wizard program as a part
of the wizard, you can include a new entry point in your ``setup.py``
with `Setuptools' Entry Point feature`__.

.. __: https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins

The group for wizard program is ``ehforwarderbot.wizard``, and
the entry point function MUST accept 2 positional arguments:
profile ID and instance ID.

Example
```````

``setup.py`` script

.. code-block:: python

    setup(
        # ...
        entry_points={
            "ehforwarderbot.wizard": ['alice.irc = efb_irc_slave.wizard:main']
        },
        # ...
    )

``.egg-info/entry_points.txt``

.. code-block:: ini

    [ehforwarderbot.wizard]
    alice.irc = efb_irc_slave.wizard:main

``efb_irc_slave/wizard.py``

.. code-block:: python

    # ...

    def main(profile, instance):
        print("Welcome to the setup wizard of my channel.")
        print("You are setting up this channel in profile "
              "'{0}' and instance '{1}'.".format(profile, instance))
        print("Press ENTER/RETURN to continue.")
        input()

        step1()

        # ...
        