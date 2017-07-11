import os
import queue
import threading
import logging
import argparse
import sys
import signal
import pydoc
from . import config, utils
from .shared_data import EFBCoordinator
from .__version__ import __version__
from .channel import EFBChannel

if sys.version_info.major < 3:
    raise Exception("Python 3.x is required. Your version is %s." % sys.version)

parser = argparse.ArgumentParser(description="EH Forwarder Bot is an extensible chat tunnel framework which allows "
                                             "users to contact people from other chat platforms, and ultimately "
                                             "remotely control their accounts in other platforms.",
                                 epilog="GitHub: https://github.com/blueset/ehForwarderBot")
parser.add_argument("-v", default=0, action="count",
                    help="Increase verbosity. -vv at most.")
parser.add_argument("-V", "--version", action="version",
                    help="Show version number and exit.",
                    version="EH Forwarder Bot %s" % __version__)
parser.add_argument("-l", "--log",
                    help="Set log file path.")
parser.add_argument("-p", "--profile",
                    help="Choose a profile to start with.")

args = parser.parse_args()

shared_data = None
master_thread = None
slave_threads = None


def stop_gracefully(sig, stack):
    l = logging.getLogger("ehForwarderBot")
    if isinstance(shared_data.master, EFBChannel):
        shared_data.master.stop_polling = True
        l.debug("Stop signal sent to master: %s" % shared_data.master.channel_name)
        while master_thread.is_alive():
            pass
    for i in shared_data.slaves:
        if isinstance(shared_data.slaves[i], EFBChannel):
            shared_data.slaves[i].stop_polling = True
            l.debug("Stop signal sent to slave: %s" % shared_data.slaves[i].channel_name)
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
    global shared_data, master_thread, slave_threads

    # Init shared data object
    shared_data = EFBCoordinator(args.profile)

    # Include custom channels
    custom_channel_path = utils.get_custom_channel_path()
    if custom_channel_path not in sys.path:
        sys.path.insert(0, custom_channel_path)

    # Initialize all channels
    # (Load libraries and modules and init them with Queue `q`)
    l = logging.getLogger("ehForwarderBot")

    conf = config.load_config()

    slaves = {}
    for i in conf['slave_channels']:
        l.critical("\x1b[0;37;46m Initializing slave %s... \x1b[0m" % str(i))

        obj = pydoc.locate(i)
        shared_data.add_channel(obj(shared_data), is_slave=True)

        l.critical("\x1b[0;37;42m Slave channel %s (%s) initialized. \x1b[0m" % (obj.channel_name, obj.channel_id))

    l.critical("\x1b[0;37;46m Initializing master %s... \x1b[0m" % str(conf['master_channel']))
    shared_data.add_channel(pydoc.locate(conf['master_channel'])(shared_data), is_slave=False)
    l.critical("\x1b[0;37;42m Master channel %s (%s) initialized. \x1b[0m" %
               (shared_data.master.channel_name, shared_data.master.channel_id))

    l.critical("\x1b[1;37;42m All channels initialized. \x1b[0m")
    master_thread = threading.Thread(target=shared_data.master.poll)
    slave_threads = {key: threading.Thread(target=slaves[key].poll) for key in slaves}


def poll():
    """
    Start threads for polling
    """
    global master_thread, slave_threads
    master_thread.start()
    for i in slave_threads:
        slave_threads[i].start()

if getattr(args, "V", None):
    print("EH Forwarder Bot\n"
          "Version: %s" % __version__)
else:
    if args.v == 0:
        level = logging.ERROR
    elif args.v == 1:
        level = logging.INFO
    else:
        level = logging.DEBUG
    logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(name)s @ '
                               '%(pathname)s/%(module)s.%(funcName)s:%(lineno)d\n'
                               '%(message)s', level=level)

    signal.signal(signal.SIGINT, stop_gracefully)
    signal.signal(signal.SIGTERM, stop_gracefully)

    if args.profile:
        os.environ['EFB_PROFILE'] = str(args.profile)

    if getattr(args, "log", None):
        LOG = args.log
        set_log_file(LOG)

    init()
    poll()
