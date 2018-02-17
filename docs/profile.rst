Profiles
========

Starting from EFB version 2, profiles are introduced
to allow users in need to run multiple EFB instances
simultaneously without affecting each other.

Each profile has its own set of configuration files
a set of channels that share the same code, but
has different data files, so that they can run on
their own.

Profiles are, by default, specific to users. This
means, two users can have profiles in the same
name but operates in isolation.

The default profile name is called ``default``.
To switch to a different profile, specify the
profile name in ``--profile`` flag while starting
EFB.

Start a new profile
-------------------

To create a new profile, you need to create a
directory in the :file:`EFB_DATA_PATH/profiles`, and
create a new configuration file as described in
chapter :doc:`getting-started`.

When everything is configured properly, you are good
to go.