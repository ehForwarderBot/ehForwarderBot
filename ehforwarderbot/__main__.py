# coding=utf-8

import threading
import logging
import argparse
import sys
import atexit
import mimetypes

import pkg_resources
import gettext
import logging.config

from typing import Dict

from . import config, utils
from . import coordinator
from .__version__ import __version__
from .channel import EFBChannel
from .middleware import EFBMiddleware
from .utils import LogLevelFilter


# gettext.install('ehforwarderbot', 'locale')
coordinator.translator = gettext.translation('ehforwarderbot',
                                             pkg_resources.resource_filename('ehforwarderbot', 'locale'),
                                             fallback=True)

_ = coordinator.translator.gettext
ngettext = coordinator.translator.ngettext

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

telemetry = None  # type: ignore


def stop_gracefully():
    logger = logging.getLogger(__name__)
    if hasattr(coordinator, "master") and isinstance(coordinator.master, EFBChannel):
        coordinator.master.stop_polling()
        logger.debug("Stop signal sent to master: %s" % coordinator.master.channel_name)
    else:
        logger.info("Valid master channel is not found.")
    for i in coordinator.slaves:
        if isinstance(coordinator.slaves[i], EFBChannel):
            coordinator.slaves[i].stop_polling()
            logger.debug("Stop signal sent to slave: %s" % coordinator.slaves[i].channel_name)
    if coordinator.master_thread and coordinator.master_thread.is_alive():
        coordinator.master_thread.join()
    for i in coordinator.slave_threads.values():
        if i.is_alive():
            i.join()


def init(conf):
    """
    Initialize all channels.
    """

    logger = logging.getLogger(__name__)

    # Initialize mimetypes library
    mimetypes.init([pkg_resources.resource_filename('ehforwarderbot', 'mimetypes')])

    # Initialize all channels
    # (Load libraries and modules and init them)

    for i in conf['slave_channels']:
        logger.log(99, "\x1b[0;37;46m %s \x1b[0m", _("Initializing slave {}...").format(i))

        cls = utils.locate_module(i, 'slave')
        telemetry_set_metadata({i: cls.__version__})
        instance_id = i.split('#', 1)[1:]
        instance_id = (instance_id and instance_id[0]) or None
        coordinator.add_channel(cls(instance_id=instance_id))

        logger.log(99, "\x1b[0;37;42m %s \x1b[0m",
                   _("Slave channel {name} ({id}) # {instance_id} is initialized.")
                   .format(name=cls.channel_name, id=cls.channel_id,
                           instance_id=instance_id or _("Default profile")))

    logger.log(99, "\x1b[0;37;46m %s \x1b[0m",
               _("Initializing master {}...").format(conf['master_channel']))
    instance_id = conf['master_channel'].split('#', 1)[1:]
    instance_id = (instance_id and instance_id[0]) or None
    module = utils.locate_module(conf['master_channel'], 'master')
    coordinator.add_channel(module(instance_id=instance_id))
    telemetry_set_metadata({conf['master_channel']: module.__version__})
    logger.log(99, "\x1b[0;37;42m %s \x1b[0m",
               _("Master channel {name} ({id}) # {instance_id} is initialized.")
               .format(name=coordinator.master.channel_name,
                       id=coordinator.master.channel_id,
                       instance_id=instance_id or _("Default profile")))

    logger.log(99, "\x1b[1;37;42m %s \x1b[0m", _("All channels initialized."))
    for i in conf['middlewares']:
        logger.log(99, "\x1b[0;37;46m %s \x1b[0m", _("Initializing middleware {}...").format(i))
        cls = utils.locate_module(i, 'middleware')
        telemetry_set_metadata({i: cls.__version__})

        instance_id = i.split('#', 1)[1:]
        instance_id = (instance_id and instance_id[0]) or None
        coordinator.add_middleware(cls(instance_id=instance_id))
        logger.log(99, "\x1b[0;37;42m %s \x1b[0m",
                   _("Middleware {name} ({id}) # {instance_id} is initialized.")
                   .format(name=cls.middleware_name, id=cls.middleware_id,
                           instance_id=instance_id or _("Default profile")))

    logger.log(99, "\x1b[1;37;42m %s \x1b[0m", _("All middlewares are initialized."))

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


