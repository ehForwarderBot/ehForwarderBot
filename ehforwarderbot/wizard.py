# -*- coding: utf-8 -*-
"""
Interactive wizard to guide user to set up EFB and modules.

Since newer version of pip (>=9.0), which checks Python version
prior to installation, is already widespread, we are dropping
Python version check in wizard script, and assuming user is
running an appropriate Python version.
"""

import argparse
import gettext
import os
import platform
import sys
from collections import namedtuple
from contextlib import suppress
from io import StringIO
from typing import Dict, Callable, Optional
from urllib.parse import quote

import bullet.utils
import cjkwrap
import pkg_resources
from bullet import Bullet, keyhandler, colors
from bullet.charDef import NEWLINE_KEY, BACK_SPACE_KEY
from ruamel.yaml import YAML

from ehforwarderbot import coordinator, utils

Module = namedtuple("Module", ['type', 'id', 'name', 'emoji', 'wizard'])
Module.replace = Module._replace  # type: ignore

gettext.translation(
    'ehforwarderbot',
    pkg_resources.resource_filename('ehforwarderbot', 'locale'),
    fallback=True
).install(names=["ngettext"])
_: Callable
ngettext: Callable


def print_wrapped(text):
    paras = text.split("\n")
    for i in paras:
        print(*cjkwrap.wrap(i), sep="\n")


