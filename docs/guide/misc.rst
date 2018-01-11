Miscellaneous
=============

Logging
-------

In complex modules, you should have detailed logs in
DEBUG level and maybe INFO level, and all your log
handlers should follow that of the root logger, which
is controlled by the framework. This could be helpful
when for you to locate issues reported by users.