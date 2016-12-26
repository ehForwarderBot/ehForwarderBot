# EFB WeChat Slave Channel

EFB WeChat Slave Channel is a slave channel for EFB based on [ItChat](https://github.com/littlecodersh/ItChat) and WeChat Web <span style="font-size: 0.5em;">(rev.eng.)</span> API.

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
  _May not be necessary as it's a built-in plugin of EFB_
* Append `("plugins.we_wechat_slave", "WeChatChannel")` to `slave_chanels` dict in `config.py`
* No other configuration is required

### Start up
* Scan QR code with your *mobile WeChat client*, then tap "Accept", if required.

## Feature availability
### Supported message types
* TO WeChat
    * Text
    * Image (Sticker sent as Image)
    * File
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

## FAQ
* **How do I log in to another WeChat Account?**  
  Please remove the `itchat.pkl` file in the EFB root directory, and restart EFB for QR code scanning.
* **Can I log in 2 WeChat accounts concurrently?**  
  No. The feature is not yet available to EWS.

## Known issues
* Random disconnection may occur occasionally due to the limit of protocol.
* Chat linking may be unstable sometime due to the limit of API.

!!! note "Technical detail"
    WeChat does not provide a stable chat identifier, so hash of the name of a user is used for the chat identifier. This may cause 2 issues:

    * Chat is no longer traceable when its name is changed.
    * Conflict and mis-delivery may happen when 2 users share the same name.