class DataModel:
    def __init__(self, profile):
        self.profile = profile

        self.yaml = YAML()
        self.config = None
        self.modules: Dict[str, Module] = {}

    @staticmethod
    def default_config():
        # TRANSLATORS: This part of text must be formatted in a monospaced font, and all lines must not exceed the width of a 70-cell-wide terminal.
        config = _(
            "# ===================================\n"
            "# EH Forwarder Bot Configuration File\n"
            "# ===================================\n"
            "# \n"
            "# This file determines what modules, including master channel, slave channels,\n"
            "# and middlewares, are enabled in this profile.\n"
            "# \n"
            "# \n"
            "# Master Channel\n"
            "# --------------\n"
            "# Exactly one instance of a master channel is required for a profile.\n"
            "# Fill in the module ID and instance ID (if needed) below.\n"
        )
        config += "\nmaster_channel:\n\n"
        # TRANSLATORS: This part of text must be formatted in a monospaced font, and all lines must not exceed the width of a 70-cell-wide terminal.
        config += _(
            "# Slave Channels\n"
            "# --------------\n"
            "# \n"
            "# At least one slave channel is required for a profile.\n"
            "# Fill in the module ID and instance ID (if needed) of each slave channel\n"
            "# to be enabled below.\n"
        )
        config += "\nslave_channels: []\n\n"
        # TRANSLATORS: This part of text must be formatted in a monospaced font, and all lines must not exceed the width of a 70-cell-wide terminal.
        config += _(
            "# Middlewares\n"
            "# -----------\n"
            "# Middlewares are not required to run an EFB profile. If you are not\n"
            "# going to use any middleware in this profile, you can safely remove\n"
            "# this section. Otherwise, please list down the module ID and instance\n"
            "# ID of each middleware to be enabled below.\n"
        )
        config += "middlewares: []\n"

        str_io = StringIO(config)
        str_io.seek(0)
        return str_io

    def load_config(self):
        coordinator.profile = self.profile
        conf_path = utils.get_config_path()
        if not os.path.exists(conf_path):
            self.config = self.yaml.load(self.default_config())
        else:
            with open(conf_path) as f:
                self.config = self.yaml.load(f)
        self.load_modules_list()

    def save_config(self):
        coordinator.profile = self.profile
        conf_path = utils.get_config_path()
        if not conf_path.exists():
            conf_path.parent.mkdir(parents=True, exist_ok=True)
        with open(conf_path, 'w') as f:
            self.yaml.dump(self.config, f)

    def load_modules_list(self):
        for i in pkg_resources.iter_entry_points("ehforwarderbot.master"):
            cls = i.load()
            self.modules[cls.channel_id] = Module(type="master",
                                                  id=cls.channel_id,
                                                  name=cls.channel_name,
                                                  emoji=cls.channel_emoji,
                                                  wizard=None)
        for i in pkg_resources.iter_entry_points("ehforwarderbot.slave"):
            cls = i.load()
            self.modules[cls.channel_id] = Module(type="slave",
                                                  id=cls.channel_id,
                                                  name=cls.channel_name,
                                                  emoji=cls.channel_emoji,
                                                  wizard=None)
        for i in pkg_resources.iter_entry_points("ehforwarderbot.middleware"):
            cls = i.load()
            self.modules[cls.middleware_id] = Module(type="middleware",
                                                     id=cls.middleware_id,
                                                     name=cls.middleware_name,
                                                     emoji=None,
                                                     wizard=None)
        for i in pkg_resources.iter_entry_points("ehforwarderbot.wizard"):
            if i.name in self.modules:
                fn = i.load()
                self.modules[i.name] = self.modules[i.name].replace(wizard=fn)

    def get_master_lists(self):
        names = []
        ids = []
        for i in self.modules.values():
            if i.type == "master":
                names.append(i.name)
                ids.append(i.id)
        return names, ids

    def get_slave_lists(self):
        names = []
        ids = []
        for i in self.modules.values():
            if i.type == "slave":
                names.append(i.name)
                ids.append(i.id)
        return names, ids

    @staticmethod
    def split_cid(cid):
        if "#" in cid:
            mid, iid = cid.split("#")
        else:
            mid = cid
            iid = None
        return mid, iid

    def get_instance_display_name(self, cid):
        if not cid:
            return cid
        mid, iid = self.split_cid(cid)
        if mid not in self.modules:
            if iid:
                return _("Unknown/custom module (instance: {instance})").format(
                    iid
                )
            else:
                return _("Unknown/custom module")
        else:
            if iid:
                name = _("{channel} (instance: {instance})").format(
                    channel=self.modules[mid].name,
                    instance=iid
                )
            else:
                name = self.modules[mid].name
        return name

    def has_wizard(self, cid):
        mid, _ = self.split_cid(cid)
        if mid not in self.modules:
            return False
        return callable(self.modules[mid].wizard)

    def get_selected_slave_lists(self):
        if 'slave_channels' not in self.config:
            self.config['slave_channels'] = []
            return [], []
        i = 0

        names = []
        ids = []

        while i < len(self.config['slave_channels']):
            cid = self.config['slave_channels'][i]
            mid, __ = self.split_cid(cid)

            if mid not in self.modules or self.modules[mid].type != "slave":
                names.append(_("Unknown/custom channel ({channel_id})").format(channel_id=cid))
                ids.append(cid)
            else:
                name = self.get_instance_display_name(cid)
                names.append(name)
                ids.append(cid)
            i += 1
        return names, ids

    def get_middleware_lists(self):
        names = []
        ids = []
        for i in self.modules.values():
            if i.type == "middleware":
                names.append(i.name)
                ids.append(i.id)
        return names, ids

    def get_selected_middleware_lists(self):
        if 'middlewares' not in self.config:
            self.config['middlewares'] = []
            return [], []
        i = 0
        names = []
        ids = []
        while i < len(self.config['middlewares']):
            cid = self.config['middlewares'][i]
            mid, __ = self.split_cid(cid)

            if mid not in self.modules or self.modules[mid].type != "middleware":
                names.append(_("Unknown/custom middleware ({middleware_id})").format(middleware_id=cid))
                ids.append(cid)
            else:
                name = self.get_instance_display_name(cid)
                names.append(name)
                ids.append(cid)
            i += 1
        return names, ids


