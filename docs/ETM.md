# EFB Telegram Master
EFB Telegram Master (ETM) is a master channel for EFB based on [`python-telegram-bot`](https://python-telegram-bot.org/) and [Telegram Official Bot API](https://core.telegram.org/bots/api).

## Specs
* Unique name: `eh_telegram_master`
* Import path: `plugins.eh_telegram_master`
* Class name: `TelegramChannel`

## Installation
### Dependencies
#### Python dependencies
```
python-telegram-bot
pymagic
pillow
pydub
moviepy
peewee
```
!!! note
    Please refer to [Pillow documentation](https://pillow.readthedocs.io/en/3.0.x/installation.html) for details on installing Pillow.

#### Non-python dependencies
```
libmagic
ffmpeg
```
and all other required by Pillow.

### Configuration
* Create a bot with [@BotFather](https://telegram.me/botfather). ([Related tutorial](https://core.telegram.org/bots#6-botfather).)
* Set `/setjoingroups` to `Enable`, `/setprivacy` to `Disable`.
* Copy `eh_telegram_master` to "plugins" directory,  
  _May not be necessary as it's a built-in plugin of EFB_
* Set `master_channel = "plugins.eh_telegram_master", "TelegramChannel"` in `config.py`
* Give read and write access to `eh_telegram_master` directory
* Add variable `eh_telegram_master` as follows

```python
eh_telegram_master = {
    "token": "Telegram bot token",
    "admins": [12345678, 87654321],
    "bing_speech_api": ["token1", "token2"],
    "baidu_speech_api": {
        "app_id": 123456,
        "api_key": "API_key",
        "secret_key": "secret_key"
    }
}
```

* `token`: (string) Telegram Bot token issued by BotFather.
* `admins`: (list of int) User IDs of admin.  
  **Only** messages from admins will be processed. All other messages will be discarded.  
  There are several ways obtaining your ID: Send a message to [@JackBot](https://telegram.me/jackbot), [@get_id_bot](https://telegram.me/get_id_bot), [@UserInfoBot](https://telegram.me/userinfobot), or check it with [Plus messenger](http://plusmessenger.org/).  
  _(No guarantee that any of these method works, or keeps your privacy safe. None of them is associated with EFB or its author.)_
* `bing_speech_api`: (list of strings | None) Enable speech recognition services from Bing. List in order of `["token1", "token1"]`.  
  Register from [here](https://www.microsoft.com/cognitive-services/en-us/speech-api). `None` to disable.
* `baidu_speech_api`: (dict | None) Enable speech recognition services from Baidu. Dict keys required: `"app_id" (int)`, `"api_key" (str)`, `"secret_key" (str)`.  
  Register from [here](http://yuyin.baidu.com/). `None` to disable.

### Start up
No extra action required during start up.

## Supported message types (both directions)
* Text (Link as Text)
* Image
* Sticker
* Document
* Video
* Audio (and Voice)
* Location (and Venue)

## Usage
At the beginning, messages from all senders will be sent to the user directly, that means every message  will be mixed in the same conversation. By linking a chat, you can redirect messages from a specific sender to an empty group for a more organized conversation.

In a nutshell, ETM offers the following commands, you can also send it to BotFather for the command list.

```
help - Show commands list.
link - Link a remote chat to a group.
unlink_all - Unlink all remote chats from a group.
chat - Generate a chat head.
recog - Recognize a speech by replying to it.
extra - Access extra functionalities.
```

!!! note "Notice"  
    In case of multiple admins are assigned, they may all send message on your behalf, but only the 0th admin can receive direct message from the bot.

### `/link`: Link a chat
1. Create a new group, invite your bot to the group
2. Send `/link` directly to the bot, then select your preferred slave chat.
3. Tap "Link" and select your new group.  
   _You can also choose to unlink or relink a linked chat from this menu._
4. Tap "Start" at the bottom of your screen, and you should see a success message: "Chat associated."

!!! note "Notice"
    You may introduce other non-ETM admins to the group, however, they:

    * Can read all messages send from the related remote chat;
    * May NOT send message on your behalf.

Also, you can send `/unlink_all` to a group to unlink all remote chats from it.

### Send a message
#### Send to a linked chat
You can send message as you do in a normal Telegram chat.

What is supported:

* Send/forward message in all supported types
* Direct reply to a message
* Send message with inline bot in supported types

What is NOT supported:

* @ reference
* Markdown/HTML formatting
* Messages with unsupported types

#### Send to a non-linked chat
To send a message to a non-linked chat, you should "direct reply" to a message or a "chat head" that is sent from your recipient. Those messages should appear only in the bot conversation.

In a non-linked chat, direct reply will not be delivered to the remote channel, everything else is supported as it does in a linked chat.

#### `/chat`: Chat head
If you want to send a message to a non-linked chat which has not yet sent you a message, you can ask ETM to generate a "chat head". Chat head works similarly to an incoming message, you can reply to it to send messages to your recipient.

Send `/chat` to the bot, and choose a chat from the list. When you see "Reply to this message to send to <chat name> from <channel>", it's ready to go.

!!! tip "Advanced feature: Filtering"
    If you have just too much chats, and being too tired for keep tapping `Next >`, or maybe you just want to find a way to filter out what you're looking for, now ETM has equipped `/chat` and `/list` with filtering feature. Attach your keyword behind, and you can get a filtered result.

    E.g.: `/chat Eana` will give you all chats has the word "Eana".

!!! note "Technical Details"
    The filter query is in fact a regular expression matching. We used Python's `re.search` with flags `re.DOTALL | re.IGNORECASE` in this case, i.e.: `.` matches everything including line breaks, and the query is NOT case-sensitive. Each comparison is done against a specially crafted string which allows you to filter multiple criteria.

        Channel: Dummy Channel
        Name: John Doe
        Alias: Jonny
        ID: john_doe
        Type: User

    > _Type can be either "User" or "Group"_

    Examples:

    * Look for all WeChat groups: `Channel: WeChat.*Type: Group`
    * Look for everyone who has an alias `Name: (.*?)\nAlias: (?!\1)`
    * Look for all entries contain "John" and "Jonny" in any order: `(?=.*John)(?=.*Jonny)"`

### `/extra`: External commands from slave channels ("extra functions")
Some slave channels may provide commands that allows you to remotely control those accounts, and achieve extra functionalities, those commands are called "extra functions". To view the lis of available extra functions, send `/extra` to the bot, you will receive a list of commands available, together with their usages.

Those commands are named like "`/<number>_<command_name>`", and can be called like a Linux/unix CLI utility. (of course, please don't expect piping, etc to be supported)

### `/recog`: Speech recognition
If you have entered a speech recognition service API keys, you can use it to convert speech in voice messages into text.

Reply any voice messages in a conversation with the bot, with the command `/recog`, and the bot will try to convert it to text using those speech recognition services enabled.

If you know the language used in this message, you can also attach the language code to the command for a more precise conversion.

Supported language codes:

Code | Baidu | Bing
---|---|---
en, en-US | English | English (US)
en-GB | - | English (UK)
en-IN | - | English (India)
en-NZ | - | English (New Zealand)
en-AU | - | English (Australia)
en-CA | - | English (Canada)
zh, zh-CN | Mandarin | Mandarin (China Mainland)
zh-TW | - | Mandarin (Taiwan)
zh-HK | - | Mandarin (Hong Kong)
ct | Cantonese | -
de-DE | - | German
ru-RU | - | Russian
ja-JP | - | Japanese
ar-EG | - | Arabic
da-DK | - | Danish
es-ES | - | Spanish (Spain)
es-MX | - | Spanish (Mexico)
fi-FI | - | Finnish
nl-NL | - | Dutch
pt-BR | - | Portuguese (Brazil)
pt-PT | - | Portuguese (Portugal)
ca-ES | - | Catalan
fr-FR | - | French (France)
fr-CA | - | French (Canada)
ko-KR | - | Korean
nb-NO | - | Norwegian
it-IT | - | Italian
sv-SE | - | Swedish

## Known issues
* In rare cases, some messages may take 20 to 35 minutes to be delivered to user. (Upstream library [python-telegram-bot#364](https://github.com/python-telegram-bot/python-telegram-bot/issues/364), said to be fixed in version 6.)
* Too often invitation of the bot to groups will trigger Telegram's anti-spam mechanism. If you see "Could not add user, please try again later", you really need to "try again later". No joking.

## Experimental flags
The following flags are experimental features, may change, break, or disappear at any time. Use at your own risk.

Flags can be enabled in the `flags` key of the configuration dict, e.g.:

```python
eh_telegram_master = {
    # ...
    "flags": {
        "flag_name": "flag_value"
    }
}
```

* `no_conversion` _(bool)_  [Default: `False`]
  Disable audio conversion, send all audio file as is, and let Telegram to handle it.
* `join_msg_threshold_secs` _(int)_ [Default: `15`]  
  Threshold in seconds for message joining. Messages sent from the same person from the same chat between the threshold time will be joined together.  
  _Only works in linked chats._
* `chats_per_page` _(int)_ [Default: `10`]  
  Number of chats shown in when choosing for `/chat` and `/link` command. An overly large value may lead to malfunction of such commands.
* `text_as_html` _(bool)_ [Default: `False`]  
  Parse all text messages as Telegram HTML. Tags supported: `a`, `b`, `strong`, `i`, `em`, `code`, `pre`.
* `multiple_slave_chats` _(bool)_  [Default: `False`]  
  Link more than one remote chat to one Telegram group. Send and reply as you do with an unlinked chat.
