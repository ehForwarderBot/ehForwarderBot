# coding=utf-8

import logging
import os
import pydoc
from pathlib import Path
from typing import Callable

import pkg_resources

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


def get_base_path() -> Path:
    """
    Get the base data path for EFB. This can be defined by the
    environment variable ``EFB_DATA_PATH``.
    
    If ``EFB_DATA_PATH`` is not defined, this gives
    ``~/.ehforwarderbot``.
    
    This method creates the queried path if not existing.
    
    Returns:
        The base path.
    """
    env_data_path = os.environ.get("EFB_DATA_PATH", None)
    if env_data_path:
        base_path = Path(env_data_path).resolve()
    else:
        base_path = Path.home() / ".ehforwarderbot"
    if not base_path.exists():
        base_path.mkdir(parents=True)
    return base_path


def get_data_path(module_id: str) -> Path:
    """
    Get the path for persistent storage of a module.
    
    This method creates the queried path if not existing.
    
    Args:
        module_id (str): Module ID

    Returns:
        The data path of indicated module.
    """
    profile = coordinator.profile
    data_path = get_base_path() / 'profiles' / profile / module_id
    if not data_path.exists():
        data_path.mkdir(parents=True)
    return data_path


def get_config_path(module_id: str = None, ext: str = 'yaml') -> Path:
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
        The path to the configuration file.
    """
    if module_id:
        config_path = get_data_path(module_id)
    else:
        profile = coordinator.profile
        config_path = get_base_path() / 'profiles' / profile
    if not config_path.exists():
        config_path.mkdir(parents=True)
    return config_path / "config.{}".format(ext)


def get_custom_modules_path() -> Path:
    """
    Get the path to custom channels

    Returns:
        The path for custom channels.
    """
    channel_path = get_base_path() / "modules"
    if not channel_path.exists():
        channel_path.mkdir(parents=True)
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
