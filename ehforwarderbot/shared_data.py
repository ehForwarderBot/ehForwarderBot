import queue
import threading


class SharedData:
    """
    Shared data among channels.

    Attributes:
        profile (str): Name of current profile.
        q (dict of MiddlewareQueue): Message queue for each destination channel.
        mutex (threading.Lock): Global interaction thread lock.
        master (EFBChannel): The running master channel object.
        slaves (dict of EFBChannel): Dictionary of running slave channel object.
    """
    def __init__(self, middlewares, profile="default"):
        self.profile = profile
        self.middlewares = middlewares
        self.q = dict()
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
        self.q[channel.channel_id] = MiddlewareQueue(self.middlewares)
        if is_slave:
            self.slaves[channel.channel_id] = channel
        else:
            self.master = channel


class MiddlewareQueue(queue.Queue):
    def __init__(self, middlewares):
        super(MiddlewareQueue, self).__init__()
        self.middlewares = middlewares

    def put(self, item, **kwargs):
        # TODO: Run through all middlewares.
        # Check the message with each middleware for
        #   1. If the middleware accepts the message
        #   2. Replace the message with the processed one.
        #   3. If the message is None'd, abort.
        super(MiddlewareQueue, self).put(item, **kwargs)
