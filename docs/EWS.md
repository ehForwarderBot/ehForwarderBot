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
> **Note**  
> Please refer to [Pillow documentation](https://pillow.readthedocs.io/en/3.0.x/installation.html) for details on installing Pillow.

#### Non-python dependencies
```
libmagic
```
and all other required by Pillow.

### Configuration
* Copy `eh_wechat_slave.py` to "plugins" directory  
  _May not be necessary as it's a built-in plugin of EFB_
* Append `("plugins.we_wechat_slave", "WeChatChannel")` to `slaves` dict in `config.py`
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
* **I want to report a bug.**  
  **I have some suggestions.**  
  **Can I submit a pull request?**  
  All bug reports, suggestions and pull requests are welcomed. Please read through and understand the [Contribution guideline](CONTRIBUTING.md) before submitting.