# @keyhandler.init
class KeyValueBullet(Bullet):
    def __init__(self, prompt: str = "", choices: list = [], choices_id: list = [], bullet: str = "●",
                 bullet_color: str = colors.foreground["default"], word_color: str = colors.foreground["default"],
                 word_on_switch: str = colors.REVERSE, background_color: str = colors.background["default"],
                 background_on_switch: str = colors.REVERSE, pad_right=0, indent: int = 0, align=0, margin: int = 0,
                 shift: int = 0):
        super().__init__(prompt, choices, bullet, bullet_color, word_color, word_on_switch, background_color,
                         background_on_switch, pad_right, indent, align, margin, shift)

        self.choices_id = choices_id
        self._key_handler: Dict[int, Callable] = self._key_handler.copy()
        self._key_handler[NEWLINE_KEY] = self.__class__.accept

    # @keyhandler.register(NEWLINE_KEY)
    def accept(self, *args):
        pos = self.pos
        bullet.utils.moveCursorDown(len(self.choices) - pos)
        self.pos = 0
        return self.choices[pos], self.choices_id[pos]


class ReorderBullet(Bullet):

    def __init__(self, prompt: str = "", choices: list = None, choices_id: list = None, bullet: str = "●",
                 bullet_color: str = colors.foreground["default"], word_color: str = colors.foreground["default"],
                 word_on_switch: str = colors.REVERSE, background_color: str = colors.background["default"],
                 background_on_switch: str = colors.REVERSE, pad_right=0, indent: int = 0, align=0, margin: int = 0,
                 shift: int = 0, required: bool = False):
        if choices is None:
            choices = []
        if choices_id is None:
            choices_id = []
        prompt += "\n" + _(
            "[ =: Shift up; -: Shift down; Backspace: Remove ]"
        )
        choices.extend((
            _("+ Add"),
            _("✓ Submit")
        ))
        super().__init__(prompt, choices, bullet, bullet_color, word_color, word_on_switch, background_color,
                         background_on_switch, pad_right, indent, align, margin, shift)
        self.choices_id = choices_id
        self.choices_id.extend((
            "add",
            "submit"
        ))
        self._key_handler: Dict[int, Callable] = self._key_handler.copy()
        self._key_handler[NEWLINE_KEY] = self.__class__.accept_fork
        self.required = required

    @keyhandler.register(ord('-'))
    def shift_up(self):
        choices = len(self.choices)
        if self.pos - 1 < 0 or self.pos >= choices - 2:
            return
        else:
            self.choices[self.pos - 1], self.choices[self.pos] = self.choices[self.pos], self.choices[self.pos - 1]
            bullet.utils.clearLine()
            old_pos = self.pos
            self.pos -= 1
            self.printBullet(old_pos)
            bullet.utils.moveCursorUp(1)
            bullet.utils.clearLine()
            self.printBullet(self.pos)

    @keyhandler.register(ord('='))
    def shift_down(self):
        choices = len(self.choices)
        if self.pos >= choices - 3:
            return
        else:
            self.choices[self.pos + 1], self.choices[self.pos] = self.choices[self.pos], self.choices[self.pos + 1]
            bullet.utils.clearLine()
            old_pos = self.pos
            self.pos += 1
            self.printBullet(old_pos)
            bullet.utils.moveCursorDown(1)
            bullet.utils.clearLine()
            self.printBullet(self.pos)

    @keyhandler.register(BACK_SPACE_KEY)
    def delete_item(self):
        choices = len(self.choices)
        if self.pos >= choices - 2:
            return
        self.choices.pop(self.pos)
        self.choices_id.pop(self.pos)
        bullet.utils.moveCursorUp(self.pos - 1)
        bullet.utils.clearConsoleDown(choices)
        bullet.utils.moveCursorUp(1)
        for i in range(len(self.choices)):
            bullet.utils.moveCursorDown(1)
            self.printBullet(i)
        bullet.utils.moveCursorUp(1)

    # @keyhandler.register(NEWLINE_KEY)
    def accept_fork(self):
        choices = len(self.choices)
        if self.required and self.pos == choices - 1 and choices <= 2:
            # Reject empty list
            return None
        if self.pos >= choices - 2:  # Add / Submit
            pos = self.pos
            bullet.utils.moveCursorDown(len(self.choices) - pos)
            self.pos = 0
            return self.choices[:-2], self.choices_id[:-2], self.choices_id[pos]
        return None


