import threading
from . import EFBMsg
from .exceptions import EFBChannelNotFound


class EFBCoordinator:
    """
    Coordinator among channels.

    Attributes:
        profile (str): Name of current profile..
        mutex (threading.Lock): Global interaction thread lock.
        master (ehforwarderbot.EFBChannel): The running master channel object.
        slaves (dict of ehforwarderbot.EFBChannel): Dictionary of running slave channel object.
    """

    def __init__(self, middlewares, profile="default"):
        self.profile = profile
        self.middlewares = middlewares
        self.mutex = threading.Lock()
        self.master = None
        self.slaves = dict()

    def add_channel(self, channel, is_slave=True):
        """
        Register the channel with the shared storage.

        Args:
            channel (EFBChannel): Channel to register
            is_slave (bool, optional): Is slave channel. Default: ``True``.
        """
        if is_slave:
            self.slaves[channel.channel_id] = channel
        else:
            self.master = channel

    def send_message(self, msg):
        """
        Deliver a message to the destination channel.
        
        Args:
            msg (EFBMsg): The message 
        """
        if msg.destination.channel_id == self.master.channel_id:
            self.master.send_message(msg)
        elif msg.destination.channel_id in self.slaves:
            self.slaves[msg.destination.channel_id].send_message(msg)
        else:
            raise EFBChannelNotFound(msg)

    def send_status(self, status):
        # TODO: Go through middlewares
        return self.master.send_status(status)
