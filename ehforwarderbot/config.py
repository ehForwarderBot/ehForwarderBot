# coding=utf-8

import os

import sys
from ruamel.yaml import YAML
from typing import Dict, Any
from . import utils
from .channel import EFBChannel
from .middleware import EFBMiddleware
from .constants import ChannelType


__all__ = ["load_config"]


def load_config() -> Dict[str, Any]:
    # Include custom channels
    custom_channel_path = utils.get_custom_modules_path()
    if custom_channel_path not in sys.path:
        sys.path.insert(0, custom_channel_path)

    conf_path = utils.get_config_path()
    if not os.path.exists(conf_path):
        raise FileNotFoundError("Config File does not exist. (%s)" % conf_path)
    with open(conf_path) as f:
        data = YAML().load(f)

        # Verify configuration

        # - Master channel
        if not isinstance(data.get("master_channel", None), str):
            raise ValueError("Master Channel path must be a string.")
        channel = utils.locate_module(data['master_channel'], 'master')
        if not channel:
            raise ValueError("\"%s\" is not found." % data['master_channel'])
        if not issubclass(channel, EFBChannel):
            raise ValueError("\"%s\" is not a channel." % data['master_channel'])
        if not channel.channel_type == ChannelType.Master:
            raise ValueError("\"%s\" is not a master channel." % data['master_channel'])

        # - Slave channels
        if not isinstance(data.get("slave_channels", None), list):
            raise ValueError("Slave Channel paths must be a list.")
        for i in data['slave_channels']:
            channel = utils.locate_module(i, 'slave')
            if not channel:
                raise ValueError("\"%s\" is not found." % i)
            if not issubclass(channel, EFBChannel):
                raise ValueError("\"%s\" is not a channel." % i)
            if not channel.channel_type == ChannelType.Slave:
                raise ValueError("\"%s\" is not a slave channel." % i)

        # - Middlewares
        if data.get("middlewares", None) is not None:
            if not isinstance(data.get("middlewares"), list):
                raise ValueError("Middleware paths must be a list")
            for i in data['middlewares']:
                middleware = utils.locate_module(i, 'middleware')
                if not middleware:
                    raise ValueError("\"%s\" is not found." % i)
                if not issubclass(middleware, EFBMiddleware):
                    raise ValueError("\"%s\" is not a middleware." % i)
        else:
            data['middlewares'] = list()
    return data
