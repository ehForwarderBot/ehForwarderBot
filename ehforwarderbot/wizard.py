# -*- coding: utf-8 -*-
"""
Interactive wizard to guide user to set up EFB and modules.

This guide should also include checks on Python versions, so this specific script is written
to be compatible with both Python 2 and 3.
"""
import argparse
from typing import Dict

import pkg_resources
import gettext
import sys
import os
import platform
import cjkwrap
from collections import namedtuple
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.exceptions import ResizeScreenError, StopApplication, NextScene
from asciimatics.widgets import Frame, ListBox, Layout, Divider, Text, \
    Button, TextBox, Widget, Label, PopUpDialog, RadioButtons
import asciimatics.widgets
from ruamel.yaml import YAML

if sys.version_info < (3,):
    # noinspection PyUnresolvedReferences
    from urllib import quote
else:
    from urllib.parse import quote

    if sys.version_info >= (3, 6):
        from ehforwarderbot import coordinator, utils

Module = namedtuple("Module", ['type', 'id', 'name', 'emoji', 'wizard'])
Module.replace = Module._replace  # type: ignore

gettext.translation(
    'ehforwarderbot',
    pkg_resources.resource_filename('ehforwarderbot', 'locale'),
    fallback=True
).install(names=["ngettext"])

# CJK support hack for asciimatics widgets

_split_text = asciimatics.widgets._split_text


def split_text(text, width, height, unicode_aware=True):
    if not unicode_aware:
        return _split_text(text, width, height, unicode_aware)
    result = []
    for i in text.split("\n"):
        if not i:
            result.append(i)
        else:
            result += cjkwrap.wrap(i, width)

    # Check for a height overrun and truncate.
    if len(result) > height:
        result = result[:height]
        result[height - 1] = result[height - 1][:width - 3] + "..."

    # Very small columns could be shorter than individual words - truncate
    # each line if necessary.
    for i, line in enumerate(result):
        if len(line) > width:
            result[i] = line[:width - 3] + "..."
    return result


def get_height(text, width):
    return len(split_text(text, width, float('inf')))


asciimatics.widgets._split_text = split_text


class DataModel:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("-p", "--profile",
                            help=_("Choose a profile to start with."),
                            default="default")
        args = parser.parse_args()
        self.profile = args.profile

        self.yaml = YAML()
        self.config = None
        self.modules = {}  # type: Dict[str, Module]

    @staticmethod
    def default_config():
        # TRANSLATORS: This part of text must be formatted in a monospaced font.
        # and no line shall exceed the width of a 70-cell-wide terminal.
        return _(
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
        ) + "\n" \
            "master_channel:\n\n" + _(
            "# Slave Channels\n"
            "# --------------\n"
            "# \n"
            "# At least one slave channel is required for a profile.\n"
            "# Fill in the module ID and instance ID (if needed) of each slave channel\n"
            "# to be enabled below.\n"
        ) + "\n" \
            "slave_channels: []\n\n" + _(
            "# Middlewares\n"
            "# -----------\n"
            "# Middlewares are not required to run an EFB profile. If you are not\n"
            "# going to use any middleware in this profile, you can safely remove\n"
            "# this section. Otherwise, please list down the module ID and instance\n"
            "# ID of each middleware to be enabled below.\n"
        ) + "middlewares: []\n"

    def load_config(self):
        coordinator.profile = self.profile
        conf_path = utils.get_config_path()
        if not os.path.exists(conf_path):
            self.config = self.yaml.load(self.default_config())

            # Fill in required fields
            if "master_channel" not in self.config:
                self.config['master_channel'] = ""
            if "slave_channels" not in self.config:
                self.config["slave_channels"] = []
            if "middlewares" not in self.config:
                self.config["middlewares"] = []
        else:
            with open(conf_path) as f:
                self.config = self.yaml.load(f)
        self.load_modules_list()

    def save_config(self):
        coordinator.profile = self.profile
        conf_path = utils.get_config_path()
        if not os.path.exists(conf_path):
            os.makedirs(os.path.dirname(conf_path))
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
                self.modules[i.name].replace(wizard=fn)

    def get_master_id_tuples(self):
        return [(i.name, i.id) for i in self.modules.values()
                if i.type == "master"]

    def get_slave_id_tuples(self):
        return [(i.name, i.id) for i in self.modules.values() if i.type == "slave"]

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
            return None
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
            return None
        return callable(self.modules[mid].wizard)

    def get_selected_slave_id_tuples(self):
        if 'slave_channels' not in self.config:
            self.config['slave_channels'] = []
            return []
        i = 0
        res = []
        while i < len(self.config['slave_channels']):
            cid = self.config['slave_channels'][i]
            mid, _ = self.split_cid(cid)

            if mid not in self.modules or self.modules[mid].type != "slave":
                self.config['slave_channels'].pop(i)
            else:
                i += 1
                name = self.get_instance_display_name(cid)
                res.append((name, cid))
        return res

    def get_middleware_id_tuples(self):
        return [(i.name, i.id) for i in self.modules.values() if i.type == "middleware"]

    def get_selected_middleware_id_tuples(self):
        if 'middlewares' not in self.config:
            self.config['middlewares'] = []
            return []
        i = 0
        res = []
        while i < len(self.config['middlewares']):
            cid = self.config['middlewares'][i]
            mid, _ = self.split_cid(cid)

            if mid not in self.modules or self.modules[mid].type != "middleware":
                self.config['middlewares'].pop(i)
            else:
                i += 1
                name = self.get_instance_display_name(cid)
                res.append((name, cid))
        return res


