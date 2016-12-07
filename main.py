import config
import queue
import threading
import logging
import argparse
from daemon import Daemon

__version__ = "1.0 build 20161207"

parser = argparse.ArgumentParser(description="EH Forwarder Bot is an extensible chat tunnel framework which allows "
                                             "users to contact people from other chat platforms, and ultimately "
                                             "remotely control their accounts in other platforms.",
                                 epilog="Support: https://github.com/blueset/ehForwarderBot")
parser.add_argument("-v", default=0, action="count",
                    help="Increase verbosity.")
parser.add_argument("-V", "--version", action="version",
                    help="Show version number and exit.",
                    version="EFB Forwarder Bot %s" % __version__)
parser.add_argument("-d", choices=["start", "stop", "restart"],
                    help="Run as a daemon.")
parser.add_argument("-l", "--log",
                    help="Set log file path.")

args = parser.parse_args()

q = None
slaves = None
master = None
master_thread = None
slave_threads = None


def set_log_file(fn):
    """
    Set log file path for root logger

    Args:
        fn (str): File name
    """
    fh = logging.FileHandler(fn, 'a')
    f = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s \n %(message)s')
    fh.setFormatter(f)
    l = logging.getLogger()
    for hdlr in l.handlers[:]:
        l.removeHandler(hdlr)
    l.addHandler(fh)


def init():
    """
    Initialize all channels.
    """
    global q, slaves, master, master_thread, slave_threads
    # Init Queue
    q = queue.Queue()
    # Initialize Plug-ins Library
    # (Load libraries and modules and init them with Queue `q`)
    slaves = {}
    for i in config.slave_channels:
        obj = getattr(__import__(i[0], fromlist=i[1]), i[1])
        slaves[obj.channel_id] = obj(q)
    master = getattr(__import__(config.master_channel[0], fromlist=config.master_channel[1]), config.master_channel[1])(
        q, slaves)

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


class EFBDaemon(Daemon):
    def __init__(self, pidfile, run):
        super().__init__(pidfile)
        self.run = run

PID = "/tmp/efb.pid"
LOG = "EFB.log"

if getattr(args, "V", None):
    print("EH Forwarder Bot\n"
          "Version: Be")
else:
    if args.v == 0:
        logging.basicConfig(level=logging.ERROR)
    elif args.v == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.v >= 2:
        logging.basicConfig(level=logging.DEBUG)
        logging.basicConfig(level=logging.DEBUG)

    if getattr(args, "log", None):
        LOG = args.log
        set_log_file(LOG)

    if getattr(args, "d", None):
        d = EFBDaemon(PID, poll)
        set_log_file(LOG)
        if args.d == "start":
            init()
            d.start()
        elif args.d == "stop":
            d.stop()
        elif args.d == "restart":
            d.stop()
            init()
            d.start()
    else:
        init()
        poll()
