EFBMiddleware
=============

.. autoclass:: ehforwarderbot.EFBMiddleware
    :members:

About Middleware ID
-------------------

With the introduction of instance IDs, it is required to use the
``self.middleware_id`` or equivalent instead of any hard-coded
ID or constants while referring to the middleware (e.g. while
retrieving the path to the configuration files, etc).