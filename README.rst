EH Forwarder Bot
================

.. image:: https://img.shields.io/badge/Python->%3D%203.6-blue.svg
   :alt: Python >= 3.6
   :target: https://www.python.org/
.. image:: https://img.shields.io/gitter/room/blueset/ehForwarderBot.svg?logo=gitter-white
   :alt: Gitter
   :target: https://gitter.im/blueset/ehForwarderBot
.. image:: https://img.shields.io/badge/-Telegram-blue.svg?logo=data:image/svg%2Bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI%2BPHBhdGggZmlsbD0iI2ZmZiIgZD0iTTkuNzgsMTguNjVMMTAuMDYsMTQuNDJMMTcuNzQsNy41QzE4LjA4LDcuMTkgMTcuNjcsNy4wNCAxNy4yMiw3LjMxTDcuNzQsMTMuM0wzLjY0LDEyQzIuNzYsMTEuNzUgMi43NSwxMS4xNCAzLjg0LDEwLjdMMTkuODEsNC41NEMyMC41NCw0LjIxIDIxLjI0LDQuNzIgMjAuOTYsNS44NEwxOC4yNCwxOC42NUMxOC4wNSwxOS41NiAxNy41LDE5Ljc4IDE2Ljc0LDE5LjM2TDEyLjYsMTYuM0wxMC42MSwxOC4yM0MxMC4zOCwxOC40NiAxMC4xOSwxOC42NSA5Ljc4LDE4LjY1WiIgLz48L3N2Zz4=
   :alt: Telegram
   :target: https://telegram.me/efbsupport
.. image:: https://readthedocs.org/projects/ehforwarderbot/badge/?version=latest
   :alt: Documentation
   :target: https://ehforwarderbot.readthedocs.io/en/latest/
.. image:: https://img.shields.io/pypi/v/ehforwarderbot.svg
   :alt: PyPI release
   :target: https://pypi.org/project/ehforwarderbot/
.. image:: https://img.shields.io/pypi/dm/ehforwarderbot.svg
   :alt: Downloads per month
   :target: https://pypi.org/project/ehforwarderbot/
.. image:: https://img.shields.io/codacy/grade/3b2555f9134844e3b01b00700bc43eeb.svg
   :alt: Codacy grade
   :target: https://www.codacy.com/app/blueset/ehForwarderBot
.. image:: https://d322cqt584bo4o.cloudfront.net/ehforwarderbot/localized.svg
   :alt: Translate this project
   :target: https://crowdin.com/project/ehforwarderbot/


.. image:: https://github.com/blueset/ehForwarderBot/blob/master/banner.png
   :alt: Banner


*Codename* **EH Forwarder Bot** (EFB) is an extensible
chat tunneling framework allowing users to contact
people from multiple chat platforms and remotely
control their accounts in one stop.

For tips, tricks and community contributed articles, see
`project wiki`_.

.. _project wiki: https://github.com/blueset/ehForwarderBot/wiki

v2.0 beta release
------------------
This is a beta release of EFB version 2 for test only.
Framework API may subject to change.

`Documentation`_.

Getting Started
---------------

1. Install the framework::

    pip3 install ehforwarderbot

2. `Install and enable channels`_ from the `channels repository`_.

3. Launch EFB::

    ehforwarderbot

Feel like contributing?
-----------------------

Everyone is welcomed to raise an issue or submit a pull request,
just remember to read through and follow the
contribution guideline before you do so.

Related articles
----------------

* `Idea: Group Chat Tunneling (Sync) with EH Forwarder Bot`_
* `What’s so new in EH Forwarder Bot 2 (and its modules)`_

.. _Idea\: Group Chat Tunneling (Sync) with EH Forwarder Bot: https://blog.1a23.com/2017/01/28/Idea-Group-Chat-Tunneling-Sync-with-EH-Forwarder-Bot/
.. _What’s so new in EH Forwarder Bot 2 (and its modules): https://blog.1a23.com/2018/02/28/What%E2%80%99s-so-new-in-EH-Forwarder-Bot-2-and-its-modules/


License
-------

EFB framework is licensed under `GNU Affero General Public License 3.0`_ or
later versions::

    EH Forwarder Bot: An extensible chat tunneling bot framework.
    Copyright (C) 2016 - 2019 Eana Hufwe, and the EH Forwarder Bot contributors
    All rights reserved.

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
Translation support
-------------------

EFB supports translated user interface prompts,
by setting the locale environmental variable (``LANGUAGE``,
``LC_ALL``, ``LC_MESSAGES`` or ``LANG``) to one of our
`supported languages`_. Our documentation is also available in different
languages. You can help to translate
this project into your languages on `our Crowdin page`_.

.. _supported languages: https://crowdin.com/project/ehforwarderbot/
.. _our Crowdin page: https://crowdin.com/project/ehforwarderbot/

.. _Install and enable channels: https://ehforwarderbot.readthedocs.io/en/latest/getting-started.html
.. _channels repository: https://github.com/blueset/ehForwarderBot/wiki/Channels-Repository
.. _Documentation: https://ehforwarderbot.readthedocs.io/
.. _GNU Affero General Public License 3.0: https://www.gnu.org/licenses/agpl-3.0.txt
