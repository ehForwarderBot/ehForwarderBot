# EH Forwarder Bot

![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)

![EFB](https://images.1a23.com/upload/images/SPET.png)

_Codename_ **EH Forwarder Bot** (EFB) is an extensible chat tunnel framework which allows users to contact people from other chat platforms, and ultimately remotely control their accounts in other platforms.

## Navigation
* [Installation](installation.md)
* [Getting started](getting-started.md)
* [Plugins repository](plugins-repository.md)
* Your first channel
    * [EFB workflow](workflow.md)
    * [Slave Channel](slave-channel.md)
    * [Master Channel]() _(TODO)_
* API Documentation
    * [`EFBMsg`](message.md)
    * [`EFBChannel`]() _(TODO)_
    * [Exceptions]() _(TODO)_

## Glossary
* **Channel**: A class that communicates with a chat platform, also known as a plugin.
* **EFB**: abbreviation for EH Forwarder Bot, this project.
* **Master channel**: A channel linked to the platform which directly interact with the user.
* **Plugin**: See "channel".
* **Slave channel**: A channel linked to the platform which is controlled by the user through EFB framework.

## Feel like contributing?
Anyone is welcomed to raise an issue or submit a pull request, just remember to read through and understand the [contribution guideline](CONTRIBUTION.md) _(TODO)_ before you do so.

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
