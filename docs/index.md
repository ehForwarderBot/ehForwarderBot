# EH Forwarder Bot

![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)
[![Gitter](https://img.shields.io/gitter/room/blueset/ehForwarderBot.svg)](https://gitter.im/blueset/ehForwarderBot)
[![Telegram support group](https://img.shields.io/badge/Chat-on%20Telegram-blue.svg)](https://telegram.me/efbsupport)
[![Docs: Stable version](https://readthedocs.org/projects/ehforwarderbot/badge/?version=latest)](https://ehforwarderbot.readthedocs.io/en/latest/)
[![Docs: Development version version](https://readthedocs.org/projects/ehforwarderbot/badge/?version=dev)](https://ehforwarderbot.readthedocs.io/en/dev/)
[![tag](https://img.shields.io/github/tag/blueset/ehforwarderbot.svg)](https://github.com/blueset/ehForwarderBot/releases)
[![Average time to resolve an issue](http://isitmaintained.com/badge/resolution/blueset/ehforwarderbot.svg)](http://isitmaintained.com/project/blueset/ehforwarderbot "Average time to resolve an issue")
[![Percentage of issues still open](http://isitmaintained.com/badge/open/blueset/ehforwarderbot.svg)](http://isitmaintained.com/project/blueset/ehforwarderbot "Percentage of issues still open")
[![Codacy grade](https://img.shields.io/codacy/grade/3b2555f9134844e3b01b00700bc43eeb.svg)](https://www.codacy.com/app/blueset/ehForwarderBot)

![EFB](https://images.1a23.com/upload/images/SPET.png)

_Codename_ **EH Forwarder Bot** (EFB) is an extensible chat tunnel framework which allows users to contact people from other chat platforms, and ultimately remotely control their accounts in other platforms.

## Navigation
* [Installation](installation.md)
* [Getting started](getting-started.md)
* [Channels repository](channels-repository.md)
* Your first channel
    * [EFB workflow](workflow.md)
    * [Slave Channel](slave-channel.md)
    * [Master Channel](master-channel.md)
* API Documentation
    * [`EFBMsg`](message.md)
    * [`EFBChannel`](channel.md)
    * [Exceptions](exceptions.md)

## Media coverage
* [Appinn: Send and Receive messages from WeChat on Telegram](http://www.appinn.com/eh-forwarder-bot/)  
  _(EH Forwarder Bot – 在 Telegram 收发「微信」消息)_

## Glossary
* **Channel**: A class that communicates with a chat platform, also known as a plugin.
* **EFB**: abbreviation for EH Forwarder Bot, this project.
* **Master channel**: A channel linked to the platform which directly interact with the user.
* **Plugin**: See "channel".
* **Slave channel**: A channel linked to the platform which is controlled by the user through EFB framework.

## Feel like contributing?
Anyone is welcomed to raise an issue or submit a pull request, just remember to read through and understand the [contribution guideline](CONTRIBUTING.md) before you do so.

## Related articles
* [Idea: Group Chat Tunneling (Sync) with EH Forwarder Bot](https://blog.1a23.com/2017/01/28/Idea-Group-Chat-Tunneling-Sync-with-EH-Forwarder-Bot/)
* [EFB How-to: Send and Receive Messages from WeChat on Telegram (zh-CN)](https://blog.1a23.com/2017/01/09/EFB-How-to-Send-and-Receive-Messages-from-WeChat-on-Telegram-zh-CN/) (Out-dated)  
  _(安装并使用 EFB：在 Telegram 收发微信消息，已过时)_

## License
EFB framework is licensed under [GNU General Public License 3.0](https://www.gnu.org/licenses/gpl-3.0.txt).

```
EH Forwarder Bot: An extensible chat tunneling bot framework.
Copyright (C) 2016 Eana Hufwe
All rights reserved.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
```
