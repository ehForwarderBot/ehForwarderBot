import threading
import logging
import argparse
import sys
import signal
import pydoc
from . import config, utils
from .__version__ import __version__
from .channel import EFBChannel
from .middleware import EFBMiddleware
from . import coordinator

if sys.version_info < (3, 5):
    raise Exception("Python 3.5 or higher is required. Your version is %s." % sys.version)

parser = argparse.ArgumentParser(description="EH Forwarder Bot is an extensible chat tunnel framework which allows "
                                             "users to contact people from other chat platforms, and ultimately "
                                             "remotely control their accounts in other platforms.",
                                 epilog="GitHub: https://github.com/blueset/ehForwarderBot")


def stop_gracefully(sig, stack):
    logger = logging.getLogger(__name__)
    if isinstance(coordinator.master, EFBChannel):
        coordinator.master.stop_polling = True
        logger.debug("Stop signal sent to master: %s" % coordinator.master.channel_name)
        while coordinator.master_thread.is_alive():
            pass
    for i in coordinator.slaves:
        if isinstance(coordinator.slaves[i], EFBChannel):
            coordinator.slaves[i].stop_polling = True
            logger.debug("Stop signal sent to slave: %s" % coordinator.slaves[i].channel_name)
            while coordinator.slave_threads[i].is_alive():
                pass
    sys.exit(0)


def init():
    """
    Initialize all channels.
    """

    logger = logging.getLogger(__name__)

    # Include custom channels
    custom_channel_path = utils.get_custom_channel_path()
    if custom_channel_path not in sys.path:
        sys.path.insert(0, custom_channel_path)

    # Initialize all channels
    # (Load libraries and modules and init them with Queue `q`)

    conf = config.load_config()

    for i in conf['slave_channels']:
        logger.critical("\x1b[0;37;46m Initializing slave %s... \x1b[0m", i)

        obj = pydoc.locate(i)
        coordinator.add_channel(obj())

        logger.critical("\x1b[0;37;42m Slave channel %s (%s) initialized. \x1b[0m",
                        obj.channel_name, obj.channel_id)

    logger.critical("\x1b[0;37;46m Initializing master %s... \x1b[0m", str(conf['master_channel']))
    coordinator.add_channel(pydoc.locate(conf['master_channel'])())
    logger.critical("\x1b[0;37;42m Master channel %s (%s) initialized. \x1b[0m",
                    coordinator.master.channel_name, coordinator.master.channel_id)

    logger.critical("\x1b[1;37;42m All channels initialized. \x1b[0m")
    coordinator.master_thread = threading.Thread(target=coordinator.master.poll)
    coordinator.slave_threads = {key: threading.Thread(target=coordinator.slaves[key].poll)
                                 for key in coordinator.slaves}


def poll():
    """
    Start threads for polling
    """
    coordinator.master_thread.start()
    for i in coordinator.slave_threads:
        coordinator.slave_threads[i].start()


if __name__ == '__main__':
    parser.add_argument("-v", action='store_true',
                        help="Enable verbose mode. (Level: Debug)")
    parser.add_argument("-V", "--version", action='store_true',
                        help="Show version number and exit.")
    parser.add_argument("-p", "--profile",
                        help="Choose a profile to start with.")

    args = parser.parse_args()

    if getattr(args, "version", None):
        versions = "EH Forwarder Bot\n" \
                   "Version: %s\n" \
                   "Python version:\n" \
                   "%s" % (__version__, sys.version)
        try:
            conf = config.load_config()
            # Master channel
            master_channel: EFBChannel = pydoc.locate(conf['master_channel'])
            versions += "\n\nMaster channel:\n    %s (%s) %s" % \
                        (master_channel.channel_name, master_channel.channel_id, master_channel.__version__)
            versions += "\n\nSlave channels:"
            for i in conf['slave_channels']:
                slave_channel: EFBChannel = pydoc.locate(i)
                versions += "\n    %s (%s) %s" % \
                            (slave_channel.channel_name, slave_channel.channel_id, slave_channel.__version__)
            versions += "\n\nMiddlewares:"
            for i in conf['middlewares']:
                middleware: EFBMiddleware = pydoc.locate(i)
                versions += "\n    %s (%s) %s" % \
                            (middleware.middleware_name, middleware.middleware_name, middleware.__version__)
            else:
                versions += "\n    No middleware is enabled."
        finally:
            print(versions)
    else:
        if getattr(args, "v", None):
            level = logging.DEBUG
        else:
            level = logging.ERROR
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(name)s (%(module)s.%(funcName)s; '
                                   '%(filename)s:%(lineno)d) \n    %(message)s', level=level)

        signal.signal(signal.SIGINT, stop_gracefully)
        signal.signal(signal.SIGTERM, stop_gracefully)

        if args.profile:
            coordinator.profile = str(args.profile)

        init()
        poll()
