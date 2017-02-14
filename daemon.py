#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
    daemon-manager.dm
    ~~~~~~~~~~~~~~~~

    client tool for daemon-manager server.

    Modified by Eana Hufwe for EH Forwarder Bot.

    :copyright: (c) 2012 by Du Jiong.
    :license: BSD
'''

import sys
import os
import inspect
from binascii import crc32
from datetime import datetime
from functools import partial
import time
import signal
import fcntl
import subprocess

try:
    import cPickle as pickle
except ImportError:
    import pickle

if sys.version_info.major < 3:
    raise Exception("Python 3.x is required. Your version is %s." % sys.version)

user_home = os.path.expanduser('~')
dm_home = os.path.join(user_home, '.dm')
dm_home_file = os.path.join(dm_home, '.dmlock')


def file_lock(func):
    def infunc(*argv, **kwargv):
        f = open(dm_home_file, 'a')
        fcntl.lockf(f, fcntl.LOCK_EX)
        try:
            func(*argv, **kwargv)
        finally:
            fcntl.lockf(f, fcntl.LOCK_UN)
            f.close()
            try:
                os.unlink(dm_home_file)
            except OSError:
                pass
    return infunc


class Daemon(object):
    def __init__(self, cmdline, logfile=None,
                 chdir=None, name=None, group=None, **ignore):
        if chdir and not os.path.isdir(chdir):
            raise OSError('no such directory: "%s"' % chdir)
        self.cmdline = cmdline.strip()
        self.proc_cmdline = self.cmdline
        self.logfile = logfile
        self.chdir = chdir
        self.name = name
        self.group = group
        self.pid = None
        if self.chdir:
            self.dir = self.chdir
        else:
            self.dir = os.getcwd()

    @staticmethod
    def load(dm_path):
        try:
            return pickle.load(open(dm_path, 'rb'))
        except:
            try:
                os.unlink(dm_path)
            except:
                pass

    def run(self):
        self_cmdline = self.get_cmdlime(os.getpid())
        pid = os.fork()
        if pid < 0:
            raise OSError('create subprocess fail')
        elif pid == 0:
            if self.chdir:
                os.chdir(self.chdir)
            os.umask(0)
            os.setsid()
            os.close(0)
            if self.logfile:
                f = open(self.logfile, 'a')
                os.dup2(f.fileno(), 1)
                os.dup2(f.fileno(), 2)
            else:
                os.close(1)
                os.close(2)
            args = self.cmdline.split()
            os.execlp(args[0], *args)
            os._exit(-1)
        else:
            self.pid = pid
            self.time = datetime.now().strftime('%Y-%m-%d %H:%m:%S')
            while True:
                cmdline = self.get_cmdlime(pid)
                if cmdline is None or cmdline != self_cmdline:
                    break
                time.sleep(0.05)
            if not self.is_alive():
                raise OSError('daemon exit')
            self.proc_cmdline = cmdline
            return pid

    def is_alive(self):
        try:
            os.kill(self.pid, 0)
        except:
            return False
        else:
            return True

    @staticmethod
    def get_cmdlime(pid):
        cmdline_path = '/proc/{0}/cmdline'.format(pid)
        if os.path.isfile(cmdline_path):
            try:
                cmdline = open(cmdline_path).read()
            except OSError:
                return False
            return cmdline.replace('\x00', ' ').strip()


class DM(object):
    def __init__(self):
        user_home = os.path.expanduser('~')
        self.home = os.path.join(user_home, '.dm')
        self.home_file = partial(os.path.join, self.home)
        if not os.path.exists(self.home):
            os.mkdir(self.home)
        elif os.path.isfile(self.home):
            raise OSError('Failed to create directory for Daemon Manager')

    def get_daemons(self, name=None, group=None):
        if name:
            dm_path = self.home_file('%s.dm' % name)
            dm = Daemon.load(dm_path)
            if dm and dm.is_alive():
                return {dm.name: dm}
            else:
                try:
                    os.unlink(dm_path)
                except:
                    pass
            return {}
        files = os.listdir(self.home)
        dm_files = filter(lambda x: x.endswith('.dm'), files)
        daemons = {}
        for fname in dm_files:
            dm_path = self.home_file(fname)
            dm = Daemon.load(dm_path)
            if dm and dm.is_alive():
                if group is None or group == dm.group:
                    daemons[dm.name or dm.pid] = dm
                continue
            try:
                os.unlink(dm_path)
            except:
                pass
        return daemons

    @file_lock
    def run(self, cmdline, logfile=None,
            chdir=None, name=None, group=None):
        if name:
            dm_path = self.home_file('%s.dm' % name)
            if dm_path:
                dm = Daemon.load(dm_path)
                if dm and dm.is_alive():
                    print('EFB Daemon is already running.')
                    return
        else:
            dm_path = None
        dm = Daemon(cmdline=cmdline, logfile=logfile, chdir=chdir,
                    name=name, group=group)
        pid = dm.run()
        if pid > 0:
            print('pid: %d' % pid)
            f = open(dm_path or self.home_file('%d.dm' % pid), 'wb')
            f.write(pickle.dumps(dm))
            f.close()
        else:
            print('Failed to start daemon.')

    @file_lock
    def list(self, name=None, group=None):
        daemons = self.get_daemons(name=name, group=group)
        if len(daemons) == 0:
            print('Daemon is not running.')
            return
        for pid, dm in daemons.items():
            lines = ['PID: %d, CMD: %s' % (dm.pid, repr(dm.cmdline))]
            if dm.logfile:
                lines.append('Logfile: %s' % repr(dm.logfile))
            if dm.chdir:
                lines.append('Chdir: %s' % repr(dm.chdir))
            if dm.name:
                lines.append('Name: %s' % dm.name)
            if dm.group:
                lines.append('Group: %s' % dm.group)
            lines.append('Start at: "%s"' % dm.time)
            print('\n'.join(lines))
            print()

    @file_lock
    def kill(self, name=None, group=None, quiet=False, sigkill=False):
        daemons = self.get_daemons(name, group)
        if len(daemons) > 0:
            notify = 'Stopping EFB Daemon (%d)\n' % len(daemons)
            if quiet is False:
                notify += 'are you sure? [Y/n]'
                yn = input(notify)
            else:
                yn = 'Y'
                print(notify)
            if len(yn) == 0 or yn.upper() == 'Y':
                for pid, dm in daemons.items():
                    try:
                        if sigkill:
                            os.kill(dm.pid, signal.SIGKILL)
                        else:
                            os.kill(dm.pid, signal.SIGTERM)
                    except OSError as e:
                        raise e
            print("Done.")
        else:
            print('Daemon is not running.')

    @file_lock
    def restart(self, name=None, group=None, cmd=None,
                quiet=False, sigkill=False):
        daemons = self.get_daemons(name, group)
        if len(daemons) > 0:
            notify = 'Restarting EFB daemon (%d)' % len(daemons)
            if quiet is False:
                notify += 'are you sure? [Y/n]'
                yn = input(notify)
            else:
                yn = 'Y'
                print(notify)
            if len(yn) == 0 or yn.upper() == 'Y':
                for pid, dm in daemons.items():
                    try:
                        if sigkill:
                            os.kill(dm.pid, signal.SIGKILL)
                        else:
                            os.kill(dm.pid, signal.SIGTERM)
                    except OSError:
                        pass
            else:
                return
            if cmd is not None:
                dm.cmdline = cmd
            for dm in daemons.values():
                pid = dm.run()
                print('PID: %d%s%s' % (pid,
                                       dm.name and '\nName: %s' % dm.name or '',
                                       dm.group and '\nGroup: %s' % dm.group or ''))
                f = open(self.home_file('%s.dm' % (dm.name or str(pid))), 'wb')
                f.write(pickle.dumps(dm))
                f.close()
        else:
            raise NameError("Daemon is not running.")

def help():
    print("EFB Daemon Process\n"
          "Usage: %s {start|stop|restart|status|transcript|help} [args_to_EFB]\n\n" % sys.argv[0] +
          "EFB help:")
    subprocess.call([sys.executable, "main.py", "-h"])


def transcript(path, reset=False):
    if reset:
        with open(path, "w") as f:
            f.write("")

    l = ["Output is saved to '%s', showing output now." % path,
         "Press ^C (Control+C on Mac, Ctrl+C otherwise) to hide."]
    w = int(max(len(i) for i in l))
    for i in l:
        print("\x1b[1;37;44m   %s  \x1b[0m" % i.ljust(w))
    print()
    try:
        subprocess.call(["tail", "-f", path])
    except KeyboardInterrupt:
        pass
    except ProcessLookupError:
        pass


def main():
    transcript_path = "EFB.log"
    instance_name = str(crc32(os.path.dirname(os.path.abspath(inspect.stack()[0][1])).encode()))
    if len(sys.argv) < 2:
        help()
        exit()
    dm = DM()
    efb_args = " ".join(sys.argv[2:])
    if len(dm.get_daemons(name="EFB")):
        print("Old daemon process is killed.")
        dm.kill(name="EFB", quiet=True, sigkill=True)
    if sys.argv[1] == "start":
        dm.run(cmdline=" ".join((sys.executable + " main.py", efb_args)),
               name=instance_name,
               logfile=transcript_path)
        transcript(transcript_path, True)
    elif sys.argv[1] == "stop":
        dm.kill(name=instance_name, quiet=True, sigkill=True)
    elif sys.argv[1] == "status":
        dm.list(name=instance_name)
    elif sys.argv[1] == "restart":
        kwargs = {"name": instance_name, "quiet": True, "sigkill": True}
        if len(sys.argv) > 2:
            kwargs["cmd"] = " ".join((sys.executable, "main.py", efb_args))
        try:
            dm.restart(**kwargs)
        except NameError as e:
            print(e)
            dm.run(cmdline=" ".join((sys.executable + " main.py", efb_args)),
                   name=instance_name,
                   logfile=transcript_path)
        transcript(transcript_path, True)
    elif sys.argv[1] == "transcript":
        transcript(transcript_path)
    else:
        help()

if __name__ == '__main__':
    main()