class ModuleEntryView(Frame):

    def __init__(self, screen, data, mtype, index, mode, on_close=None):
        # self.palette['background'] = (Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLUE)

        if mtype == "slave" and mode == "add":
            title = _("Add a new slave channel")
        elif mtype == "slave" and mode == "edit":
            title = _("Edit a slave channel entry")
        elif mtype == "middleware" and mode == "add":
            title = _("Add a new middleware")
        elif mtype == "middleware" and mode == "edit":
            title = _("Edit a middleware entry")
        else:
            raise ValueError("Unknown mtype and mode pair: %s, %s", mtype, mode)

        super(ModuleEntryView, self) \
            .__init__(screen,
                      min(screen.height, 15), min(screen.width, 75),
                      hover_focus=True,
                      is_modal=True,
                      title=title,
                      reduce_cpu=True
                      )

        self.set_theme("bright")
        self._model = data  # type: DataModel
        self._mtype = mtype  # type: str
        self._index = index
        self._mode = mode
        self._on_close = on_close
        layout = Layout([1])
        self.add_layout(layout)

        module_kv = []
        label = ""
        if mtype == "slave":
            module_kv = self._model.get_slave_id_tuples()
            label = _("Slave channel")
        elif mtype == 'middleware':
            module_kv = self._model.get_middleware_id_tuples()
            label = _("Middleware")

        self.modules = RadioButtons(
            module_kv,
            label=label,
            name="modules"
        )
        layout.add_widget(self.modules)

        self.instance = Text(
            _("Instance ID"),
            "instance_id",
        )
        layout.add_widget(self.instance)

        layout.add_widget(Label(_("Leave this blank to use the default instance."), 3))

        layout.add_widget(Divider(height=2))
        layout.add_widget(Button(_("Save"), self._save))

        if mode == "edit":
            if mtype == "slave":
                c = self._model.config['slave_channels'][index].split("#")
            else:  # mtype == "middleware"
                c = self._model.config['middlewares'][index].split("#")
            self.modules.value = c[0]
            if len(c) > 1:
                self.instance.value = c[1]
        self.fix()

    def _save(self):
        val = self.modules.value
        name = self._model.modules[val].name

        if self.instance.value:
            val += "#" + self.instance.value

        if self._mtype == "slave":
            dest = self._model.config['slave_channels']
        else:  # self._mode == "edit"
            dest = self._model.config['middlewares']

        if self._mode == "add":
            if val in dest:
                return
            dest.insert(self._index, "")
        else:  # mode == edit
            if val in dest[:self._index] or val in dest[self._index + 1:]:
                dest.pop(self._index)
                return

        dest[self._index] = val
        dest.yaml_add_eol_comment(name, self._index)

        self._scene.remove_effect(self)
        if self._on_close:
            self._on_close()


