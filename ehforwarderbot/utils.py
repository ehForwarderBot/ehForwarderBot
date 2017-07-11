import getpass
import os
from .constants import ChatType


class Emoji:
    GROUP_EMOJI = "👥"
    USER_EMOJI = "👤"
    SYSTEM_EMOJI = "💻"
    UNKNOWN_EMOJI = "❓"
    LINK_EMOJI = "🔗"

    @staticmethod
    def get_source_emoji(t):
        """
        Get the Emoji for the corresponding chat type.
        
        Args:
            t (ChatType): The chat type.

        Returns:
            str: Emoji string.
        """
        if t == ChatType.User:
            return Emoji.USER_EMOJI
        elif t == ChatType.Group:
            return Emoji.GROUP_EMOJI
        elif t == ChatType.System:
            return Emoji.SYSTEM_EMOJI
        else:
            return Emoji.UNKNOWN_EMOJI


def extra(name, desc):
    """
    Decorator for slave channel's "extra functions" interface.
    
    Args:
        name (str): A human readable name for the function.
        desc (str): A short description and usage of it. Use 
            `{function_name}` in place of the function name
            in the description.

    Returns:
        The decorated method.
    """

    def attr_dec(f):
        f.__setattr__("extra_fn", True)
        f.__setattr__("name", name)
        f.__setattr__("desc", desc)
        return f

    return attr_dec


def get_base_path():
    """
    Get the base data path for EFB. This is defined by the environment
    variable ``EFB_DATA_PATH``.
    
    When ``EFB_DATA_PATH`` is defined, the path is constructed by
    ``$EFB_DATA_PATH/$USERNAME``. By default, this gives
    ``~/.ehforwarderbot``.
    
    This method creates the queried path if not existing.
    
    Returns:
        str: The base path.
    """
    base_path = os.environ.get("EFB_DATA_PATH", None)
    if base_path:
        base_path = os.path.join(base_path, getpass.getuser(), "")
    else:
        base_path = os.path.expanduser("~/.ehforwarderbot/")
    os.makedirs(base_path, exist_ok=True)
    return base_path


def get_data_path(channel_id, profile='default'):
    """
    Get the path for channel data.
    
    This method creates the queried path if not existing.
    
    Args:
        channel_id (str): Channel ID
        profile (str, optional): Profile name. Default: ``'default'``

    Returns:
        str: The data path of selected channel.
    """
    base_path = get_base_path()
    data_path = os.path.join(base_path, profile, channel_id, "")
    os.makedirs(data_path, exist_ok=True)
    return data_path


def get_config_path(channel_id=None, ext='yaml', profile='default'):
    """
    Get path for configuration file. Defaulted to
    ``~/.ehforwarderbot/profiles/profile_name/channel_id/config.yaml``.
    
    This method creates the queried path if not existing. The config file will 
    not be created, however.
    
    Args:
        channel_id (str): Channel ID.
        ext (:obj:`str`, optional): Extension name of the config file.
            Defaulted to ``"yaml"``.
        profile (str, optional): Profile name. Default: ``'default'``

    Returns:
        str: The path to the configuration file.
    """
    base_path = get_base_path()
    if channel_id:
        config_path = get_data_path(channel_id)
    else:
        config_path = os.path.join(base_path, profile)
    os.makedirs(config_path, exist_ok=True)
    return os.path.join(config_path, "config.%s" % ext)


def get_cache_path(channel, profile='default'):
    """
    Get path for the channel cache directory. Defaulted to
    ``~/.ehforwarderbot/.cache/profile_name/channel_id``.
    
    This can be defined by the environment variable ``EFB_CACHE_PATH``.
    When defined, the cache path is directed to 
    ``$EFB_CACHE_PATH/username/profile_name/channel_id``.
    
    This method creates the queried path if not existing.
    
    Args:
        channel (str): Channel ID.
        profile (str, optional): Profile name. Default: ``'default'``

    Returns:
        str: Cache path.
    """
    base_path = os.environ.get("EFB_CACHE_PATH", None)
    if base_path:
        base_path = os.path.join(base_path, getpass.getuser(), profile, channel, "")
    else:
        base_path = os.path.expanduser(
            os.path.join(os.path.expanduser("~/.ehforwarderbot/.cache/"), profile, channel, ""))
    os.makedirs(base_path, exist_ok=True)
    return base_path


def get_custom_channel_path():
    """
    Get the path for custom channels

    Returns:
        str: The path.
    """
    channel_path = os.path.join(get_base_path(), "plugins")
    os.makedirs(channel_path, exist_ok=True)
    return channel_path
