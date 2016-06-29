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

master_channel = 'plugins.tg', 'TelegramChannel'
slave_channels = [('plugins.wechat', 'WeChatChannel')]

#
#  Plugin specific settings
# --------------------------
# Plugin specific settings should be written below in the format of:
# `channel_name = {"key1": "value1", "key2": "value2"}`
# Please refer to docs of individual plugin for details
#