def get_platform_name():
    p = platform.system()
    if p == "Linux":
        # noinspection PyBroadException
        try:
            # noinspection PyDeprecation
            return ' '.join(platform.linux_distribution()[:2])
        except:  # lgtm [py/catch-base-exception]
            # noinspection PyDeprecation
            return ' '.join(platform.dist()[:2])
    elif p == "Darwin":
        return "macOS " + platform.mac_ver()[0]
    elif p == "Windows":
        return "Windows " + platform.win32_ver()[1]
    else:
        return ""


def build_search_query(query):
    return "https://google.com/search?q=" + quote(query)


def prerequisite_check():
    """
    Check prerequisites of the framework, including Python version, installation of
    modules, etc.

    Returns:
        Optional[str]: If the check is not passed, return error message regarding
            failed test case.  None is returned otherwise.
    """

    # Check Python version
    print(_("Checking Python version... "), end="")
    if sys.version_info < (3, 6):
        version_str = "%s.%s.%s" % sys.version_info[:3]
        # TRANSLATORS: This word is used as a part of search query suggested to users,
        # it may appears in context like "Ubuntu 16.04 install Python 3.7"
        search_url = build_search_query(_("install") + " Python 3.7")
        print()
        print(_("EH Forwarder Bot requires a minimum of Python 3.6 to run.  You "
                "are currently using Python {version}. \n"
                "\n"
                "You may want to try:\n"
                "{url}").format(version=version_str, url=search_url))
        exit(1)
    else:
        print(_("OK"))

    # Check installations of modules
    modules_err = _("You may want to visit the modules repository to find a list of "
                    "available modules to install.\n"
                    "https://efb-modules.1a23.studio")
    # 1. At least 1 master channel must be installed
    print(_("Checking master channels... "), end="")
    try:
        next(pkg_resources.iter_entry_points("ehforwarderbot.master"))
    except StopIteration:
        print()
        print(_("No master channel detected.  EH Forwarder Bot requires at least one "
                "master channel installed to run.") + "\n\n" + modules_err)
        exit(1)
    print(_("OK"))

    # 2. At least 1 slave channel must be installed
    print(_("Checking slave channels... "), end="")
    try:
        next(pkg_resources.iter_entry_points("ehforwarderbot.slave"))
    except StopIteration:
        print()
        print(_("No slave channel detected.  EH Forwarder Bot requires at least one "
                "slave channel installed to run.") + "\n\n" + modules_err)
        exit(1)
    print(_("OK"))
    print()


def choose_master_channel(data: DataModel):
    channel_names, channel_ids = data.get_master_lists()

    list_widget = KeyValueBullet(prompt=_("1. Choose master channel"),
                                 choices=channel_names,
                                 choices_id=channel_ids)

    default_idx = None
    default_instance = ''
    if "master_channel" in data.config and data.config['master_channel']:
        default_config = data.config['master_channel'].split("#")
        default_id = default_config[0]
        if len(default_config) > 1:
            default_instance = default_config[1]
        with suppress(ValueError):
            default_idx = channel_ids.index(default_id)

    chosen_channel_name, chosen_channel_id = list_widget.launch(default=default_idx)

    chosen_instance = input(_("Instance name to use with {channel_name}: [{default_instance}]")
                            .format(channel_name=chosen_channel_name,
                                    default_instance=default_instance or _("default instance"))
                            + " ").strip()
    if chosen_instance:
        chosen_channel_id += "#" + chosen_instance
    data.config['master_channel'] = chosen_channel_id


