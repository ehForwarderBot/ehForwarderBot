Directories
===========

Since EH Forwarder Bot 2.0, most modules should be
installed with the Python Package Manager ``pip``,
while configurations and data are stored in the "EFB
data directory".

By default, the data directory is user specific, located in
the user's home directory, ``~/.ehforwarderbot``.  This can be
overridden with the environment variable ``EFB_DATA_PATH``.
This path defined here should be an **absolute path**.

.. comment, deprecated
    EFB cache is deprecated. System temporary file
    manager is used instead.
    Besides the data path, you can also customize the path for
    cache/temporary files produced by channels. By default, it's
    stored together with the data: ``~/.ehforwarderbot/cache``.
    It can be overridden with environment variable
    ``EFB_CACHE_PATH``.

Directory structure
-------------------

Using the default configuration as an example, this section
will introduce about the structure of EFB data directory.

::

    ./ehforwarderbot                or $EFB_DATA_PATH/username
    |- profiles
    |  |- default                   The default profile.
    |  |  |- config.yaml            Main configuration file.
    |  |  |- dummy_ch_master        Directory for data of the channel
    |  |  |  |- config.yaml         Config file of the channel. (example)
    |  |  |  |- ...
    |  |  |- random_ch_slave
    |  |  |  |- ...
    |  |- profile2                  Alternative profile
    |  |  |- config.yaml
    |  |  |- ...
    |  |- ...
    |- modules                      Place for source code of your own channels/middlewares
    |  |- random_ch_mod_slave       Channels here have a higher priority while importing
    |  |  |- __init__.py
    |  |  |- ...

