Launch the framework
====================

EH Forwarder Bot offered 2 ways to launch the framework:

- ``ehforwarderbot``
- ``python3 -m ehforwarderbot``

Both commands are exactly the same thing, accept the
same flags, run the same code. The latter is only a backup
in case the former does not work.

Options
-------

- ``-h``, ``--help``: Show help message

- :samp:`-p {PROFILE}`, :samp:`--profile {PROFILE}`: Switch :doc:`profile <profile>`

    From version 2, EFB supports running different instances
    under the same user, identified by their profiles.
    The default profile is named ``default``.

- ``-V``, ``--version``: Print version information

    This shows version number of Python you are using,
    the EFB framework, and all channels and middlewares
    enabled.

- ``-v``, ``--verbose``: Print verbose log

    This option enables verbose log of EFB and all enabled
    modules. This, together with ``--version``, is particularly
    useful in debugging and issue reporting.

- ``--trace-threads``: Trace hanging threads

    This option is useful to identify source of the issue
    when you encounter situations where you had to force quit
    EFB. When this option is enabled, once the first stop signal (``SIGINT`` or
    ``SIGTERM``) is sent, threads that are *asleep* will be identified and
    reported every 10 seconds, until a second stop signal is seen.

    In order to use this option, you need to install extra Python dependencies
    using the following command.

    .. code-block:: shell

        pip3 install 'ehforwarderbot[trace]'


Quitting EFB
------------

If you started EFB in a shell, you can simply press :kbd:`Control-c` to trigger
the quit process. Otherwise, ask your service manager to issue a ``SIGTERM``
for a graceful exit. The exit process may take a few second to complete.

.. important::
    It is important for you to issue a graceful termination signal (e.g.
    ``SIGTERM``), and **NOT** to use ``SIGKILL``. Otherwise you may face the
    risk of losing data and breaking programs.

If you have encountered any issue quitting EFB, press :kbd:`Control-c` for 5
times consecutively to trigger a force quit. In case you have frequently
encountered situations where you had to force quit EFB, there might be a bug
with EFB or any modules enabled. You may want to use the ``--trace-threads``
option described above to identify the source of issue, and report this to
relevant developers.