def choose_slave_channels(data: DataModel):
    chosen_slave_names, chosen_slave_ids = data.get_selected_slave_lists()
    widget = ReorderBullet(_("2. Choose slave channels (at least one is required)."),
                           choices=chosen_slave_names,
                           choices_id=chosen_slave_ids,
                           required=True)

    channel_names, channel_ids = data.get_slave_lists()
    list_widget = KeyValueBullet(prompt=_("Choose a slave channel to add."),
                                 choices=channel_names,
                                 choices_id=channel_ids)

    while True:
        print()
        chosen_slave_names, chosen_slave_ids, action = widget.launch()
        if action == 'add':
            print()
            add_channel_name, add_channel_id = list_widget.launch()
            add_channel_instance = input(_("Instance name to use with {channel_name}: [{default_instance}]")
                                         .format(channel_name=add_channel_name,
                                                 default_instance=_("default instance"))
                                         + " ").strip()
            if add_channel_instance:
                add_channel_id += "#" + add_channel_instance

            display_name = data.get_instance_display_name(add_channel_id)
            if add_channel_id in widget.choices_id:
                print_wrapped(_("{instance_name} ({instance_id}) is already enabled. "
                                "Please try another one.")
                              .format(instance_name=display_name, instance_id=add_channel_id))
            else:
                widget.choices.insert(-2, display_name)
                widget.choices_id.insert(-2, add_channel_id)
        else:  # action == 'submit'
            break
    data.config['slave_channels'] = chosen_slave_ids


def choose_middlewares(data: DataModel):
    chosen_middlewares_names, chosen_middlewares_ids = data.get_selected_middleware_lists()
    widget = ReorderBullet(_("3. Choose middlewares (optional)."),
                           choices=chosen_middlewares_names,
                           choices_id=chosen_middlewares_ids)

    middlewares_names, middlewares_ids = data.get_middleware_lists()
    list_widget: Optional[KeyValueBullet]
    if middlewares_ids:
        list_widget = KeyValueBullet(prompt=_("Choose a middleware to add."),
                                     choices=middlewares_names,
                                     choices_id=middlewares_ids)
    else:
        list_widget = None

    while True:
        print()
        chosen_middlewares_names, chosen_middlewares_ids, action = widget.launch()
        if action == 'add':
            print()
            if not list_widget:
                print_wrapped(_("No installed middleware is detected, press ENTER to go back."))
                input()
            else:
                add_middleware_name, add_middleware_id = list_widget.launch()
                add_middleware_instance = input(_("Instance name to use with {middleware_name}: [{default_instance}]")
                                                .format(middleware_name=add_middleware_name,
                                                        default_instance=_("default instance"))
                                                + " ").strip()
                if add_middleware_instance:
                    add_middleware_id += "#" + add_middleware_instance

                display_name = data.get_instance_display_name(add_middleware_id)
                if add_middleware_id in widget.choices_id:
                    print_wrapped(_("{instance_name} ({instance_id}) is already enabled. "
                                    "Please try another one.")
                                  .format(instance_name=display_name, instance_id=add_middleware_id))
                else:
                    widget.choices.insert(-2, display_name)
                    widget.choices_id.insert(-2, add_middleware_id)
        else:  # action == 'submit'
            break
    data.config['middlewares'] = chosen_middlewares_ids


