#!/usr/bin/python3

import gettext
import os
import locale

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gio

from plugins.easybuttons import easyButton
from plugins.execute import Execute

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")
locale.bindtextdomain("mintmenu", "/usr/share/linuxmint/locale")
locale.textdomain("mintmenu")

class pluginclass(object):

    def __init__(self, mintMenuWin, toggleButton, de):

        self.mintMenuWin = mintMenuWin
        self.toggleButton = toggleButton
        self.de = de

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("mintmenu")
        self.builder.add_from_file("/usr/share/linuxmint/mintmenu/system.ui")

        self.systemBtnHolder    = self.builder.get_object("system_button_holder")
        self.editableBtnHolder  = self.builder.get_object("editable_button_holder")
        self.scrolledWindow = self.builder.get_object("scrolledwindow2")

        # These properties are NECESSARY to maintain consistency

        # Set 'window' property for the plugin (Must be the root widget)
        self.window = self.builder.get_object("mainWindow")

        # Set 'heading' property for plugin
        self.heading = _("System")

        # This should be the first item added to the window in glade
        self.content_holder = self.builder.get_object("System")

        # Gconf stuff
        self.settings = Gio.Settings("com.linuxmint.mintmenu.plugins.system_management")

        self.settings.connect("changed::icon-size", self.RegenPlugin)
        self.settings.connect("changed::show-control-center", self.RegenPlugin)
        self.settings.connect("changed::show-lock-screen", self.RegenPlugin)
        self.settings.connect("changed::show-logout", self.RegenPlugin)
        self.settings.connect("changed::show-package-manager", self.RegenPlugin)
        self.settings.connect("changed::show-software-manager", self.RegenPlugin)
        self.settings.connect("changed::show-terminal", self.RegenPlugin)
        self.settings.connect("changed::show-quit", self.RegenPlugin)
        self.settings.connect("changed::allow-scrollbar", self.RegenPlugin)
        self.settings.connect("changed::height", self.changePluginSize)
        self.settings.connect("changed::width", self.changePluginSize)

        self.GetGSettingsEntries()

        self.content_holder.set_size_request(self.width, self.height)

    def wake(self):
        pass

    def changePluginSize(self, settings, key, args):
        self.allowScrollbar = self.settings.get_boolean("allow-scrollbar")
        if key == "width":
            self.width = settings.get_int(key)
        elif key == "height":
            if not self.allowScrollbar:
                self.height = -1
                self.scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
            else:
                self.scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
                self.height = settings.get_int(key)

        self.content_holder.set_size_request(self.width, self.height)


    def RegenPlugin(self, *args, **kargs):
        self.GetGSettingsEntries()
        self.ClearAll()
        self.do_standard_items()

    def GetGSettingsEntries(self):

        self.width = self.settings.get_int("width")
        self.allowScrollbar = self.settings.get_boolean("allow-scrollbar")
        self.scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.height = self.settings.get_int("height")
        self.content_holder.set_size_request(self.width, self.height)
        if not self.allowScrollbar:
            self.height = -1
            self.scrolledWindow.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER)
        self.content_holder.set_size_request(self.width, self.height)
        self.iconsize = self.settings.get_int("icon-size")

        # Check toggles
        self.showSoftwareManager = self.settings.get_boolean("show-software-manager")
        self.showPackageManager = self.settings.get_boolean("show-package-manager")
        self.showControlCenter = self.settings.get_boolean("show-control-center")
        self.showTerminal = self.settings.get_boolean("show-terminal")
        self.showLockScreen = self.settings.get_boolean("show-lock-screen")
        self.showLogout = self.settings.get_boolean("show-logout")
        self.showQuit = self.settings.get_boolean("show-quit")

        if self.de == "cinnamon":
            self.lock_cmd = "cinnamon-screensaver-command --lock"
            self.logout_cmd = "cinnamon-session-quit --logout"
            self.shutdown_cmd = "cinnamon-session-quit --power-off"
            self.terminal_cmd = "/usr/bin/gnome-terminal"
            self.settings_cmd = "cinnamon-settings"
        elif self.de == "xfce":
            self.lock_cmd = "xdg-screensaver lock"
            self.logout_cmd = "xfce4-session-logout"
            self.shutdown_cmd = ""
            self.terminal_cmd = "/usr/bin/gnome-terminal"
            self.settings_cmd = "xfce4-settings-manager"
            self.showLockScreen = False
            self.showQuit = False
        else:
            self.lock_cmd = "mate-screensaver-command -l"
            self.logout_cmd = "mate-session-save --logout-dialog"
            self.shutdown_cmd = "mate-session-save --shutdown-dialog"
            self.terminal_cmd = "/usr/bin/mate-terminal"
            self.settings_cmd = "mate-control-center"

        # Hide vertical dotted separator
        self.hideseparator = self.settings.get_boolean("hide-separator")
        # Plugin icon
        self.icon = self.settings.get_string("icon")

    def ClearAll(self):
        for child in self.systemBtnHolder.get_children():
            child.destroy()
        for child in self.editableBtnHolder.get_children():
            child.destroy()

    #Add standard items
    def do_standard_items(self):

        if self.showSoftwareManager:
            if os.path.exists("/usr/bin/mintinstall"):
                Button1 = easyButton("mintinstall", self.iconsize, [_("Software Manager")], -1, -1)
                Button1.connect("clicked", self.ButtonClicked, "mintinstall")
                Button1.show()
                self.systemBtnHolder.pack_start(Button1, False, False, 0)
                self.mintMenuWin.setTooltip(Button1, _("Browse and install available software"))

        if self.showPackageManager:
            Button2 = easyButton("applications-system", self.iconsize, [_("Package Manager")], -1, -1)
            Button2.connect("clicked", self.ButtonClicked, "synaptic-pkexec")
            Button2.show()
            self.systemBtnHolder.pack_start(Button2, False, False, 0)
            self.mintMenuWin.setTooltip(Button2, _("Install, remove and upgrade software packages"))

        if self.showControlCenter:
            Button3 = easyButton("gtk-preferences", self.iconsize, [_("Control Center")], -1, -1)
            Button3.connect("clicked", self.ButtonClicked, self.settings_cmd)
            Button3.show()
            self.systemBtnHolder.pack_start(Button3, False, False, 0)
            self.mintMenuWin.setTooltip(Button3, _("Configure your system"))

        if self.showTerminal:
            Button4 = easyButton("terminal", self.iconsize, [_("Terminal")], -1, -1)
            if os.path.exists(self.terminal_cmd):
                Button4.connect("clicked", self.ButtonClicked, self.terminal_cmd)
            else:
                Button4.connect("clicked", self.ButtonClicked, "x-terminal-emulator")
            Button4.show()
            self.systemBtnHolder.pack_start(Button4, False, False, 0)
            self.mintMenuWin.setTooltip(Button4, _("Use the command line"))

        if self.showLockScreen:
            Button5 = easyButton("system-lock-screen", self.iconsize, [_("Lock Screen")], -1, -1)
            Button5.connect("clicked", self.ButtonClicked, self.lock_cmd)
            Button5.show()
            self.systemBtnHolder.pack_start(Button5, False, False, 0)
            self.mintMenuWin.setTooltip(Button5, _("Requires password to unlock"))

        if self.showLogout:
            Button6 = easyButton("system-log-out", self.iconsize, [_("Logout")], -1, -1)
            Button6.connect("clicked", self.ButtonClicked, self.logout_cmd)
            Button6.show()
            self.systemBtnHolder.pack_start(Button6, False, False, 0)
            self.mintMenuWin.setTooltip(Button6, _("Log out or switch user"))

        if self.showQuit:
            Button7 = easyButton("system-shutdown", self.iconsize, [_("Quit")], -1, -1)
            Button7.connect("clicked", self.ButtonClicked, self.shutdown_cmd)
            Button7.show()
            self.systemBtnHolder.pack_start(Button7, False, False, 0)
            self.mintMenuWin.setTooltip(Button7, _("Shutdown, restart, suspend or hibernate"))

    def ButtonClicked(self, widget, Exec):
        self.mintMenuWin.hide()
        if Exec:
            Execute(Exec)

    def do_plugin(self):
        self.do_standard_items()