class ModulesView(Frame):
    def __init__(self, screen, data):
        """
        Args:
            screen (Screen): Screen
            data (DataModel): Data model
        """
        super(ModulesView, self).__init__(screen, min(screen.height, 43), min(screen.width, 132),
                                          hover_focus=True,
                                          title=_("Choose modules"),
                                          reduce_cpu=True)

        self._model = data
        self.set_theme("bright")
        master_layout = Layout([6, 4])
        self.add_layout(master_layout)

        self.master_channel = RadioButtons(
            self._model.get_master_id_tuples(),
            label=_("Master channel"),
            name="master_channel"
        )
        if "master_channel" in self._model.config and \
                self._model.config['master_channel'] in self._model.modules and \
                self._model.modules[self._model.config['master_channel']].type == "master":
            self.master_channel.value = self._model.config['master_channel']
        master_layout.add_widget(self.master_channel, 0)
        self.master_instance = Text(_("Instance ID"), "master_channel_instance")
        master_layout.add_widget(self.master_instance, 1)
        master_layout.add_widget(Label(_("Leave this blank to use the default instance."), 3), 1)

        layout = Layout([1])
        self.add_layout(layout)
        layout.add_widget(Label("", 3))

        slave_layout = Layout([8, 2])
        self.add_layout(slave_layout)
        slave_layout.add_widget(Label(_("Slave channels")), 0)
        self.slave_channels = ListBox(
            Widget.FILL_COLUMN,
            self._model.get_selected_slave_id_tuples(),
            name="slave_channels",
            add_scroll_bar=True
        )
        slave_layout.add_widget(self.slave_channels, 0)
        slave_layout.add_widget(Button(_("Add"), self.edit_popup("slave", "add")), 1)
        slave_layout.add_widget(Button(_("Edit"), self.edit_popup("slave", "edit")), 1)
        slave_layout.add_widget(Button(_("Up"), self.shift("slave", is_up=True)), 1)
        slave_layout.add_widget(Button(_("Down"), self.shift("slave", is_up=False)), 1)
        slave_layout.add_widget(Button(_("Remove"), self.delete("slave")), 1)

        layout = Layout([1])
        self.add_layout(layout)
        layout.add_widget(Label("", 3))

        middleware_layout = Layout([8, 2])
        self.add_layout(middleware_layout)
        middleware_layout.add_widget(Label(_("Middlewares")), 0)
        self.middlewares = ListBox(
            Widget.FILL_COLUMN,
            self._model.get_selected_middleware_id_tuples(),
            name="middlewares",
            add_scroll_bar=True
        )
        middleware_layout.add_widget(self.middlewares, 0)
        middleware_layout.add_widget(Button(_("Add"), self.edit_popup("middleware", "add")), 1)
        middleware_layout.add_widget(Button(_("Edit"), self.edit_popup("middleware", "edit")), 1)
        middleware_layout.add_widget(Button(_("Up"), self.shift("middleware", is_up=True)), 1)
        middleware_layout.add_widget(Button(_("Down"), self.shift("middleware", is_up=False)), 1)
        middleware_layout.add_widget(Button(_("Remove"), self.delete("middleware")), 1)

        confirm_layout = Layout([1])
        self.add_layout(confirm_layout)
        confirm_layout.add_widget(Divider(height=4))
        confirm_layout.add_widget(Button(_("Next"), self._ok))
        self.fix()

    def _ok(self):
        self.save()

        # Check if the current configuration is valid
        if len(self.slave_channels.options) < 1:
            self.show_popup(_("You must enable at least one slave channel."))
            return

        options = list(map(repr, self.slave_channels.options))
        if len(options) != len(set(options)):
            self.show_popup(_("Duplicate instances detected in slave channel settings. "
                              "Each module-instance pair must be unique."))
            return

        options = list(map(repr, self.middlewares.options))
        if len(options) != len(set(options)):
            self.show_popup(_("Duplicate instances detected in middleware settings. "
                              "Each module-instance pair must be unique."))
            return

        self._model.save_config()
        raise NextScene("ModulesSetup")

    def show_popup(self, message):
        self._scene.add_effect(PopUpDialog(
            self.screen,
            message,
            [_("OK")]
        ))

    def edit_popup(self, mtype, mode):
        def on_add_edit():
            if mtype == "slave":
                on_close = self.update_slaves_list
                index = self.slave_channels._line
                l = self.slave_channels.options
            else:  # mtype == "middleware":
                on_close = self.update_middleware_list
                index = self.middlewares._line
                l = self.middlewares.options

            if len(l) == 0:
                return

            self._scene.add_effect(ModuleEntryView(self.screen, self._model, mtype,
                                                   index, mode, on_close))
        return on_add_edit

    def shift(self, mtype, is_up=False):
        def on_shift():
            if mtype == "slave":
                l = self._model.config["slave_channels"]
                control = self.slave_channels
                update = self.update_slaves_list
            else:  # mtype == "middleware"
                l = self._model.config["middlewares"]
                control = self.middlewares
                update = self.update_middleware_list
            index = control._line
            if (is_up and index <= 0) or (not is_up and index >= len(l) - 1):
                return
            if is_up:
                l[index], l[index - 1] = l[index - 1], l[index]
            else:
                l[index], l[index + 1] = l[index + 1], l[index]
            update()
            control._line += -1 if is_up else 1
            control.value = control.options[control._line][1]
        return on_shift

    def delete(self, mtype):
        def on_delete():
            if mtype == "slave":
                l = self._model.config["slave_channels"]
                index = self.slave_channels._line
                update = self.update_slaves_list
            else:  # mtype == "middleware"
                l = self._model.config["middlewares"]
                index = self.middlewares._line
                update = self.update_middleware_list
            if len(l) < 1:
                return
            index = max(0, min(index, len(l) - 1))
            l.pop(index)
            update()
        return on_delete

    def update_slaves_list(self):
        self.slave_channels.options = self._model.get_selected_slave_id_tuples()

    def update_middleware_list(self):
        self.middlewares.options = self._model.get_selected_middleware_id_tuples()


