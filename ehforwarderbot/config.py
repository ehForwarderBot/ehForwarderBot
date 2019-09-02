# coding=utf-8

import sys
from typing import Dict, Any

from ruamel.yaml import YAML
from typing_extensions import Final

from . import utils, coordinator
from .channel import EFBChannel
from .constants import ChannelType
from .middleware import EFBMiddleware

OPTIONAL_DEFAULTS: Final[Dict[str, Any]] = {
    "logging": {},
    "telemetry": ''
}

_ = coordinator.translator.gettext


__all__ = ["load_config"]


def load_config() -> Dict[str, Any]:
    # Include custom channels
    custom_channel_path = str(utils.get_custom_modules_path())
    if custom_channel_path not in sys.path:
        sys.path.insert(0, custom_channel_path)

    conf_path = utils.get_config_path()
    if not conf_path.exists():
        raise FileNotFoundError(_("Config File does not exist. ({})").format(conf_path))
    with conf_path.open() as f:
        data: Dict[str, Any] = OPTIONAL_DEFAULTS.copy()
        data.update(YAML().load(f))

        # Verify configuration

        # - Master channel
        master_channel_id = data.get("master_channel", None)
        if not master_channel_id:
            raise ValueError(_("Master Channel is not specified in the profile config."))
        elif not isinstance(master_channel_id, str):
            raise ValueError(_("Master Channel ID is expected to be a string, but "
                               "\"{0}\" is of type {1}.").format(master_channel_id, type(master_channel_id)))
        channel = utils.locate_module(data['master_channel'], 'master')
        if not channel:
            raise ValueError(_("\"{}\" is not found.").format(master_channel_id))
        if not issubclass(channel, EFBChannel):
            raise ValueError(_("\"{0}\" is not a channel, but a {1}.").format(master_channel_id, channel))
        if not channel.channel_type == ChannelType.Master:
            raise ValueError(_("\"{0}\" is not a master channel, but a {1}.")
                             .format(master_channel_id, channel.channel_type))

        # - Slave channels
        slave_channels_list = data.get("slave_channels", None)
        if not slave_channels_list:
            if not master_channel_id:
                raise ValueError(_("Slave Channels are not specified in the profile config."))
        elif not isinstance(slave_channels_list, list):
            raise ValueError(_("Slave Channel IDs are expected to be a list, but {} is found.")
                             .format(slave_channels_list))
        for i in slave_channels_list:
            channel = utils.locate_module(i, 'slave')
            if not channel:
                raise ValueError(_("\"{}\" is not found.").format(master_channel_id))
            if not issubclass(channel, EFBChannel):
                raise ValueError(_("\"{0}\" is not a channel, but a {1}.").format(master_channel_id, channel))
            if not channel.channel_type == ChannelType.Slave:
                raise ValueError(_("\"{0}\" is not a slave channel, but a {1}.")
                                 .format(master_channel_id, channel.channel_type))

        # - Middlewares
        middlewares_list = data.get("middlewares", None)
        if middlewares_list is not None:
            if not isinstance(middlewares_list, list):
                raise ValueError(_("Middleware IDs must be a list, but a {} is found.")
                                 .format(type(middlewares_list)))
            for i in middlewares_list:
                middleware = utils.locate_module(i, 'middleware')
                if not middleware:
                    raise ValueError(_("\"{}\" is not found.").format(i))
                if not issubclass(middleware, EFBMiddleware):
                    raise ValueError(_("\"{0}\" is not a middleware, but a {1}.")
                                     .format(i, middleware))
        else:
            data['middlewares'] = list()
    return data
