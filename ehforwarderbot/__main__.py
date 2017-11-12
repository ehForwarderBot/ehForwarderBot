import os
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
        while master_thread.is_alive():
            pass
    for i in coordinator.slaves:
        if isinstance(coordinator.slaves[i], EFBChannel):
            coordinator.slaves[i].stop_polling = True
            logger.debug("Stop signal sent to slave: %s" % coordinator.slaves[i].channel_name)
            while slave_threads[i].is_alive():
                pass
    sys.exit(0)


def set_log_file(fn):
    """
    Set log file path for root logger

    Args:
        fn (str): File name
    """
    fh = logging.FileHandler(fn, 'a')
    f = logging.Formatter('%(asctime)s: %(name)s [%(levelname)s]\n    %(message)s')
    fh.setFormatter(f)
    l = logging.getLogger()
    for hdlr in l.handlers[:]:
        l.removeHandler(hdlr)
    l.addHandler(fh)


def init():
    """
    Initialize all channels.
    """
    global master_thread, slave_threads

    logger = logging.getLogger(__name__)

    # Include custom channels
    custom_channel_path = utils.get_custom_channel_path()
    if custom_channel_path not in sys.path:
        sys.path.insert(0, custom_channel_path)

    # Initialize all channels
    # (Load libraries and modules and init them with Queue `q`)

    conf = config.load_config()

    slaves = {}
    for i in conf['slave_channels']:
        logger.critical(__name__, "\x1b[0;37;46m Initializing slave %s... \x1b[0m" % str(i))

        obj = pydoc.locate(i)
        coordinator.add_channel(obj())

        logger.critical(__name__, "\x1b[0;37;42m Slave channel %s (%s) initialized. \x1b[0m" % (obj.channel_name, obj.channel_id))

    logger.critical(__name__, "\x1b[0;37;46m Initializing master %s... \x1b[0m" % str(conf['master_channel']))
    coordinator.add_channel(pydoc.locate(conf['master_channel'])())
    logger.critical(__name__, "\x1b[0;37;42m Master channel %s (%s) initialized. \x1b[0m" %
               (coordinator.master.channel_name, coordinator.master.channel_id))

    logger.critical(__name__, "\x1b[1;37;42m All channels initialized. \x1b[0m")
    master_thread = threading.Thread(target=coordinator.master.poll)
    slave_threads = {key: threading.Thread(target=slaves[key].poll) for key in slaves}


def poll():
    """
    Start threads for polling
    """
    global master_thread, slave_threads
    master_thread.start()
    for i in slave_threads:
        slave_threads[i].start()


if __name__ == '__main__':
    parser.add_argument("-v",
                        help="Enable verbose mode. (Level: Debug)")
    parser.add_argument("-V", "--version",
                        help="Show version number and exit.")
    parser.add_argument("-l", "--log",
                        help="Set log file path.")
    parser.add_argument("-p", "--profile",
                        help="Choose a profile to start with.")

    args = parser.parse_args()

    master_thread = None
    slave_threads = None

    if getattr(args, "V", None):
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
            for i in conf['slave_channel']:
                slave_channel: EFBChannel = pydoc.locate(i)
                versions += "\n    %s (%s) %s" % \
                            (slave_channel.channel_name, slave_channel.channel_id, slave_channel.__version__)
            versions += "\n\nMiddlewares:"
            for i in conf['middlewares']:
                middleware: EFBMiddleware = pydoc.locate(i)
                versions += "\n    %s (%s) %s" % \
                            (middleware.middleware_name, middleware.middleware_name, middleware.__version__)
        finally:
            print(versions)
    else:
        if getattr(args, "v", None):
            level = logging.DEBUG
        else:
            level = logging.ERROR
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(name)s (%(module)s.%(funcName)s) \n    %(message)s', level=level)

        signal.signal(signal.SIGINT, stop_gracefully)
        signal.signal(signal.SIGTERM, stop_gracefully)

        if args.profile:
            coordinator.profile = str(args.profile)

        if getattr(args, "log", None):
            LOG = args.log
            set_log_file(LOG)

        init()
        poll()
