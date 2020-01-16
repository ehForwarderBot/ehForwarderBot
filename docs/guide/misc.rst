Miscellaneous
=============

Logging
-------

In complex modules, you should have detailed logs in
DEBUG level and optionally INFO level. All your log
handlers SHOULD follow that of the root logger, which
is controlled by the framework. This could be helpful
when for you to locate issues reported by users.

Vendor-specifics
----------------

If you are going to include vendor specific information
in messages and/or chats, please make your effort to
document them in your README or documentation, so that
other developers can refer to it when adapting your
module.

Threading
---------

All channels are RECOMMENDED a separate thread while
processing a new message, so as to prevent unexpectedly
long thread blocking.

We are also considering to move completely to asynchronous
programming when most channels are ready for the change.


Static type checking
--------------------

EH Forwarder Bot is fully labeled in the Python 3 type
hint notations. Since sometimes maintaining a module with
high complexity could be difficult, we RECOMMEND you to
type your module too and use tools like mypy_ to check your
code statically.

.. _mypy: https://github.com/python/mypy