def setup_logging(args, conf):
    """Setup logging"""
    logging_format = "%(asctime)s [%(levelname)s]: %(name)s (%(module)s.%(funcName)s; " \
                     "%(filename)s:%(lineno)d)\n    %(message)s"

    if getattr(args, "verbose", None):
        debug_logger = logging.StreamHandler(sys.stdout)
        debug_logger.addFilter(LogLevelFilter(max_level=logging.WARNING))
        debug_logger.setFormatter(logging.Formatter(logging_format))
        logging.root.addHandler(debug_logger)
        logging.root.level = logging.DEBUG

    error_logger = logging.StreamHandler(sys.stderr)
    error_logger.addFilter(LogLevelFilter(min_level=logging.ERROR))
    error_logger.setFormatter(logging.Formatter(logging_format))
    logging.root.addHandler(error_logger)

    if conf['logging']:
        logging.config.dictConfig(conf['logging'])


CAPTURE_EXCEPTIONS = "I agree."
CAPTURE_LOG = "I agree to surrender my immortal soul."
CAPTURE_LOG_ANALYSIS = "I agree to surrender my immortal soul and endless knowledge."


def setup_telemetry(key: str):
    """
    Setup telemetry

    EH Forwarder Bot Framework includes NO code that uploads your log
    or any other data to anywhere.

    To enable telemetry functionality, additional modules need to be
    installed manually. See :doc:`telemetry` for details.
    """

    if not isinstance(key, str):
        return

    if key not in (CAPTURE_EXCEPTIONS, CAPTURE_LOG, CAPTURE_LOG_ANALYSIS):
        return

    telemetry_config = {}
    if key in (CAPTURE_LOG, CAPTURE_LOG_ANALYSIS):
        telemetry_config.update({"sentry": {"enable": True, "capture_logs": True}})
    if key == CAPTURE_LOG_ANALYSIS:
        telemetry_config.update({
            "logz": {"enable": True},
            "loggly": {"enable": True},
            "logdna": {"enable": True}
        })

    global telemetry

    import telemetry_1a23
    telemetry_1a23.init('ehforwarderbot', telemetry_config)
    telemetry_1a23.set_metadata({"ehforwarderbot": __version__})

    telemetry = telemetry_1a23


def telemetry_set_metadata(metadata: Dict[str, str]):
    global telemetry
    if telemetry:
        telemetry.set_metadata(metadata)  # type: ignore


def main():
    args = parser.parse_args()

    if getattr(args, "version", None):
        versions = _("EH Forwarder Bot\n"
                     "Version: {version}\n"
                     "Python version:\n"
                     "{py_version}\n"
                     "Running on profile \"{profile}\"."
                     ).format(version=__version__, py_version=sys.version, profile=args.profile)
        try:
            if args.profile:
                coordinator.profile = str(args.profile)

            conf = config.load_config()
            # Master channel
            master_channel: EFBChannel = utils.locate_module(conf['master_channel'], 'master')
            instance_id = conf['master_channel'].split('#', 1)[1:]
            instance_id = (instance_id and instance_id[0]) or _("Default instance")
            versions += "\n\n" + _("Master channel:") + "\n    " + _("{name} ({id}) {version} # {instance_id}") \
                .format(name=master_channel.channel_name,
                        id=master_channel.channel_id,
                        version=master_channel.__version__,
                        instance_id=instance_id)
            versions += "\n\n" + ngettext("Slave channel:", "Slave channels:", len(conf['slave_channels']))
            for i in conf['slave_channels']:
                instance_id = i.split('#', 1)[1:]
                instance_id = (instance_id and instance_id[0]) or _("Default instance")
                slave_channel: EFBChannel = utils.locate_module(i, 'slave')
                versions += "\n    " + _("{name} ({id}) {version} # {instance_id}") \
                            .format(name=slave_channel.channel_name,
                                    id=slave_channel.channel_id,
                                    version=slave_channel.__version__,
                                    instance_id=instance_id)
            versions += "\n\n" + ngettext("Middleware:", "Middlewares:", len(conf['middlewares']))
            if conf['middlewares']:
                for i in conf['middlewares']:
                    instance_id = i.split('#', 1)[1:]
                    instance_id = (instance_id and instance_id[0]) or _("Default instance")
                    middleware: EFBMiddleware = utils.locate_module(i, 'middleware')
                    versions += "\n    " + _("{name} ({id}) {version} # {instance_id}") \
                                .format(name=middleware.middleware_name,
                                        id=middleware.middleware_id,
                                        version=middleware.__version__,
                                        instance_id=instance_id)
            else:
                versions += "\n    " + _("No middleware is enabled.")
        finally:
            print(versions)
    else:
        if args.profile:
            coordinator.profile = str(args.profile)

        conf = config.load_config()

        setup_logging(args, conf)
        setup_telemetry(conf['telemetry'])

        atexit.register(stop_gracefully)

        init(conf)
        poll()


if __name__ == '__main__':
    main()
