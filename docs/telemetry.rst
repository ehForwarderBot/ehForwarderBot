Telemetry / Error Tracking
==========================

If you want to enable telemetry / error tracking / log analysis to help
us make EFB better, you can install EFB with optional ``telemetry`` option.

.. code-block:: bash

    pip3 install --update ehforwarderbot[telemetry]

And then, enable in the config file under the name
``telemetry``. There are 2 options you can choose from.

- Exception only: Send only exceptions and stack trace to us.
- Exception log: Send verbose log to us alongside exceptions.
- Full log: Send the full verbose log content and what's
  send in previous modes.

To enable "exception only" mode, append the following line to the
config file:

.. code-block:: yaml

    telemetry: I agree.

To enable "Exception log" mode, append the following line to the
config file:

.. code-block:: yaml

    telemetry: I agree to surrender my immortal soul.

To enable "Full log" mode, append the following line to the
config file:

.. code-block:: yaml

    telemetry: I agree to surrender my immortal soul and endless knowledge.


For more details about what telemetry service we are using,
privacy policies, and how we are collecting information through
this, you can visit `1A23 Telemetry GitHub Repository`_ for more
details.

.. _1A23 Telemetry GitHub Repository: https://github.com/blueset/1a23-telemetry