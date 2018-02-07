# coding=utf-8

import threading
import logging
import argparse
import sys
import atexit
import mimetypes
import pkg_resources
import gettext

from . import config, utils
from . import coordinator
from .__version__ import __version__
from .channel import EFBChannel
from .middleware import EFBMiddleware

# gettext.install('ehforwarderbot', 'locale')
gettext.install('ehforwarderbot', pkg_resources.resource_filename('ehforwarderbot', 'locale'),
                names=("ngettext",))

if sys.version_info < (3, 6):
    raise Exception(_("Python 3.6 or higher is required. Your version is {version}.").format(version=sys.version))

description = _("EH Forwarder Bot is an extensible chat tunnel framework which allows "
                "users to contact people from other chat platforms, and ultimately "
                "remotely control their accounts in other platforms.")

parser = argparse.ArgumentParser(description=description,
                                 epilog="GitHub: https://github.com/blueset/ehForwarderBot")

parser.add_argument("-v", '--verbose', action='store_true',
                    help=_("Enable verbose mode. (Level: Debug)"))
parser.add_argument("-V", "--version", action='store_true',
                    help=_("Show version numbers and exit."))
parser.add_argument("-p", "--profile",
                    help=_("Choose a profile to start with."),
                    default="default")


def stop_gracefully():
    logger = logging.getLogger(__name__)
    if isinstance(coordinator.master, EFBChannel):
        coordinator.master.stop_polling()
        logger.debug("Stop signal sent to master: %s" % coordinator.master.channel_name)
    for i in coordinator.slaves:
        if isinstance(coordinator.slaves[i], EFBChannel):
            coordinator.slaves[i].stop_polling()
            logger.debug("Stop signal sent to slave: %s" % coordinator.slaves[i].channel_name)
    if coordinator.master_thread and coordinator.master_thread.is_alive():
        coordinator.master_thread.join()
    for i in coordinator.slave_threads.values():
        if i.is_alive():
            i.join()


def init():
    """
    Initialize all channels.
    """

    logger = logging.getLogger(__name__)

    # Initialize mimetypes library
    mimetypes.init([pkg_resources.resource_filename('ehforwarderbot', 'mimetypes')])

    # Initialize all channels
    # (Load libraries and modules and init them with Queue `q`)

    conf = config.load_config()

    for i in conf['slave_channels']:
        logger.log(99, "\x1b[0;37;46m Initializing slave %s... \x1b[0m", i)

        cls = utils.locate_module(i, 'slave')
        coordinator.add_channel(cls())

        logger.log(99, "\x1b[0;37;42m Slave channel %s (%s) initialized. \x1b[0m",
                   cls.channel_name, cls.channel_id)

    logger.log(99, "\x1b[0;37;46m Initializing master %s... \x1b[0m", str(conf['master_channel']))
    coordinator.add_channel(utils.locate_module(conf['master_channel'], 'master')())
    logger.log(99, "\x1b[0;37;42m Master channel %s (%s) initialized. \x1b[0m",
               coordinator.master.channel_name, coordinator.master.channel_id)

    logger.log(99, "\x1b[1;37;42m All channels initialized. \x1b[0m")
    for i in conf['middlewares']:
        logger.log(99, "\x1b[0;37;46m Initializing middleware %s... \x1b[0m", i)
        cls = utils.locate_module(i, 'middleware')
        coordinator.add_middleware(cls())
        logger.log(99, "\x1b[0;37;42m Master channel %s (%s) initialized. \x1b[0m",
                   cls.middleware_name, cls.middleware_id)

    logger.log(99, "\x1b[1;37;42m All middlewares initialized. \x1b[0m")

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


def main():
    args = parser.parse_args()

    if getattr(args, "version", None):
        versions = _("EH Forwarder Bot\n"
                     "Version: {version}\n"
                     "Python version:\n"
                     "{py_version}").format(version=__version__, py_version=sys.version)
        try:
            conf = config.load_config()
            # Master channel
            master_channel: EFBChannel = utils.locate_module(conf['master_channel'], 'master')
            versions += _("\n\nMaster channel:\n    {name} ({id}) {version}") \
                .format(name=master_channel.channel_name,
                        id=master_channel.channel_id,
                        version=master_channel.__version__)
            versions += ngettext("\n\nSlave channel:", "\n\nSlave channels:", len(conf['slave_channels']))
            for i in conf['slave_channels']:
                slave_channel: EFBChannel = utils.locate_module(i, 'slave')
                versions += _("\n    {name} ({id}) {version}") \
                            .format(name=slave_channel.channel_name,
                                    id=slave_channel.channel_id,
                                    version=slave_channel.__version__)
            versions += _("\n\nMiddlewares:")
            if conf['middlewares']:
                for i in conf['middlewares']:
                    middleware: EFBMiddleware = utils.locate_module(i, 'middleware')
                    versions += _("\n    {name} ({id}) {version}") \
                                .format(name=middleware.middleware_name,
                                        id=middleware.middleware_name,
                                        version=middleware.__version__)
            else:
                versions += _("\n    No middleware is enabled.")
        finally:
            print(versions)
    else:
        if getattr(args, "verbose", None):
            level = logging.DEBUG
        else:
            level = logging.ERROR
        logging.basicConfig(format='%(asctime)s [%(levelname)s]: %(name)s (%(module)s.%(funcName)s; '
                                   '%(filename)s:%(lineno)d) \n    %(message)s', level=level)
        logging.root.setLevel(level)

        # signal.signal(signal.SIGINT, stop_gracefully)
        # signal.signal(signal.SIGTERM, stop_gracefully)
        atexit.register(stop_gracefully)

        if args.profile:
            coordinator.profile = str(args.profile)

        init()
        poll()


if __name__ == '__main__':
    main()
