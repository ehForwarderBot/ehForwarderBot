# EFB WeChat Slave Channel

EFB WeChat Slave (EWS) is a slave channel for EFB based on [ItChat](https://github.com/littlecodersh/ItChat) and WeChat Web <span style="font-size: 0.5em;">(rev.eng.)</span> API.

## Specs
* Unique name: `eh_wechat_slave`
* Import path: `plugins.eh_wechat_slave`
* Class name: `WeChatChannel`

## Installation
### Dependencies
#### Python dependencies
```
itchat
pymagic
pillow
xmltodict
```
!!! note
    Please refer to [Pillow documentation](https://pillow.readthedocs.io/en/3.0.x/installation.html) for details on installing Pillow.

#### Non-python dependencies
```
libmagic
```
and all other required by Pillow.

### Configuration
* Copy `eh_wechat_slave.py` to "plugins" directory  
  _May not be necessary as it's bundled in EFB_
* Append `("plugins.we_wechat_slave", "WeChatChannel")` to `slave_chanels` list in `config.py`
* No other configuration is required

### Start up
* Scan QR code with your *mobile WeChat client*, then tap "Accept", if required.

## Feature availability
### Supported message types
* TO WeChat
    * Text
    * Image (Sticker sent as Image)
    * File
    * Video
    * Audio (as file)
* FROM WeChat
    * Text
    * Image
    * Sticker
    * Video
    * Location
    * Voice
    * Link
    * Card
    * File
    * System notices

### Command messages, Extra Functions
* Add "Card" as friend or accept friend request
* Change "alias" of friends
* Get friend list and force refresh

## FAQ
* **How do I log in to another WeChat Account?**  
  Please remove the `storage/eh_wechat_slave.pkl` file in the EFB root directory, and restart EFB for QR code scanning.
* **Can I log in 2 WeChat accounts concurrently?**  
  No. The feature is not yet available to EWS.
* **How stable is EWS?**  
  EWS relies on the upstream project [ItChat](https://github.com/littlecodersh/ItChat) and WeChat Web protocol. According to [ItChat FAQ](https://itchat.readthedocs.io/zh/latest/FAQ/): the connection can be stable for months, provided you:
  * have a stable internet connection,
  * **keep your WeChat account accessible on a mobile device, (Android, iOS, etc).**

## Known issues
* Random disconnection may occur occasionally due to the limit of protocol.
* Copyright protected sticker sets are not available to Web WeChat, leading to an empty sticker file to be delivered.
* Chat linking may be unstable sometime due to the limit of API.

!!! note "Technical detail"
    WeChat does not provide a stable chat identifier, so hash of the name of a user is used for the chat identifier. This may cause 2 issues:

    * Chat is no longer traceable when its name is changed.
    * Conflict and mis-delivery may happen when 2 users share the same name.


## Experimental flags
The following flags are experimental features, may change, break, or disappear at any time. Use at your own risk.

Flags can be enabled in the `flags` key of the configuration dict, e.g.:

```python
eh_wechat_slave = {
    "flags": {
        "flag_name": "flag_value"
    }
}
```

* `refresh_friends` _(bool)_  [Default: `False`]  
  Always refresh chat lists when asked. (Except from the extra function.)
* `uid_order` _(list of str)_  [Default: `["NickName"]`]  
  Fallback order of resolving `uid` from WeChat user info. Highest priority goes to index 0. The list **MUST** be non empty with only values below, and the last element associate to a rather stable and available value for most chats, if not all of them.  
  Available values: _(U, G, M means the value is available to users, groups, and group members respectively)_
    * `"NickName"`: [UGM] Name of the user/group
    * `"alias"`: [UM] Alias of the user
    * `"uin"`: [UG] WeChat Unique Identifier for all chats, **Not always available**.  
      Only recommended for those with "Uin rate" higher than 90% in most cases. Check Uin rate with the `check_uin` command.
* `first_link_only` _(bool)_  [Default: `False`]  
  Send only the first links from MPS messages with multiple links. Each link is sent as separate message by default.
* `max_quote_length` _(int)_  [Default: `-1`]  
  Maximum length of text for quotation messages. Set to 0 to fully disable quotation. Set to -1 to always quote full message.
* `qr_reload` _(str)_  [Default: `"master_qr_code"`]  
  Method to display QR code during reauthentication.  
  Available values:
    * `"console_qr_code"`: QR code is printed to the console or log, depend on the logger setting.
    * `"master_qr_code"`: QR code is sent to the master channel as system message.
  !!! note
      The QR code refreshes every 5 to 10 seconds, be aware that sending system messages may lead to flood of message in your conversation.
* `on_log_out` _(str)_  [Default: `"command"`]  
  Behavior when WeChat server logs out the user.  
    Available values:
    * `"idle"`: Notify the user, then do nothing.
    * `"reauth"`: Notify the user, then immediately start reauthentication.
    * `"command"`: Notify the user, then send the user a command message to trigger reauthentication process.
