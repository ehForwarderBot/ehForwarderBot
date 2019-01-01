# coding=utf-8

import getpass
import os
import pydoc
import logging

import pkg_resources
from typing import Callable
from . import coordinator


def extra(name: str, desc: str) -> Callable:
    """
    Decorator for slave channel's "additional features" interface.

    Args:
        name (str): A human readable name for the function.
        desc (str): A short description and usage of it. Use
            ``{function_name}`` in place of the function name
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


def get_base_path() -> str:
    """
    Get the base data path for EFB. This can be defined by the
    environment variable ``EFB_DATA_PATH``.
    
    If ``EFB_DATA_PATH`` is not defined, this gives
    ``~/.ehforwarderbot``.
    
    This method creates the queried path if not existing.
    
    Returns:
        str: The base path.
    """
    base_path = os.environ.get("EFB_DATA_PATH", None)
    if base_path:
        base_path = os.path.abspath(base_path)
    else:
        base_path = os.path.expanduser(os.path.join("~", ".ehforwarderbot"))
    os.makedirs(base_path, exist_ok=True)
    return base_path


def get_data_path(module_id: str):
    """
    Get the path for permanent storage of a module.
    
    This method creates the queried path if not existing.
    
    Args:
        module_id (str): Module ID

    Returns:
        str: The data path of indicated module.
    """
    profile = coordinator.profile
    base_path = get_base_path()
    data_path = os.path.join(base_path, 'profiles', profile, module_id, "")
    os.makedirs(data_path, exist_ok=True)
    return data_path


def get_config_path(module_id: str = None, ext: str = 'yaml') -> str:
    """
    Get path for configuration file. Defaulted to
    ``~/.ehforwarderbot/profiles/profile_name/channel_id/config.yaml``.
    
    This method creates the queried path if not existing. The config file will
    not be created, however.
    
    Args:
        module_id (str): Module ID.
        ext (Optional[Str]): Extension name of the config file.
            Defaulted to ``"yaml"``.

    Returns:
        str: The path to the configuration file.
    """
    base_path = get_base_path()
    profile = coordinator.profile
    if module_id:
        config_path = get_data_path(module_id)
    else:
        config_path = os.path.join(base_path, 'profiles', profile)
    os.makedirs(config_path, exist_ok=True)
    return os.path.join(config_path, "config.%s" % ext)


def get_custom_modules_path() -> str:
    """
    Get the path to custom channels

    Returns:
        str: The path.
    """
    channel_path = os.path.join(get_base_path(), "modules")
    os.makedirs(channel_path, exist_ok=True)
    return channel_path


def locate_module(module_id: str, module_type: str = None):
    """
    Locate module by module ID

    Args:
        module_id: Module ID
        module_type: Type of module, one of ``'master'``, ``'slave'`` and ``'middleware'``
    """

    entry_point = None

    if module_type:
        entry_point = 'ehforwarderbot.%s' % module_type

    module_id = module_id.split('#', 1)[0]

    if entry_point:
        for i in pkg_resources.iter_entry_points(entry_point):
            if i.name == module_id:
                return i.load()

    return pydoc.locate(module_id)


class LogLevelFilter:
    def __init__(self, min_level=float('-inf'), max_level=float('inf')):
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord):
        return self.min_level <= record.levelno <= self.max_level
