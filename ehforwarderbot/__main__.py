# coding=utf-8
import argparse
import atexit
import gettext
import logging
import logging.config
import mimetypes
import signal
import sys
import threading
from typing import Dict

import pkg_resources

from . import config, utils
from . import coordinator
from .__version__ import __version__
from .channel import MasterChannel, SlaveChannel
from .middleware import Middleware
from .utils import LogLevelFilter

# gettext.install('ehforwarderbot', 'locale')
coordinator.translator = gettext.translation('ehforwarderbot',
                                             pkg_resources.resource_filename('ehforwarderbot', 'locale'),
                                             fallback=True)

_ = coordinator.translator.gettext
ngettext = coordinator.translator.ngettext

if sys.version_info < (3, 6):
    raise Exception(_("Python 3.6 or higher is required. Your version is {version}.").format(version=sys.version))

description = _("EH Forwarder Bot is an extensible message tunneling chat bot "
                "framework which delivers messages to and from multiple "
                "platforms and remotely control your accounts.")

parser = argparse.ArgumentParser(description=description,
                                 epilog="GitHub: https://efb.1a23.studio")

parser.add_argument("-v", '--verbose', action='store_true',
                    help=_("Enable verbose mode. (Level: Debug)"))
parser.add_argument("-V", "--version", action='store_true',
                    help=_("Show version numbers and exit."))
parser.add_argument("-p", "--profile",
                    help=_("Choose a profile to start with."),
                    default="default")
parser.add_argument("--trace-threads", action='store_true',
                    help=_("Trace hanging threads which are preventing EFB from stopping."))

telemetry = None  # type: ignore
signal_call_counter = 0
MAX_SIG_CALL_BEFORE_FORCE_EXIT = 5
trace_threads = False
monitoring_thread = None


def stop_gracefully(*_, **__):
    global signal_call_counter, trace_threads, monitoring_thread
    signal_call_counter += 1
    logger = logging.getLogger(__name__)

    if trace_threads:
        from hanging_threads import start_monitoring
        if signal_call_counter == 1:
            logger.critical(
                "Thread monitoring is started. "
                "Hanging threads will be reported every 10 seconds.\n"
                "If you see a thread keeps showing for multiple "
                "occurrences, please report it to the developer.\n\n"
                "Press Ctrl-C again to stop reporting, "
                "press another 3 times to force quit EFB."
            )
            monitoring_thread = start_monitoring()
        elif monitoring_thread is not None and monitoring_thread.is_alive():
            monitoring_thread.stop()
            logger.critical(
                "Thread report is now stopped, "
                "press Ctrl-C for 3 times to force quit EFB."
            )

    # print("SIGNAL_CALL_COUNTER", signal_call_counter)

    if signal_call_counter >= MAX_SIG_CALL_BEFORE_FORCE_EXIT:
        logger.error(
            "5 consequent exit signals detected.\n"
            "Force exiting EFB without cleaning up.\n"
            "\n"
            "If it has taken you too long to quit EFB, "
            "it is most likely a bug with EFB or some of the modules enabled. "
            "Please consider tracing the hanging thread using --trace-threads "
            "argument, and report a bug to the developers."
        )
        exit(1)

    if hasattr(coordinator, "master") and isinstance(coordinator.master, MasterChannel):
        coordinator.master.stop_polling()
        logger.debug("Stop signal sent to master: %s" % coordinator.master.channel_name)
    else:
        logger.info("Valid master channel is not found.")
    for i in coordinator.slaves:
        if isinstance(coordinator.slaves[i], SlaveChannel):
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

    coordinator.master_thread = threading.Thread(target=coordinator.master.poll,
                                                 name=f"{coordinator.master.channel_id} polling thread")
    coordinator.slave_threads = {key: threading.Thread(target=coordinator.slaves[key].poll,
                                                       name=f"{key} polling thread")
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
    """Setup telemetry.

    EH Forwarder Bot framework includes NO code that uploads your log
    or any other data to anywhere.

    To enable telemetry functionality, additional modules need to be
    installed manually, and explicit settings must be added in the configuration
    file. See :doc:`telemetry` for details.
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


def print_versions(args):
    """Print versions and exit."""
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
        master_channel: MasterChannel = utils.locate_module(conf['master_channel'], 'master')
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
            slave_channel: SlaveChannel = utils.locate_module(i, 'slave')
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
                middleware: Middleware = utils.locate_module(i, 'middleware')
                versions += "\n    " + _("{name} ({id}) {version} # {instance_id}") \
                    .format(name=middleware.middleware_name,
                            id=middleware.middleware_id,
                            version=middleware.__version__,
                            instance_id=instance_id)
        else:
            versions += "\n    " + _("No middleware is enabled.")
    finally:
        print(versions)


def main():
    args = parser.parse_args()

    if getattr(args, "version", None):
        return print_versions(args)

    if args.trace_threads:
        try:
            import hanging_threads
            global trace_threads
            trace_threads = True
        except ModuleNotFoundError:
            print(_(
                "Required dependencies are not found. Please install them with "
                "the following command:"
            ))
            print()
            print(f"    ${sys.executable} -m pip install 'ehforwarderbot[trace]'")
            print()
            exit(1)

    if args.profile:
        coordinator.profile = str(args.profile)

    conf = config.load_config()

    setup_logging(args, conf)
    setup_telemetry(conf['telemetry'])

    atexit.register(stop_gracefully)
    signal.signal(signal.SIGTERM, stop_gracefully)
    signal.signal(signal.SIGINT, stop_gracefully)

    init(conf)
    poll()


if __name__ == '__main__':
    main()
