"""
Coordinator among channels.

Attributes:
    profile (str): Name of current profile..
    mutex (threading.Lock): Global interaction thread lock.
    master (ehforwarderbot.EFBChannel): The running master channel object.
    slaves (dict[str: ehforwarderbot.EFBChannel]): Dictionary of running slave channel object.
        Keys are the unique identifier of the dictionary.
    middlewares (list[EFBMiddleware]): List of middlewares
"""

import threading
from typing import List, Dict

from . import EFBMsg
from .channel import EFBChannel
from .constants import ChannelType
from .exceptions import EFBChannelNotFound
from .middleware import EFBMiddleware
from .status import EFBStatus

profile: str = "default"
mutex: threading.Lock = threading.Lock()
master: EFBChannel = None
slaves: Dict[str, EFBChannel] = dict()
middlewares: List[EFBMiddleware] = list()


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


def send_message(msg: EFBMsg):
    """
    Deliver a message to the destination channel.

    Args:
        msg (EFBMsg): The message
    """
    global middlewares, master, slaves
    if msg is None:
        return

    # Go through middlewares
    for i in middlewares:
        msg = i.process_message(msg)
        if msg is None:
            return

    if msg.destination.channel_id == master.channel_id:
        master.send_message(msg)
    elif msg.destination.channel_id in slaves:
        slaves[msg.destination.channel_id].send_message(msg)
    else:
        raise EFBChannelNotFound(msg)


def send_status(status: EFBStatus):
    """
    Deliver a message to the destination channel.

    Args:
        status (EFBStatus): The status
    """
    global middlewares, master
    if status is None:
        return

    # Go through middlewares
    for i in middlewares:
        status = i.process_status(status)
        if status is None:
            return

    master.send_status(status)
