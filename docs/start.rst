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

- ``-p PROFILE``, ``--profile PROFILE``: Switch :doc:`profile <profile>`

    From version 2, EFB supports running different instances
    under the same user, identified by their profiles.
    The default profile is named ``default``.

- ``-V``, ``--version``: Print version information

    This shows version number of Python you are using,
    the EFB framework, and all channels and middlewares
    enabled.

- ``-v``, ``--verbose``: Print verbose log

    This option enables verbose log of EFB and all enabled
    modules. This, together with ``-V``, is particularly
    useful in debugging and issue reporting.
