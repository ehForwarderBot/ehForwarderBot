import config
import queue
import threading
import logging
import argparse
import sys
import signal
from channel import EFBChannel

if sys.version_info.major < 3:
    raise Exception("Python 3.x is required. Your version is %s." % sys.version)

__version__ = "1.5.5"

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

args = parser.parse_args()

q = None
mutex = None
slaves = []
master = None
master_thread = None
slave_threads = None


def stop_gracefully(*args, **kwargs):
    l = logging.getLogger("ehForwarderBot")
    if isinstance(master, EFBChannel):
        master.stop_polling = True
        l.debug("Stop signal sent to master: %s" % master.channel_name)
        while master_thread.is_alive():
            pass
    for i in slaves:
        if isinstance(slaves[i], EFBChannel):
            slaves[i].stop_polling = True
            l.debug("Stop signal sent to slave: %s" % slaves[i].channel_name)
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
    global q, slaves, master, master_thread, slave_threads, mutex
    # Init Queue, thread lock
    q = queue.Queue()
    mutex = threading.Lock()
    # Initialize Plug-ins Library
    # (Load libraries and modules and init them with Queue `q`)
    l = logging.getLogger("ehForwarderBot")
    slaves = {}
    for i in config.slave_channels:
        l.critical("\x1b[0;37;46m Initializing slave %s... \x1b[0m" % str(i))
        obj = getattr(__import__(i[0], fromlist=i[1]), i[1])
        slaves[obj.channel_id] = obj(q, mutex)
        l.critical("\x1b[0;37;42m Slave channel %s (%s) initialized. \x1b[0m" % (obj.channel_name, obj.channel_id))
    l.critical("\x1b[0;37;46m Initializing master %s... \x1b[0m" % str(config.master_channel))
    master = getattr(__import__(config.master_channel[0], fromlist=config.master_channel[1]), config.master_channel[1])(
        q, mutex, slaves)
    l.critical("\x1b[0;37;42m Master channel %s (%s) initialized. \x1b[0m" % (master.channel_name, master.channel_id))

    l.critical("\x1b[1;37;42m All channels initialized. \x1b[0m")
    master_thread = threading.Thread(target=master.poll)
    slave_threads = {key: threading.Thread(target=slaves[key].poll) for key in slaves}


def poll():
    """
    Start threads for polling
    """
    global master_thread, slave_threads
    master_thread.start()
    for i in slave_threads:
        slave_threads[i].start()


PID = "/tmp/efb.pid"
LOG = "EFB.log"

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
    logging.basicConfig(format='%(asctime)s: %(name)s [%(levelname)s]\n    %(message)s', level=level)
    logging.getLogger('requests').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    logging.getLogger('telegram.bot').setLevel(logging.CRITICAL)

    signal.signal(signal.SIGINT, stop_gracefully)
    signal.signal(signal.SIGTERM, stop_gracefully)

    if getattr(args, "log", None):
        LOG = args.log
        set_log_file(LOG)

    init()
    poll()