class StartupView(Frame):
    def __init__(self, screen, data):
        super(StartupView, self).__init__(screen, min(screen.height, 43), min(screen.width, 132),
                                          hover_focus=True,
                                          title=_("EH Forwarder Bot Setup Wizard"),
                                          reduce_cpu=True)

        self._model = data
        self.set_theme("bright")
        layout = Layout([100], fill_frame=True)
        self.add_layout(layout)
        label_text = _("Checking Python version... OK\n"
                       "Checking master channels... OK\n"
                       "Checking slave channels... OK\n"
                       "\n"
                       "Welcome to EH Forwarder Bot Setup Wizard.  This program "
                       "will guide you to finish up the last few steps to "
                       "get EFB ready to use.\n"
                       "\n"
                       "To use this wizard in another supported language, "
                       "please change your system language or modify the "
                       "language environment variable and restart the wizard.\n"
                       "\n"
                       "Confirm the profile name to use below and "
                       "select \"Next\" to continue.\n\n")
        h = get_height(label_text, screen.width)
        layout.add_widget(Label(label_text, height=h))

        self.profile = Text("Profile", "profile")
        self.profile.value = self._model.profile
        layout.add_widget(self.profile)
        layout.add_widget(Divider(height=4))

        layout.add_widget(Button(_("Next"), self._ok))
        self.fix()

    def _ok(self):
        self.save()
        self._model.profile = self.data['profile']
        self._model.load_config()
        raise NextScene("Modules")


class ModulesSetupView(Frame):
    def __init__(self, screen, data):
        super(ModulesSetupView, self).__init__(screen, min(screen.height, 43), min(screen.width, 132),
                                               hover_focus=True,
                                               title=_("EH Forwarder Bot Setup Wizard"),
                                               reduce_cpu=True)

        self._model = data  # type: DataModel
        self.set_theme("bright")
        layout = Layout([1], fill_frame=True)
        self.add_layout(layout)
        label_text = _("You have chosen to enable the following modules for profile \"{0}\".\n"
                       "\n"
                       "Master channel: {1}").format(
            self._model.profile,
            self._model.get_instance_display_name(self._model.config['master_channel'])
        )

        label_text += "\n\n" + \
                      ngettext("Slave channel:", "Slave channels:", len(self._model.config['slave_channels'])) + "\n"
        for i in self._model.config['slave_channels']:
            label_text += '- ' + self._model.get_instance_display_name(i) + "\n"

        num_middlewares = len(self._model.config.get('middlewares', []))
        if num_middlewares > 0:
            label_text += '\n\n' + \
                ngettext("Middleware:", "Middlewares:")
            for i in self._model.config['middlewares']:
                label_text += '- ' + self._model.get_instance_display_name(i) + "\n"

        modules_count = 1
        missing_wizards = []
        if not self._model.has_wizard(self._model.config['master_channel']):
            missing_wizards.append(self._model.config['master_channel'])
        for i in self._model.config['slave_channels']:
            modules_count += 1
            if not self._model.has_wizard(i):
                missing_wizards.append(i)
        for i in self._model.config['middlewares']:
            modules_count += 1
            if not self._model.has_wizard(i):
                missing_wizards.append(i)

        if missing_wizards:
            label_text += "\n" + \
                ngettext("Note:\n"
                         "The following module does not have a setup wizard. It is probably because "
                         "that it does not need to be set up, or it requires you to set up manually.\n"
                         "Please consult its documentation for further details.\n",
                         "Note:\n"
                         "The following modules do not have a setup wizard. It is probably because "
                         "that they do not need to be set up, or they require you to set up manually.\n"
                         "Please consult their documentations respectively for further details.\n",
                         len(missing_wizards))
            for i in missing_wizards:
                label_text += "- " + self._model.get_instance_display_name(i) + "\n"

        label_text += "\n"
        if len(missing_wizards) == modules_count:
            label_text += _("If you are happy with this settings, you may finish this wizard now, and "
                            "continue to configure other modules if necessary. Otherwise, you can also "
                            "go back to change your module settings again.")
            button_text = _("Finish")
        else:
            label_text += _("If you are happy with this settings, this wizard will guide you to setup "
                            "modules you have enabled. Otherwise, you can also go back to change your "
                            "module settings again.")
            button_text = _("Continue")

        h = get_height(label_text, screen.width) + 3
        layout.add_widget(Label(label_text, height=h))

        layout.add_widget(Button(_("Back"), self._back))
        layout.add_widget(Button(button_text, self._ok))
        self.fix()

    @staticmethod
    def _back():
        raise NextScene("Modules")

    @staticmethod
    def _ok():
        raise StopApplication("Continue")


