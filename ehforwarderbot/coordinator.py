# coding=utf-8

"""
Coordinator among channels.

Attributes:
    profile (str): Name of current profile..
    mutex (threading.Lock): Global interaction thread lock.
    master (EFBChannel): The running master channel object.
    slaves (Dict[str, EFBChannel]): Dictionary of running slave channel object.
        Keys are the unique identifier of the channel.
    middlewares (List[EFBMiddleware]): List of middlewares
"""

import threading
from gettext import NullTranslations
from typing import List, Dict, Optional, cast, TYPE_CHECKING, Union

from .channel import EFBChannel
from .constants import ChannelType
from .exceptions import EFBChannelNotFound
from .middleware import EFBMiddleware
from .types import ModuleID

if TYPE_CHECKING:
    from . import EFBMsg
    from .status import EFBStatus

profile: str = "default"
"""Current running profile name"""

mutex: threading.Lock = threading.Lock()
"""Mutual exclusive lock for user interaction through CLI interface"""

master: EFBChannel  # late init
"""The instance of the master channel."""

slaves: Dict[ModuleID, EFBChannel] = dict()
"""Instances of slave channels. Keys are the channel IDs."""

middlewares: List[EFBMiddleware] = list()
"""Instances of middlewares. Sorted in the order of execution."""

master_thread: Optional[threading.Thread] = None
"""The thread running poll() of the master channel."""

slave_threads: Dict[ModuleID, threading.Thread] = dict()
"""Threads running poll() from slave channels. Keys are the channel IDs."""

translator: NullTranslations = NullTranslations()
"""Internal GNU gettext translator."""


def add_channel(channel: EFBChannel):
    """
    Register the channel with the coordinator.

    Args:
        channel (EFBChannel): Channel to register
    """
    global master, slaves
    if isinstance(channel, EFBChannel):
        if channel.channel_type == ChannelType.Slave:
            slaves[channel.channel_id] = channel
        else:
            master = channel
    else:
        raise TypeError("Channel instance is expected")


def add_middleware(middleware: EFBMiddleware):
    """
    Register a middleware with the coordinator.

    Args:
        middleware (EFBMiddleware): Middleware to register
    """
    global middlewares
    if isinstance(middleware, EFBMiddleware):
        middlewares.append(middleware)
    else:
        raise TypeError("Middleware instance is expected")


def send_message(msg: 'EFBMsg') -> Optional['EFBMsg']:
    """
    Deliver a message to the destination channel.

    Args:
        msg (EFBMsg): The message

    Returns:
        The message sent by the destination channel,
        includes the updated message ID from there.
        Returns ``None`` if the message is not sent.
    """
    global middlewares, master, slaves

    if msg is None:
        return

    # Go through middlewares
    for i in middlewares:
        m = i.process_message(msg)
        if m is None:
            return None
        # for mypy type check
        assert m is not None
        msg = m

    msg.verify()

    if msg.deliver_to.channel_id == master.channel_id:
        return master.send_message(msg)
    elif msg.deliver_to.channel_id in slaves:
        return slaves[msg.deliver_to.channel_id].send_message(msg)
    else:
        raise EFBChannelNotFound(msg)


def send_status(status: 'EFBStatus'):
    """
    Deliver a message to the destination channel.

    Args:
        status (EFBStatus): The status
    """
    global middlewares, master
    if status is None:
        return

    s: 'Optional[EFBStatus]' = status

    # Go through middlewares
    for i in middlewares:
        s = i.process_status(cast('EFBStatus', s))
        if s is None:
            return

    status = cast('EFBStatus', s)

    status.verify()

    status.destination_channel.send_status(status)


def get_module_by_id(module_id: ModuleID) -> Union[EFBChannel, EFBMiddleware]:
    """
    Return the module instance of a provided module ID
    Args:
        module_id: Module ID, with instance ID if available.

    Returns:
        Module instance requested.

    Raises:
        NameError: When the module is not found.
    """
    try:
        if master.channel_id == module_id:
            return master
    except NameError:
        pass
    if module_id in slaves:
        return slaves[module_id]
    for i in middlewares:
        if i.middleware_id == module_id:
            return i
    raise NameError("Module ID {} is not found".format(module_id))
