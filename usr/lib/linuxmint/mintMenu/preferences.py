#!/usr/bin/python3

import gettext
import glob
import locale
import setproctitle

import gi
gi.require_version("Gtk", "3.0")
gi.require_version('XApp', '1.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, XApp

import keybinding
from xapp.GSettingsWidgets import *

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")
locale.bindtextdomain("mintmenu", "/usr/share/linuxmint/locale")
locale.textdomain("mintmenu")

class CustomPlaceDialog (Gtk.Dialog):

    def __init__(self):
        Gtk.Dialog.__init__(self, title=_("Custom Place"), flags=Gtk.DialogFlags.MODAL,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK))
        self.set_default_size(150, 100)

        grid = Gtk.Grid()
        grid.set_row_spacing(12)
        grid.set_column_spacing(12)
        grid.set_border_width(12)

        self.name = Gtk.Entry()
        grid.attach(Gtk.Label(_("Name:")), 0, 0, 1, 1)
        grid.attach(self.name, 1, 0, 1, 1)

        self.filechooser_button = Gtk.FileChooserButton()
        self.filechooser_button.set_title(_("Select a folder"))
        self.filechooser_button.set_action(Gtk.FileChooserAction.SELECT_FOLDER)
        grid.attach(Gtk.Label(_("Folder:")), 0, 1, 1, 1)
        grid.attach(self.filechooser_button, 1, 1, 1, 1)

        self.get_content_area().add(grid)

        self.show_all()