def screen(scr, scene, data):
    scene_decorators = [StartupView(scr, data)]
    result = prerequisite_check()
    if result:
        scene_decorators.append(PopUpDialog(
            scr,
            result,
            [_("OK")],
            on_close=stop_wizard
        ))
    scenes = [Scene(scene_decorators, -1, name="Welcome"),
              Scene([ModulesView(scr, data)], -1, name="Modules"),
              Scene([ModulesSetupView(scr, data)], -1, name="ModulesSetup")]
    scene = scene or scenes[0]
    scr.play(scenes, stop_on_resize=True, start_scene=scene)


def stop_wizard(_):
    raise StopApplication('')


def get_platform_name():
    p = platform.system()
    if p == "Linux":
        # noinspection PyBroadException
        try:
            # noinspection PyDeprecation
            return ' '.join(platform.linux_distribution()[:2])
        except:
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
    if sys.version_info < (3, 6):
        version_str = "%s.%s.%s" % sys.version_info[:3]
        # TRANSLATORS: This word is used as a part of search query suggested to users,
        # it may appears in context like "Ubuntu 16.04 install Python 3.7"
        search_url = build_search_query(_("install") + " Python 3.7")
        return _("EH Forwarder Bot requires a minimum of Python 3.6 to run.  You "
                 "are currently using Python {version}. \n"
                 "\n"
                 "You may want to try:\n"
                 "{url}").format(version=version_str, url=search_url)

    # Check installations of modules
    modules_err = _("You may want to visit the modules repository to find a list of "
                    "available modules to install.\n"
                    "https://github.com/blueset/ehForwarderBot/wiki/Channels-Repository")
    # 1. At least 1 master channel must be installed
    try:
        next(pkg_resources.iter_entry_points("ehforwarderbot.master"))
    except StopIteration:
        return _("No master channel detected.  EH Forwarder Bot requires at least one "
                 "master channel to run.") + "\n\n" + modules_err

    # 2. At least 1 slave channel must be installed
    try:
        next(pkg_resources.iter_entry_points("ehforwarderbot.slave"))
    except StopIteration:
        return _("No slave channel detected.  EH Forwarder Bot requires at least one "
                 "slave channel to run.") + "\n\n" + modules_err


def main():
    data = DataModel()
    data.load_config()
    last_scene = None
    while True:
        try:
            Screen.wrapper(screen,
                           arguments=[last_scene, data])
            break
        except ResizeScreenError as e:
            last_scene = e.scene
        except StopApplication:
            break

    modules = [data.config['master_channel']]
    modules.extend(data.config['slave_channels'])
    if 'middlewares' in data.config:
        modules.extend(data.config['middlewares'])
    for i in modules:
        mid, cid = data.split_cid(i)
        if callable(data.modules[mid].wizard):
            print(_("Press ENTER/RETURN to start setting up {0}.").format(i))
            input()
            data.modules[mid].wizard(data.profile, cid)


if __name__ == '__main__':
    main()
