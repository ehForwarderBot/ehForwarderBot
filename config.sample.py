# ##############################
#  Configs for EH Forwarder Bot
# ##############################
#
#  Basic settings
# ----------------
#
# Master/Slave Channels
#
# Master channel:
# The channel that is mainly used to view/manage messages
# from slave channels.
# Currently only 1 master channel is supported.
#
# Slave channels:
# Channels that are hosted on the server and being delivered
# to and from the master channel.
# You may have more than 1 slave channel.
#

master_channel = 'plugins.eh_telegram_master', 'TelegramChannel'
slave_channels = [('plugins.eh_wechat_slave', 'WeChatChannel')]

#
#  Plugin specific settings
# --------------------------
# Plugin specific settings should be written below in the format of:
# `channel_name = {"key1": "value1", "key2": "value2"}`
# Please refer to docs of individual plugin for details
#

eh_telegram_master = {
    "token": "12345678:QWFPGJLUYarstdheioZXCVBKM",
    "admins": [0],
    "bing_speech_api": ["3243f6a8885a308d313198a2e037073", "2b7e151628ae082b7e151628ae08"],
    "baidu_speech_api": {
        "app_id": 0,
        "api_key": "3243f6a8885a308d313198a2e037073",
        "secret_key": "2b7e151628ae082b7e151628ae08"
    }
}