def confirmation(data: DataModel):
    list_widget = KeyValueBullet(prompt=_("Would you like to continue?"),
                                 choices=[_("Save and continue"),
                                          _("Change master channel settings"),
                                          _("Change slave channel settings"),
                                          _("Change middleware settings")],
                                 choices_id=["continue", "master", "slave", "middleware"])

    while True:
        print()
        print_wrapped(_('You have chosen to enable the following '
                        'modules for profile "{profile}".')
                      .format(profile=data.profile))
        print()
        master_name = data.get_instance_display_name(data.config['master_channel'])
        print_wrapped(_("Master channel: {channel_name}")
                      .format(channel_name=master_name))
        print()
        print_wrapped(ngettext("Slave channel:", "Slave channels:",
                               len(data.config['slave_channels'])))
        for i in data.config['slave_channels']:
            print_wrapped('- ' + data.get_instance_display_name(i))

        num_middlewares = len(data.config.get('middlewares', []))
        if num_middlewares > 0:
            print()
            print_wrapped(ngettext("Middleware:", "Middlewares:", num_middlewares))
            for i in data.config['middlewares']:
                print_wrapped('- ' + data.get_instance_display_name(i))
        print()

        outcome = list_widget.launch()[1]

        if outcome == "master":
            choose_master_channel(data)
        elif outcome == "slave":
            choose_slave_channels(data)
        elif outcome == "middleware":
            choose_middlewares(data)
        else:  # "continue"
            break

    data.save_config()
    print()
    print(_("Configuration is saved."))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--profile",
                        help=_("Choose a profile to start with."),
                        default="default")
    parser.add_argument("-m", "--module",
                        help=_("Start the wizard of a module manually, skipping "
                               "the framework wizard."))
    args = parser.parse_args()

    data = DataModel(args.profile)
    data.load_config()

    if args.module:
        mid, iid = data.split_cid(args.module)
        if callable(data.modules[mid].wizard):
            data.modules[mid].wizard(data.profile, iid)
            return
        else:
            print(_("{module_id} did not register any wizard "
                    "program to start with.").format(module_id=args.module))
            exit(1)

    prerequisite_check()

    print_wrapped(_("Welcome to EH Forwarder Bot Setup Wizard.  This program "
                    "will guide you to finish up the last few steps to "
                    "get EFB ready to use.\n"
                    "\n"
                    "To use this wizard in another supported language, "
                    "please change your system language or modify the "
                    "language environment variable and restart the wizard."))

    print()

    data.profile = input(_("Profile") + f": [{data.profile}] ") or data.profile
    print()

    choose_master_channel(data)
    choose_slave_channels(data)
    choose_middlewares(data)
    confirmation(data)

    print_wrapped(_("Some more advanced settings, such as granulated log control, "
                    "are not included in this wizard.  For further details, you may want to "
                    "refer to the documentation.\n\n"
                    "https://ehforwarderbot.readthedocs.io/en/latest/config.html"))
    print()

    modules_count = 1
    missing_wizards = []
    if not data.has_wizard(data.config['master_channel']):
        missing_wizards.append(data.config['master_channel'])
    for i in data.config['slave_channels']:
        modules_count += 1
        if not data.has_wizard(i):
            missing_wizards.append(i)
    for i in data.config['middlewares']:
        modules_count += 1
        if not data.has_wizard(i):
            missing_wizards.append(i)

    if missing_wizards:
        prompt = ngettext("Note:\n"
                          "The following module does not have a setup wizard. It is probably because "
                          "that it does not need to be set up, or it requires you to set up manually.\n"
                          "Please consult its documentation for further details.\n",
                          "Note:\n"
                          "The following modules do not have a setup wizard. It is probably because "
                          "that they do not need to be set up, or they require you to set up manually.\n"
                          "Please consult their documentations respectively for further details.\n",
                          len(missing_wizards))
        print_wrapped(prompt)
        print()

        for i in missing_wizards:
            print_wrapped("- " + data.get_instance_display_name(i) + " (" + i + ")")

        print()

        if len(missing_wizards) == modules_count:
            print_wrapped(_("Congratulations! You have finished setting up EFB "
                            "framework for the chosen profile. "
                            "You may now continue to configure modules you have "
                            "enabled manually, if necessary."))
            exit(0)
        else:
            print_wrapped(_("We will now guide you to set up some modules you "
                            "have enabled. "
                            "But you may still need to configure other modules "
                            "manually if necessary."))
    else:
        print_wrapped("We will now guide you to set up modules you have enabled, "
                      "each at a time.")

    modules = [data.config['master_channel']]
    modules.extend(data.config['slave_channels'])
    if 'middlewares' in data.config:
        modules.extend(data.config['middlewares'])
    for i in modules:
        mid, iid = data.split_cid(i)
        if mid in data.modules and callable(data.modules[mid].wizard):
            print(_("Press ENTER/RETURN to start setting up {0}.").format(i))
            input()
            data.modules[mid].wizard(data.profile, iid)

    print()
    print_wrapped(_("Congratulations! You have now finished all wizard-enabled "
                    "modules. If you did not configure some modules enabled, "
                    "you might need to configure them manually."))


if __name__ == '__main__':
    main()