class mintMenuPreferences():

    def __init__(self):

        self.settings = Gio.Settings("com.linuxmint.mintmenu")
        self.places_settings = Gio.Settings("com.linuxmint.mintmenu.plugins.places")

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("mintmenu")
        self.builder.add_from_file("/usr/share/linuxmint/mintmenu/preferences.ui")

        self.window = self.builder.get_object("main_window")
        self.window.set_title(_("Menu preferences"))
        self.window.set_icon_name("linuxmint-logo")
        self.window.connect("destroy", Gtk.main_quit)

        page = SettingsPage()
        self.builder.get_object("box_general").add(page)

        section = page.add_section(_("Menu button"), _("Applet button in the panel"))
        section.add_row(GSettingsSwitch(_("Show button icon"), "com.linuxmint.mintmenu", "show-applet-icon"))
        section.add_reveal_row(GSettingsEntry(_("Button text"), "com.linuxmint.mintmenu", "applet-text"), "com.linuxmint.mintmenu", "show-applet-icon")
        section.add_reveal_row(GSettingsIconChooser(_("Button icon"), "com.linuxmint.mintmenu", "applet-icon"), "com.linuxmint.mintmenu", "show-applet-icon")

        binding_widget = keybinding.KeybindingWidget()
        binding_widget.set_val(self.settings.get_string("hot-key"))
        binding_widget.connect("accel-edited", self.set_keyboard_shortcut)
        label = SettingsLabel(_("Keyboard shortcut"))
        setting_widget = SettingsWidget()
        setting_widget.pack_start(label, False, False, 0)
        setting_widget.pack_end(binding_widget, False, False, 0)
        section.add_row(setting_widget)

        section = page.add_section(_("Options"), _("General applet options"))
        self.system_switch = Switch(_("Show system management"))
        self.system_switch.content_widget.connect("notify::active", self.set_plugins)
        section.add_row(self.system_switch)
        self.places_switch = Switch(_("Show places"))
        self.places_switch.content_widget.connect("notify::active", self.set_plugins)
        section.add_row(self.places_switch)
        self.recent_switch = Switch(_("Show recently used documents and applications"))
        self.recent_switch.content_widget.connect("notify::active", self.set_plugins)
        section.add_row(self.recent_switch)
        self.set_plugins_switches()
        section.add_row(GSettingsSwitch(_("Show tooltips"), "com.linuxmint.mintmenu", "tooltips-enabled"))

        page = SettingsPage()
        self.builder.get_object("box_appearance").add(page)
        section = page.add_section(_("Theme"), _("Custom theme selection"))
        options = []
        options.append(["default", _("Desktop theme"), "default"])
        themes = glob.glob("/usr/share/themes/*/*/gtkrc")
        for theme in sorted(themes):
            if theme.startswith("/usr/share/themes") and theme.endswith("/gtk-2.0/gtkrc"):
                theme = theme.replace("/usr/share/themes/", "")
                theme = theme.replace("gtk-2.0", "")
                theme = theme.replace("gtkrc", "")
                theme = theme.replace("/", "")
                theme = theme.strip()
                options.append([theme, theme])
        section.add_row(GSettingsComboBox(_("Theme:"), "com.linuxmint.mintmenu", "theme-name", options))

        section = page.add_section(_("Icon sizes"), _("The size of the icons"))
        section.add_row(GSettingsSpinButton(_("Favorites"), "com.linuxmint.mintmenu.plugins.applications", "favicon-size", mini=1, maxi=128, step=1, page=2))
        section.add_row(GSettingsSpinButton(_("Applications"), "com.linuxmint.mintmenu.plugins.applications", "icon-size", mini=1, maxi=128, step=1, page=2))
        section.add_row(GSettingsSpinButton(_("System"), "com.linuxmint.mintmenu.plugins.system_management", "icon-size", mini=1, maxi=128, step=1, page=2))
        section.add_row(GSettingsSpinButton(_("Places"), "com.linuxmint.mintmenu.plugins.places", "icon-size", mini=1, maxi=128, step=1, page=2))

        page = SettingsPage()
        self.builder.get_object("box_applications").add(page)

        section = page.add_section(_("Layout"), _("Section layout"))
        section.add_row(GSettingsSwitch(_("Show search bar on top"), "com.linuxmint.mintmenu.plugins.applications", "search-on-top"))
        section.add_row(GSettingsSwitch(_("Show applications comments"), "com.linuxmint.mintmenu.plugins.applications", "show-application-comments"))

        section = page.add_section(_("Categories"), _("Applications categories"))
        section.add_row(GSettingsSwitch(_("Show category icons"), "com.linuxmint.mintmenu.plugins.applications", "show-category-icons"))
        section.add_row(GSettingsSwitch(_("Switch categories on hover"), "com.linuxmint.mintmenu.plugins.applications", "categories-mouse-over"))
        section.add_reveal_row(GSettingsSpinButton(_("Hover delay"), "com.linuxmint.mintmenu.plugins.applications", "category-hover-delay", units=_("milliseconds"), mini=1, maxi=500, step=1, page=10), "com.linuxmint.mintmenu.plugins.applications", "categories-mouse-over")

        section = page.add_section(_("Search"), _("Search options"))
        section.add_row(GSettingsSwitch(_("Search for packages to install"), "com.linuxmint.mintmenu.plugins.applications", "use-apt"))
        section.add_row(GSettingsSwitch(_("Remember the last category or search"), "com.linuxmint.mintmenu.plugins.applications", "remember-filter"))
        section.add_row(GSettingsSwitch(_("Enable Internet search"), "com.linuxmint.mintmenu.plugins.applications", "enable-internet-search"))
        section.add_row(GSettingsEntry(_("Search command"), "com.linuxmint.mintmenu.plugins.applications", "search-command"))

        page = SettingsPage()
        self.builder.get_object("box_favorites").add(page)

        section = page.add_section(_("Layout"), _("Section layout"))
        section.add_row(GSettingsSpinButton(_("Number of columns"), "com.linuxmint.mintmenu.plugins.applications", "fav-cols", mini=1, maxi=5, step=1, page=1))
        section.add_row(GSettingsSwitch(_("Swap name and generic name"), "com.linuxmint.mintmenu.plugins.applications", "swap-generic-name"))
        section.add_row(GSettingsSwitch(_("Show favorites when the menu is open"), "com.linuxmint.mintmenu", "start-with-favorites"))

        page = SettingsPage()
        self.builder.get_object("box_system").add(page)

        section = page.add_section(_("Layout"), _("Section layout"))
        section.add_row(GSettingsSwitch(_("Custom height"), "com.linuxmint.mintmenu.plugins.system_management", "allow-scrollbar"))
        section.add_reveal_row(GSettingsSpinButton(_("Height"), "com.linuxmint.mintmenu.plugins.system_management", "height", mini=1, maxi=800, step=1, page=2), "com.linuxmint.mintmenu.plugins.system_management", "allow-scrollbar")

        section = page.add_section(_("Items"), _("Toggle default items"))
        section.add_row(GSettingsSwitch(_("Software Manager"), "com.linuxmint.mintmenu.plugins.system_management", "show-software-manager"))
        section.add_row(GSettingsSwitch(_("Package Manager"), "com.linuxmint.mintmenu.plugins.system_management", "show-package-manager"))
        section.add_row(GSettingsSwitch(_("Control Center"), "com.linuxmint.mintmenu.plugins.system_management", "show-control-center"))
        section.add_row(GSettingsSwitch(_("Terminal"), "com.linuxmint.mintmenu.plugins.system_management", "show-terminal"))
        section.add_row(GSettingsSwitch(_("Lock Screen"), "com.linuxmint.mintmenu.plugins.system_management", "show-lock-screen"))
        section.add_row(GSettingsSwitch(_("Logout"), "com.linuxmint.mintmenu.plugins.system_management", "show-logout"))
        section.add_row(GSettingsSwitch(_("Quit"), "com.linuxmint.mintmenu.plugins.system_management", "show-quit"))

        page = SettingsPage()
        self.builder.get_object("box_places").add(page)

        section = page.add_section(_("Layout"), _("Section layout"))
        section.add_row(GSettingsSwitch(_("Custom height"), "com.linuxmint.mintmenu.plugins.places", "allow-scrollbar"))
        section.add_reveal_row(GSettingsSpinButton(_("Height"), "com.linuxmint.mintmenu.plugins.places", "height", mini=1, maxi=800, step=1, page=2), "com.linuxmint.mintmenu.plugins.places", "allow-scrollbar")

        section = page.add_section(_("Items"), _("Toggle default items"))
        section.add_row(GSettingsSwitch(_("Computer"), "com.linuxmint.mintmenu.plugins.places", "show-computer"))
        section.add_row(GSettingsSwitch(_("Home Folder"), "com.linuxmint.mintmenu.plugins.places", "show-home-folder"))
        section.add_row(GSettingsSwitch(_("Network"), "com.linuxmint.mintmenu.plugins.places", "show-network"))
        section.add_row(GSettingsSwitch(_("Desktop"), "com.linuxmint.mintmenu.plugins.places", "show-desktop"))
        section.add_row(GSettingsSwitch(_("Trash"), "com.linuxmint.mintmenu.plugins.places", "show-trash"))
        section.add_row(GSettingsSwitch(_("GTK Bookmarks"), "com.linuxmint.mintmenu.plugins.places", "show-gtk-bookmarks"))

        section = page.add_section(_("Custom places"), _("You can add your own places in the menu"))
        box = self.builder.get_object("custom_places_box")
        section.add(box)
        self.custom_places_tree = self.builder.get_object("custom_places_tree")
        self.custom_places_paths = self.places_settings.get_strv("custom-paths")
        self.custom_places_names = self.places_settings.get_strv("custom-names")
        self.custom_places_model = Gtk.ListStore(str, str)
        self.cell = Gtk.CellRendererText()
        for count in range(len(self.custom_places_paths)):
            self.custom_places_model.append([self.custom_places_names[count], self.custom_places_paths[count]])
        self.custom_places_model.connect("row-inserted", self.save_custom_places)
        self.custom_places_model.connect("row-deleted", self.save_custom_places)
        self.custom_places_model.connect("rows-reordered", self.save_custom_places)
        self.custom_places_model.connect("row-changed", self.save_custom_places)
        self.custom_places_tree.set_model(self.custom_places_model)
        self.custom_places_tree.append_column(Gtk.TreeViewColumn(_("Name"), self.cell, text=0))
        self.custom_places_tree.append_column(Gtk.TreeViewColumn(_("Path"), self.cell, text=1))
        self.builder.get_object("newButton").connect("clicked", self.add_custom_place)
        self.builder.get_object("editButton").connect("clicked", self.edit_custom_place)
        self.builder.get_object("upButton").connect("clicked", self.move_up)
        self.builder.get_object("downButton").connect("clicked", self.move_down)
        self.builder.get_object("removeButton").connect("clicked", self.remove_custom_place)

        self.window.show_all()
        return

    def set_keyboard_shortcut(self, widget):
        self.settings.set_string("hot-key", widget.get_val())

    def set_plugins_switches(self):
        plugins = self.settings.get_strv("plugins-list")
        self.recent_switch.content_widget.set_active("recent" in plugins)
        self.system_switch.content_widget.set_active("system_management" in plugins)
        self.places_switch.content_widget.set_active("places" in plugins)

    def set_plugins(self, widget, param):
        visible_plugins = []
        if self.places_switch.content_widget.get_active():
            visible_plugins.append("places")
        if self.system_switch.content_widget.get_active():
            visible_plugins.append("system_management")
        if self.places_switch.content_widget.get_active() or self.system_switch.content_widget.get_active():
            visible_plugins.append("newpane")
        visible_plugins.append("applications")
        if self.recent_switch.content_widget.get_active():
            visible_plugins.append("newpane")
            visible_plugins.append("recent")
        self.settings.set_strv("plugins-list", visible_plugins)

    def add_custom_place(self, newButton):
        dialog = CustomPlaceDialog()
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            name = dialog.name.get_text()
            path = dialog.filechooser_button.get_filename()
            if name and path and name != "":
                self.custom_places_model.append((name, path))
        dialog.destroy()
        return

    def edit_custom_place(self, editButton):
        dialog = CustomPlaceDialog()
        treeselection = self.custom_places_tree.get_selection()
        currentiter = treeselection.get_selected()[1]
        if currentiter:
            initName = self.custom_places_model.get_value(currentiter, 0)
            initPath = self.custom_places_model.get_value(currentiter, 1)
            dialog.name.set_text(initName)
            dialog.filechooser_button.set_filename(initPath)
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                name = dialog.name.get_text()
                path = dialog.filechooser_button.get_filename()
                if name and path and name != "":
                    self.custom_places_model.set_value(currentiter, 0, name)
                    self.custom_places_model.set_value(currentiter, 1, path)
            dialog.destroy()

    def move_up(self, upButton):
        treeselection = self.custom_places_tree.get_selection()
        currentiter = treeselection.get_selected()[1]
        if treeselection:
            lagiter = self.custom_places_model.get_iter_first()
            nextiter = self.custom_places_model.get_iter_first()
            while nextiter and self.custom_places_model.get_path(nextiter) != \
                               self.custom_places_model.get_path(currentiter):
                lagiter = nextiter
                nextiter = self.custom_places_model.iter_next(nextiter)
            if nextiter:
                self.custom_places_model.swap(currentiter, lagiter)
        return

    def move_down(self, downButton):
        treeselection = self.custom_places_tree.get_selection()
        currentiter = treeselection.get_selected()[1]
        nextiter = self.custom_places_model.iter_next(currentiter)
        if nextiter:
            self.custom_places_model.swap(currentiter, nextiter)
        return

    def remove_custom_place(self, removeButton):
        treeselection = self.custom_places_tree.get_selection()
        currentiter = treeselection.get_selected()[1]
        if currentiter:
            self.custom_places_model.remove(currentiter)
        return

    def save_custom_places(self, treemodel, path, iter = None, new_order = None):
        if not iter or self.custom_places_model.get_value(iter, 1):
            treeiter = self.custom_places_model.get_iter_first()
            custom_places_names = []
            custom_places_paths = []
            while treeiter:
                custom_places_names = custom_places_names + [self.custom_places_model.get_value(treeiter, 0)]
                custom_places_paths = custom_places_paths + [self.custom_places_model.get_value(treeiter, 1)]
                treeiter = self.custom_places_model.iter_next(treeiter)
            self.places_settings.set_strv("custom-paths", custom_places_paths)
            self.places_settings.set_strv("custom-names", custom_places_names)

if __name__ == "__main__":
    setproctitle.setproctitle('mintmenu-preferences')
    preferences = mintMenuPreferences()
    Gtk.main()
