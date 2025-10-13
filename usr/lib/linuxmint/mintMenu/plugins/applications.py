#!/usr/bin/python3

import html
import filecmp
import gettext
import locale
import os
import subprocess
import threading
import urllib.request, urllib.parse, urllib.error

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("MateMenu", "2.0")
gi.require_version("XApp", "1.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, Gio, GLib, MateMenu, XApp

import plugins.recentHelper as RecentHelper
from plugins.easybuttons import (ApplicationLauncher, CategoryButton,
                                 FavApplicationLauncher,
                                 MenuApplicationLauncher)

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")
locale.bindtextdomain("mintmenu", "/usr/share/linuxmint/locale")
locale.textdomain("mintmenu")

home = os.path.expanduser("~")

class PackageDescriptor():
    def __init__(self, name, summary, description):
        self.name = name
        self.summary = summary
        self.description = description

# import time
# def print_timing(func):
#     def wrapper(*arg):
#         t1 = time.time()
#         res = func(*arg)
#         t2 = time.time()
#         print('%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0))
#         return res
#     return wrapper

# Helper function for retrieving the user's location for storing new or modified menu items
def get_user_item_path():
    item_dir = None

    if 'XDG_DATA_HOME' in os.environ:
        item_dir = os.path.join(os.environ['XDG_DATA_HOME'], 'applications')
    else:
        item_dir = os.path.join(home, '.local/share/applications')

    if not os.path.isdir(item_dir):
        os.makedirs(item_dir)

    return item_dir

def get_system_item_paths():
    item_dirs = []
    if 'XDG_DATA_DIRS' in os.environ:
        item_dirs = os.environ['XDG_DATA_DIRS'].split(":")
    item_dirs.append(os.path.join('/usr', 'share'))
    return item_dirs

def rel_path(target, base=os.curdir):
    if not os.path.exists(target):
        raise OSError("Target does not exist: %s" % target)

    if not os.path.isdir(base):
        raise OSError("Base is not a directory or does not exist: %s" % base)

    base_list = (os.path.abspath(base)).split(os.sep)
    target_list = (os.path.abspath(target)).split(os.sep)

    for i in range(min(len(base_list), len(target_list))):
        if base_list[i] != target_list[i]:
            break
        else:
            i += 1

    rel_list = [os.pardir] * (len(base_list) - i) + target_list[i:]
    return os.path.join(*rel_list)

def get_contents(item):
    contents = []
    item_iter = item.iter()
    item_type = item_iter.next()

    while item_type != MateMenu.TreeItemType.INVALID:
        item = None
        if item_type == MateMenu.TreeItemType.DIRECTORY:
            item = item_iter.get_directory()
        elif item_type == MateMenu.TreeItemType.ENTRY:
            item = item_iter.get_entry()
        elif item_type == MateMenu.TreeItemType.HEADER:
            item = item_iter.get_header()
        elif item_type == MateMenu.TreeItemType.ALIAS:
            item = item_iter.get_alias()
        elif item_type == MateMenu.TreeItemType.SEPARATOR:
            item = item_iter.get_separator()
        if item:
            contents.append(item)
        item_type = item_iter.next()
    return contents

class Menu:

    def __init__(self, MenuToLookup):
        self.tree = MateMenu.Tree.new(MenuToLookup, MateMenu.TreeFlags.SORT_DISPLAY_NAME)
        self.tree.load_sync()
        self.directory = self.tree.get_root_directory()

    def getMenus(self, parent=None):
        if parent == None:
            #gives top-level "Applications" item
            yield self.tree.root
        else:
            for menu in get_contents(parent):
                if isinstance(menu, MateMenu.TreeDirectory) and self.__isVisible(menu):
                    yield menu

    def getItems(self, menu):
        for item in get_contents(menu):
            if isinstance(item, MateMenu.TreeEntry) and \
               item.get_desktop_file_id()[-19:] != '-usercustom.desktop' and \
               self.__isVisible(item):
                yield item

    def __isVisible(self, item):
        if isinstance(item, MateMenu.TreeEntry):
            return not(item.get_is_excluded() or item.get_is_nodisplay())
        if isinstance(item, MateMenu.TreeDirectory) and len(get_contents(item)):
            return True

class SuggestionButton(Gtk.Button):

    def __init__(self, iconName, iconSize, label):
        Gtk.Button.__init__(self)
        self.set_relief(Gtk.ReliefStyle.NONE)
        self.set_size_request(-1, -1)
        Align1 = Gtk.Alignment()
        Align1.set(0, 0.5, 1.0, 0)
        HBox1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        labelBox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        if iconName.startswith("/"):
            self.image = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(iconName, iconSize, iconSize))
        else:
            self.image = Gtk.Image.new_from_icon_name(iconName, Gtk.IconSize.DIALOG)
            self.image.set_pixel_size(iconSize)
        HBox1.pack_start(self.image, False, False, 5)
        self.label = Gtk.Label()
        self.label.set_markup(label)
        self.label.set_ellipsize(3)
        self.label.set_alignment(0.0, 1.0)
        labelBox.pack_start(self.label, True, True, 2)
        HBox1.pack_start(labelBox, True, True, 2)
        Align1.add(HBox1)
        self.add(Align1)
        self.show_all()

    def set_image(self, path):
        self.image.set_from_file(path)

    def set_text(self, text):
        self.label.set_markup(text)

    def set_icon_size (self, size):
        self.image.set_pixel_size(size)

class pluginclass(object):
    TARGET_TYPE_TEXT = 80
    toButton = (Gtk.TargetEntry.new("text/uri-list", 0, TARGET_TYPE_TEXT),
                Gtk.TargetEntry.new("text/uri-list", 0, TARGET_TYPE_TEXT))
    TARGET_TYPE_FAV = 81
    toFav = (Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 81),
             Gtk.TargetEntry.new("text/plain", 0, 100),
             Gtk.TargetEntry.new("text/uri-list", 0, 101))
    fromFav = (Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 81),
               Gtk.TargetEntry.new("text/plain", Gtk.TargetFlags.SAME_APP, 81))

    #@print_timing
    def __init__(self, mintMenuWin, toggleButton, de):
        self.mintMenuWin = mintMenuWin
        RecentHelper.mintMenuWin = mintMenuWin
        self.mainMenus = []
        self.toggleButton = toggleButton
        self.menuFiles = []
        self.de = de

        self.canOffload = False

        try:
            helper = XApp.GpuOffloadHelper.get_sync()
            self.canOffload = helper.is_offload_supported()
        except AttributeError:
            try:
                self.canOffload = XApp.util_gpu_offload_supported()
            except AttributeError:
                print("Could not check for gpu offload support - maybe xapps isn't up to date.");

        # Detect the locale (this is used for the Wikipedia search)
        self.lang = "en"
        lang = os.getenv('LANG')
        if lang is not None and lang != "":
            self.lang = lang.split("_")[0]

        self.builder = Gtk.Builder()
        self.builder.set_translation_domain("mintmenu")
        self.builder.add_from_file("/usr/share/linuxmint/mintmenu/applications.ui")

        # Read GLADE file
        self.main_box = self.builder.get_object("main_box")
        self.notebook = self.builder.get_object("notebook2")
        self.search_bar = self.builder.get_object("search_bar")
        self.searchEntry = self.builder.get_object("searchEntry")
        self.searchButton = self.builder.get_object("searchButton")
        self.showAllAppsButton = self.builder.get_object("showAllAppsButton")
        self.showFavoritesButton = self.builder.get_object("showFavoritesButton")
        self.applicationsBox = self.builder.get_object("applicationsBox")
        self.categoriesBox = self.builder.get_object("categoriesBox")
        self.favoritesBox = self.builder.get_object("favoritesBox")
        self.applicationsScrolledWindow = self.builder.get_object("applicationsScrolledWindow")


        self.numApps = 0
        # These properties are NECESSARY to maintain consistency

        # Set 'window' property for the plugin (Must be the root widget)
        self.window = self.builder.get_object("mainWindow")

        # Set 'heading' property for plugin
        self.heading = ""#_("Applications")

        # This should be the first item added to the window in glade
        self.content_holder = self.builder.get_object("Applications")

        # Unset all timers
        self.filterTimer = None
        self.menuChangedTimer = None
        # Hookup for text input
        self.keyPress_handler = self.mintMenuWin.window.connect("key-press-event", self.keyPress)

        self.favoritesBox.connect("drag-data-received", self.ReceiveCallback)
        self.favoritesBox.drag_dest_set(Gtk.DestDefaults.MOTION |
                                        Gtk.DestDefaults.HIGHLIGHT |
                                        Gtk.DestDefaults.DROP,
                                        self.toButton, Gdk.DragAction.COPY)
        self.showFavoritesButton.connect("drag-data-received", self.ReceiveCallback)
        self.showFavoritesButton.drag_dest_set(Gtk.DestDefaults.MOTION |
                                               Gtk.DestDefaults.HIGHLIGHT |
                                               Gtk.DestDefaults.DROP,
                                               self.toButton, Gdk.DragAction.COPY)

        # self.searchButton.connect("button_release_event", self.SearchWithButton)
        try:
            # GSettings stuff
            self.settings = Gio.Settings("com.linuxmint.mintmenu.plugins.applications")

            self.migrate_favorites()

            self.GetGSettingsEntries()
            self.settings.connect("changed::icon-size", self.changeIconSize)
            self.settings.connect("changed::favicon-size", self.changeFavIconSize)
            self.settings.connect("changed::height", self.changePluginSize)
            self.settings.connect("changed::width", self.changePluginSize)
            self.settings.connect("changed::categories-mouse-over", self.changeCategoriesMouseOver)
            self.settings.connect("changed::swap-generic-name", self.changeSwapGenericName)
            self.settings.connect("changed::show-category-icons", self.changeShowCategoryIcons)
            self.settings.connect("changed::show-application-comments", self.changeShowApplicationComments)
            self.settings.connect("changed::search-on-top", self.positionSearchBar)
            self.settings.connect("changed::use-apt", self.switchAPTUsage)
            self.settings.connect("changed::fav-cols", self.changeFavCols)
            self.settings.connect("changed::remember-filter", self.changeRememberFilter)
            self.settings.connect("changed::enable-internet-search", self.changeEnableInternetSearch)
            self.settings.connect("changed::category-hover-delay", self.GetGSettingsEntries)
            self.settings.connect("changed::do-not-filter", self.GetGSettingsEntries)
            self.settings.connect("changed::enable-internet-search", self.GetGSettingsEntries)
            self.settings.connect("changed::search-command", self.GetGSettingsEntries)
            self.settings.connect("changed::default-tab", self.GetGSettingsEntries)
            self.settings.connect("changed::favorite-apps-list", self.favoriteAppsChanged)
        except Exception as e:
            print(e)

        self.positionSearchBar()

        self.currentFavCol = 0
        self.favorites = []

        self.content_holder.set_size_request(self.width, self.height)
        # Calculate applicationsBox width based on categoryBox width, but since
        # we won't have that until the menu has been shown go with an estimate
        self.applicationsBox.set_size_request(self.width - 155, -1)
        # Add margin for scrollbars to categoriesBox
        categoriesScrolledWindow = self.builder.get_object("categoriesScrolledWindow")
        scrollbar_width = categoriesScrolledWindow.get_vscrollbar().get_preferred_width()
        self.categoriesBox.set_margin_right(scrollbar_width.natural_width + 2)

        self.buildingButtonList = False
        self.stopBuildingButtonList = False

        self.categoryList = []
        self.applicationList = []

        #dirty ugly hack, to get favorites drag origin position
        self.drag_origin = None

        self.rebuildLock = False
        self.activeFilter = (1, "", self.searchEntry)

        self.adminMenu = None

        for mainitems in ["mate-applications.menu", "mate-settings.menu"]:
            mymenu = Menu(mainitems)
            mymenu.tree.connect("changed", self.menuChanged, None)
            self.menuFiles.append(mymenu)

        self.refresh_apt_cache()
        self.suggestions = []
        self.current_suggestion = None
        self.panel = "top"
        self.panel_position = -1

        self.builder.get_object("searchButton").connect("button-press-event", self.searchPopup)

        # self.icon_theme = Gtk.IconTheme.get_default()
        # self.icon_theme.connect("changed", self.on_icon_theme_changed)

    def refresh_apt_cache(self):
        if self.useAPT:
            path = "%s/.linuxmint/mintMenu" % home
            if not os.path.exists(path):
                os.makedirs(path)
            subprocess.Popen(["/usr/lib/linuxmint/mintMenu/plugins/get_apt_cache.py", "%s/apt.cache" % path])

    def get_panel(self):
        panelsettings = Gio.Settings.new("org.mate.panel")
        applet_list = panelsettings.get_strv("object-id-list")
        for applet in applet_list:
            object_schema = Gio.Settings.new_with_path("org.mate.panel.object", "/org/mate/panel/objects/%s/" % applet)
            keys = object_schema.list_keys()
            if "applet-iid" in keys:
                iid = object_schema.get_string("applet-iid")
                if iid is not None and iid.find("MintMenu") != -1:
                    self.panel = object_schema.get_string("toplevel-id")
                    self.panel_position = object_schema.get_int("position") + 1

    def url_install(self, widget, pkg_name):
        subprocess.Popen(["xdg-open", "apt://%s" % pkg_name])
        self.mintMenuWin.hide()

    @staticmethod
    def wake():
        return

    def destroy(self):
        self.content_holder.destroy()
        self.searchEntry.destroy()
        self.searchButton.destroy()
        self.showAllAppsButton.destroy()
        self.showFavoritesButton.destroy()
        self.applicationsBox.destroy()
        self.categoriesBox.destroy()
        self.favoritesBox.destroy()

        self.mintMenuWin.window.disconnect(self.keyPress_handler)

    def changePluginSize(self, settings, key):
        if key == "width":
            self.width = settings.get_int(key)
            self.applicationsBox.set_size_request(self.width - self.categoriesBox.get_preferred_width().natural_width, -1)

        elif key == "height":
            self.heigth = settings.get_int(key)
        self.content_holder.set_size_request(self.width, self.height)

    def changeSwapGenericName(self, settings, key):
        self.swapgeneric = settings.get_boolean(key)

        for child in self.favoritesBox:
            if isinstance(child, FavApplicationLauncher):
                child.setSwapGeneric(self.swapgeneric)

    def changeShowCategoryIcons(self, settings, key):
        self.showcategoryicons = settings.get_boolean(key)

        if self.showcategoryicons:
            categoryIconSize = self.iconSize
        else:
            categoryIconSize = 0

        for child in self.categoriesBox:
            child.setIconSize(categoryIconSize)

    def changeIconSize(self, settings, key):
        self.iconSize = settings.get_int(key)

        if self.showcategoryicons:
            categoryIconSize = self.iconSize
        else:
            categoryIconSize = 0

        for child in self.categoriesBox:
            child.setIconSize(categoryIconSize)

        for child in self.applicationsBox:
            try:
                child.setIconSize(self.iconSize)
            except:
                pass

    def changeFavIconSize(self, settings, key):
        self.faviconsize = settings.get_int(key)

        for child in self.favoritesBox:
            if isinstance(child, FavApplicationLauncher):
                child.setIconSize(self.faviconsize)

    def positionSearchBar(self, settings=None, key=None):
        self.main_box.remove(self.notebook)
        self.main_box.remove(self.search_bar)
        if self.settings.get_boolean("search-on-top"):
            self.main_box.pack_start(self.search_bar, False, False, 0)
            self.main_box.pack_start(self.notebook, True, True, 0)
        else:
            self.main_box.pack_start(self.notebook, True, True, 0)
            self.main_box.pack_start(self.search_bar, False, False, 0)

    def switchAPTUsage(self, settings, key):
        self.useAPT = settings.get_boolean(key)
        self.refresh_apt_cache()

    def changeRememberFilter(self, settings, key):
        self.rememberFilter = settings.get_boolean(key)

    def changeEnableInternetSearch(self, settings, key):
        self.enableInternetSearch = settings.get_boolean(key)

    def changeShowApplicationComments(self, settings, key):
        self.showapplicationcomments = settings.get_boolean(key)
        for child in self.applicationsBox:
            child.setShowComment(self.showapplicationcomments)

    def changeCategoriesMouseOver(self, settings, key):
        self.categories_mouse_over = settings.get_boolean(key)
        for child in self.categoriesBox:
            if self.categories_mouse_over and not child.mouseOverHandlerIds:
                startId = child.connect("enter", self.StartFilter, child.filter)
                stopId = child.connect("leave", self.StopFilter)
                child.mouseOverHandlerIds = (startId, stopId)
            elif not self.categories_mouse_over and child.mouseOverHandlerIds:
                child.disconnect(child.mouseOverHandlerIds[0])
                child.disconnect(child.mouseOverHandlerIds[1])
                child.mouseOverHandlerIds = None

    def changeFavCols(self, settings, key):
        self.favCols = settings.get_int(key)
        for fav in self.favorites:
            self.favoritesBox.remove(fav)
            self.favoritesPositionOnGrid(fav)

    def RegenPlugin(self, *args, **kargs):
        self.refresh_apt_cache()

        # save old config - this is necessary because the app will notified
        # when it sets the default values and you don't want the to reload
        # itself several times
        oldcategories_mouse_over = self.categories_mouse_over
        oldiconsize = self.iconSize
        oldfaviconsize = self.faviconsize
        oldswapgeneric = self.swapgeneric
        oldshowcategoryicons = self.showcategoryicons
        oldcategoryhoverdelay = self.categoryhoverdelay
        oldicon = self.icon
        oldhideseparator = self.hideseparator
        oldshowapplicationcomments = self.showapplicationcomments

        self.GetGSettingsEntries()

        # if the config hasn't changed return
        if (oldcategories_mouse_over == self.categories_mouse_over and
            oldiconsize == self.iconSize and
            oldfaviconsize == self.faviconsize and
            oldswapgeneric == self.swapgeneric and
            oldshowcategoryicons == self.showcategoryicons and
            oldcategoryhoverdelay == self.categoryhoverdelay and
            oldicon == self.icon and
            oldhideseparator == self.hideseparator and
            oldshowapplicationcomments == self.showapplicationcomments
            ):
            return

        self.Todos()
        self.buildFavorites()
        RecentHelper.buildRecentApps()
        self.RebuildPlugin()

    def GetGSettingsEntries(self, settings=None, key=None):

        self.categories_mouse_over = self.settings.get_boolean("categories-mouse-over")
        self.width = self.settings.get_int("width")
        self.height = self.settings.get_int("height")
        self.donotfilterapps = self.settings.get_boolean("do-not-filter")
        self.iconSize = self.settings.get_int("icon-size")
        self.faviconsize = self.settings.get_int("favicon-size")
        self.favCols = self.settings.get_int("fav-cols")
        self.swapgeneric = self.settings.get_boolean("swap-generic-name")
        self.showcategoryicons = self.settings.get_boolean("show-category-icons")
        self.categoryhoverdelay = self.settings.get_int("category-hover-delay")
        self.showapplicationcomments = self.settings.get_boolean("show-application-comments")
        self.useAPT = self.settings.get_boolean("use-apt")
        self.rememberFilter = self.settings.get_boolean("remember-filter")
        self.enableInternetSearch = self.settings.get_boolean("enable-internet-search")

        self.lastActiveTab =  self.settings.get_int("last-active-tab")
        self.defaultTab = self.settings.get_int("default-tab")

        # Search tool
        self.searchtool = self.settings.get_string("search-command")
        if self.searchtool == "beagle-search SEARCH_STRING":
            self.searchtool = "mate-search-tool --named \"%s\" --start"
            self.settings.set_string("search-command", "mate-search-tool --named \"%s\" --start")

        # Plugin icon
        self.icon = self.settings.get_string("icon")

        # Hide vertical dotted separator
        self.hideseparator = self.settings.get_boolean("hide-separator")

    def RebuildPlugin(self):
        self.content_holder.set_size_request(self.width, self.height)

    def onShowMenu(self):
        if self.favorites:
            if self.defaultTab == -1:
                self.changeTab(self.lastActiveTab)
            else:
                self.changeTab((self.defaultTab - 1) * -1)
        else:
            self.changeTab(1)

        if self.rememberFilter and self.searchEntry.get_text().strip() != "":
            self.Filter(self.activeFilter[2], self.activeFilter[1])

    def onHideMenu(self):
        self.settings.set_int("last-active-tab", self.lastActiveTab)

    def changeTab(self, tabNum, clear = True):
        notebook = self.builder.get_object("notebook2")
        if tabNum == 0:
            notebook.set_current_page(0)
        elif tabNum == 1:
            notebook.set_current_page(1)

        self.focusSearchEntry(clear)
        self.lastActiveTab = tabNum

    def Todos(self):
        self.searchEntry.connect("popup-menu", self.blockOnPopup)
        self.searchEntry.connect("button-press-event", self.blockOnRightPress)
        self.searchEntry.connect("changed", self.Filter)
        self.searchEntry.connect("activate", self.Search)
        self.showAllAppsButton.connect("clicked", lambda widget: self.changeTab(1))
        self.showFavoritesButton.connect("clicked", lambda widget: self.changeTab(0))
        self.buildButtonList()

    def blockOnPopup(self, *args):
        self.mintMenuWin.stopHiding()
        return False

    def blockOnRightPress(self, widget, event):
        if event.button == 3:
            self.mintMenuWin.stopHiding()
        return False

    def focusSearchEntry(self, clear = True):
        # grab_focus() does select all text,
        # restoring the original selection is somehow broken, so just select the end
        # of the existing text, that's the most likely candidate anyhow
        self.searchEntry.grab_focus()
        if self.rememberFilter or not clear:
            self.searchEntry.select_region(0, -1)
        else:
            self.searchEntry.set_text("")

    def buildButtonList(self):
        if self.buildingButtonList:
            self.stopBuildingButtonList = True
            GLib.timeout_add(100, self.buildButtonList)
            return
        self.stopBuildingButtonList = False
        self.updateBoxes(False)

    def categoryBtnFocus(self, widget, event, category):
        self.scrollItemIntoView(widget)
        self.StartFilter(widget, category)

    def StartFilter(self, widget, category):
        # if there is a timer for a different category running stop it
        if self.filterTimer:
            GLib.source_remove(self.filterTimer)
        self.filterTimer = GLib.timeout_add(self.categoryhoverdelay, self.Filter, widget, category)

    def StopFilter(self, widget):
        if self.filterTimer:
            GLib.source_remove(self.filterTimer)
            self.filterTimer = None

    def add_suggestion(self, icon=None, label=None, tooltip=None, callback=None, *args):
        if icon:
            item = SuggestionButton(icon, self.iconSize, label)
            item.connect("clicked", callback, *args)
            if tooltip:
                item.set_tooltip_text(tooltip)
        else:
            item = Gtk.SeparatorMenuItem()
            item.show_all()
        self.applicationsBox.add(item)
        self.suggestions.append(item)

    def add_search_suggestions(self, text):
        text = "<b>%s</b>" % html.escape(text)
        if self.enableInternetSearch:
            self.add_suggestion("/usr/lib/linuxmint/mintMenu/search_engines/ddg.svg",
                                _("Search DuckDuckGo for %s") % text, None, self.search_ddg)
            self.add_suggestion("/usr/lib/linuxmint/mintMenu/search_engines/wikipedia.svg",
                                _("Search Wikipedia for %s") % text, None, self.search_wikipedia)
            self.add_suggestion()

        self.add_suggestion("accessories-dictionary", _("Lookup %s in Dictionary") % text, None,
                            self.search_dictionary)
        self.add_suggestion("xapp-edit-find-symbolic", _("Search Computer for %s") % text, None, self.Search)

        self.applicationsBox.get_children()[-1].grab_focus()

    def add_apt_filter_results(self, keyword):
        try:
            # Wait to see if the keyword has changed.. before doing anything
            current_keyword = self.searchEntry.get_text()
            if keyword != current_keyword:
                return
            found_packages = []
            found_in_name = []
            found_elsewhere = []
            keywords = keyword.split(" ")
            path = os.path.join(home, ".linuxmint/mintMenu/apt.cache")
            if not os.path.isfile(path):
                return
            with open(path) as aptcache:
                pkgs = [line for line in aptcache.readlines() if all(keyword in line for keyword in keywords)]
            for pkg in pkgs:
                values = pkg.split("###")
                if len(values) == 4:
                    status = values[0]
                    if status == "ERROR":
                        print("Could not refresh APT cache")
                    elif status == "CACHE":
                        name = values[1]
                        summary = values[2]
                        description = values[3].replace("~~~", "\n")
                        package = PackageDescriptor(name, summary, description)
                        # See if all keywords are in the name (so we put these results at the top of the list)
                        some_found = False
                        some_not_found = False
                        for word in keywords:
                            if word in package.name:
                                some_found = True
                            else:
                                some_not_found = True
                        if some_found and not some_not_found:
                            found_in_name.append(package)
                        else:
                            found_elsewhere.append(package)
                    else:
                        print("Invalid status code:",status)
            found_packages.extend(found_in_name)
            found_packages.extend(found_elsewhere)
            if keyword == self.searchEntry.get_text() and len(found_packages) > 0:
                self.add_suggestion()
                # Reduce the number of results to 10 max...
                # it takes a HUGE amount of time to add the GTK box in the menu otherwise..
                if len(found_packages) > 10:
                    found_packages = found_packages[:10]
                for pkg in found_packages:
                    name = pkg.name
                    for word in keywords:
                        if word != "":
                            name = name.replace(word, "<b>%s</b>" % word)
                    self.add_suggestion("package-x-generic",
                        _("Install package '%s'") % name,
                        "%s\n\n%s\n\n%s" % (pkg.name, pkg.summary, pkg.description),
                        self.url_install, pkg.name)
                    #if cache != self.current_results:
                    #    self.current_results.append(pkg)

            #if len(found_packages) == 0:
            #    gtk.gdk.threads_enter()
            #    try:
            #        self.applicationsBox.remove(self.last_separator)
            #        self.suggestions.remove(self.last_separator)
            #    finally:
            #        gtk.gdk.threads_leave()

        except Exception as e:
            print(e)

    def add_apt_filter_results_sync(self, cache, keyword):
        try:
            found_packages = []
            keywords = keyword.split(" ")
            if cache is not None:
                for pkg in cache:
                    some_found = False
                    some_not_found = False
                    for word in keywords:
                        if word in pkg.name:
                            some_found = True
                        else:
                            some_not_found = True
                    if some_found and not some_not_found:
                        found_packages.append(pkg)

            if len(found_packages) > 0:
                self.add_suggestion()

            for pkg in found_packages:
                name = pkg.name
                for word in keywords:
                    if word != "":
                        name = name.replace(word, "<b>%s</b>" % word)
                self.add_suggestion(Gtk.STOCK_ADD,
                    _("Install package '%s'") % name,
                    "%s\n\n%s\n\n%s" % (pkg.name, pkg.summary, pkg.description),
                    self.url_install, pkg.name)

            #if len(found_packages) == 0:
            #    self.applicationsBox.remove(self.last_separator)
            #    self.suggestions.remove(self.last_separator)

        except Exception as e:
            print(e)

    def Filter(self, widget, category = None):
        self.filterTimer = None

        for suggestion in self.suggestions:
            self.applicationsBox.remove(suggestion)
        self.suggestions = []

        if widget == self.searchEntry:
            if self.donotfilterapps:
                widget.set_text("")
            else:
                text = widget.get_text()
                if self.lastActiveTab != 1:
                    self.changeTab(1, clear = False)
                text = widget.get_text()
                showns = False # Are any app shown?
                shownList = []
                for i in self.applicationsBox.get_children():
                    shown = i.filterText(text)
                    if shown:
                        dupe = False
                        for item in shownList:
                            if i.desktopFile == item.desktopFile:
                                dupe = True
                        if dupe:
                            i.hide()
                        else:
                            shownList.append(i)
                            self.applicationsBox.remove(i)
                            showns = True
                if not showns:
                    if len(text) >= 3:
                        self.add_search_suggestions(text)
                        if self.useAPT:
                            GLib.timeout_add(300, self.add_apt_filter_results, text)
                else:
                    # Sort applications by relevance, and alphabetical within that
                    shownList = sorted(shownList, key=lambda app: app.appName)
                    shownList = sorted(shownList, key=lambda app: app.relevance, reverse=True)
                    focused = False
                    for i in shownList:
                        self.applicationsBox.add(i)
                        if not focused:
                            # Grab focus of the first app shown
                            i.grab_focus()
                            focused = True
                for i in self.categoriesBox.get_children():
                    i.released()
                    i.set_relief(Gtk.ReliefStyle.NONE)

                allButton = self.categoriesBox.get_children()[0]
                allButton.set_relief(Gtk.ReliefStyle.HALF)
                self.activeFilter = (0, text, widget)
        else:
            apps = self.applicationsBox.get_children()

            if self.activeFilter[0] == 0: # Previous view was a search, reset our list order.
                apps = sorted(apps, key=lambda app: app.appName)
                for i in apps:
                    self.applicationsBox.remove(i)
                    self.applicationsBox.add(i)

            self.activeFilter = (1, category, widget)

            listedDesktopFiles = []
            for i in apps:
                if category == "":
                    if not i.desktop_file_path in listedDesktopFiles:
                        listedDesktopFiles.append(i.desktop_file_path)
                        i.show_all()
                    else:
                        i.hide()
                else:
                    i.filterCategory(category)

            for i in self.categoriesBox.get_children():
                i.released()
                i.set_relief(Gtk.ReliefStyle.NONE)
            widget.set_relief(Gtk.ReliefStyle.HALF)

        self.applicationsScrolledWindow.get_vadjustment().set_value(0)

    def FilterAndClear(self, widget, category = None):
        self.searchEntry.set_text("")
        self.Filter(widget, category)

    def keyPress(self, widget, event):
        """ Forward all text to the search box """
        if event.string.strip() or event.keyval == Gdk.KEY_space:
            self.searchEntry.event(event)
            return True
        return False

    def favPopup(self, widget, event):
        if not event.button == 3:
            return
        if event.y > widget.get_allocation().height / 2:
            insertBefore = False
        else:
            insertBefore = True

        if widget.type == "location":
            mTree = Gtk.Menu()
            mTree.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
                             Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                             Gdk.EventMask.BUTTON_PRESS_MASK |
                             Gdk.EventMask.BUTTON_RELEASE_MASK)
            #i18n
            desktopMenuItem = Gtk.MenuItem(_("Add to desktop"))
            panelMenuItem = Gtk.MenuItem(_("Add to panel"))
            separator1 = Gtk.SeparatorMenuItem()
            insertSpaceMenuItem = Gtk.MenuItem(_("Insert space"))
            insertSeparatorMenuItem = Gtk.MenuItem(_("Insert separator"))
            separator2 = Gtk.SeparatorMenuItem()
            startupMenuItem = Gtk.CheckMenuItem(_("Launch when I log in"))
            separator3 = Gtk.SeparatorMenuItem()
            launchMenuItem = Gtk.MenuItem(_("Launch"))
            launchOffloadedMenuItem = Gtk.MenuItem(_("Run with NVIDIA GPU"))
            removeFromFavMenuItem = Gtk.MenuItem(_("Remove from favorites"))
            separator4 = Gtk.SeparatorMenuItem()
            propsMenuItem = Gtk.MenuItem(_("Edit properties"))

            desktopMenuItem.connect("activate", self.add_to_desktop, widget)
            panelMenuItem.connect("activate", self.add_to_panel, widget)
            insertSpaceMenuItem.connect("activate", self.onFavoritesInsertSpace, widget, insertBefore)
            insertSeparatorMenuItem.connect("activate", self.onFavoritesInsertSeparator, widget, insertBefore)
            if widget.isInStartup():
                startupMenuItem.set_active(True)
                startupMenuItem.connect("toggled", self.onRemoveFromStartup, widget)
            else:
                startupMenuItem.set_active(False)
                startupMenuItem.connect("toggled", self.onAddToStartup, widget)
            launchMenuItem.connect("activate", self.onLaunchApp, widget)
            launchOffloadedMenuItem.connect("activate", self.onLaunchOffloadedApp, widget)
            removeFromFavMenuItem.connect("activate", self.onFavoritesRemove, widget)
            propsMenuItem.connect("activate", self.onPropsApp, widget)

            if self.de == "mate":
                mTree.append(desktopMenuItem)
                mTree.append(panelMenuItem)
                mTree.append(separator1)
            mTree.append(insertSpaceMenuItem)
            mTree.append(insertSeparatorMenuItem)
            mTree.append(separator2)
            mTree.append(startupMenuItem)
            mTree.append(separator3)
            mTree.append(launchMenuItem)
            if self.canOffload:
                mTree.append(launchOffloadedMenuItem)
            mTree.append(removeFromFavMenuItem)
            mTree.append(separator4)
            mTree.append(propsMenuItem)
        else:
            mTree = Gtk.Menu()
            mTree.set_events(Gdk.EventMask.POINTER_MOTION_MASK |
                             Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                             Gdk.EventMask.BUTTON_PRESS_MASK |
                             Gdk.EventMask.BUTTON_RELEASE_MASK)

            #i18n
            removeMenuItem = Gtk.MenuItem(_("Remove"))
            insertSpaceMenuItem = Gtk.MenuItem(_("Insert space"))
            insertSeparatorMenuItem = Gtk.MenuItem(_("Insert separator"))
            mTree.append(removeMenuItem)
            mTree.append(insertSpaceMenuItem)
            mTree.append(insertSeparatorMenuItem)

            removeMenuItem.connect("activate", self.onFavoritesRemove, widget)
            insertSpaceMenuItem.connect("activate", self.onFavoritesInsertSpace, widget, insertBefore)
            insertSeparatorMenuItem.connect("activate", self.onFavoritesInsertSeparator, widget, insertBefore)
        mTree.show_all()
        self.mintMenuWin.stopHiding()
        mTree.attach_to_widget(widget, None)
        if (Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION) >= (3, 22):
            mTree.popup_at_pointer(event)
        else:
            mTree.popup(None, None, None, None, event.button, event.time)

    def menuPopup(self, widget, event):
        if not event.button == 3:
            return
        mTree = Gtk.Menu()
        #i18n
        desktopMenuItem = Gtk.MenuItem(_("Add to desktop"))
        panelMenuItem = Gtk.MenuItem(_("Add to panel"))
        separator1 = Gtk.SeparatorMenuItem()
        favoriteMenuItem = Gtk.CheckMenuItem(_("Show in my favorites"))
        startupMenuItem = Gtk.CheckMenuItem(_("Launch when I log in"))
        separator2 = Gtk.SeparatorMenuItem()
        launchMenuItem = Gtk.MenuItem(_("Launch"))
        launchOffloadedMenuItem = Gtk.MenuItem(_("Run with NVIDIA GPU"))
        uninstallMenuItem = Gtk.MenuItem(_("Uninstall"))
        deleteMenuItem = Gtk.MenuItem(_("Delete from menu"))
        separator3 = Gtk.SeparatorMenuItem()
        propsMenuItem = Gtk.MenuItem(_("Edit properties"))

        if self.de == "mate":
            mTree.append(desktopMenuItem)
            mTree.append(panelMenuItem)
            mTree.append(separator1)

        mTree.append(favoriteMenuItem)
        mTree.append(startupMenuItem)
        mTree.append(separator2)
        mTree.append(launchMenuItem)
        if self.canOffload:
            mTree.append(launchOffloadedMenuItem)
        mTree.append(uninstallMenuItem)
        if home in widget.desktopFile:
            mTree.append(deleteMenuItem)
            deleteMenuItem.connect("activate", self.delete_from_menu, widget)
        mTree.append(separator3)
        mTree.append(propsMenuItem)
        mTree.show_all()

        desktopMenuItem.connect("activate", self.add_to_desktop, widget)
        panelMenuItem.connect("activate", self.add_to_panel, widget)
        launchMenuItem.connect("activate", self.onLaunchApp, widget)
        launchOffloadedMenuItem.connect("activate", self.onLaunchOffloadedApp, widget)
        propsMenuItem.connect("activate", self.onPropsApp, widget)
        uninstallMenuItem.connect("activate", self.onUninstallApp, widget)

        if self.isLocationInFavorites(widget.desktopFile):
            favoriteMenuItem.set_active(True)
            favoriteMenuItem.connect("toggled", self.onRemoveFromFavorites, widget)
        else:
            favoriteMenuItem.set_active(False)
            favoriteMenuItem.connect("toggled", self.onAddToFavorites, widget)

        if widget.isInStartup():
            startupMenuItem.set_active(True)
            startupMenuItem.connect("toggled", self.onRemoveFromStartup, widget)
        else:
            startupMenuItem.set_active(False)
            startupMenuItem.connect("toggled", self.onAddToStartup, widget)

        self.mintMenuWin.stopHiding()
        mTree.attach_to_widget(widget, None)
        mTree.popup(None, None, None, None, event.button, event.time)

    def searchPopup(self, widget, event):
        def add_menu_item(icon=None, text=None, callback=None):
            box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            if icon == None:
                menuItem = Gtk.SeparatorMenuItem()
            else:
                if icon.startswith("/"):
                    icon = Gtk.Image.new_from_pixbuf(GdkPixbuf.Pixbuf.new_from_file_at_size(icon, 16, 16))
                else:
                    icon = Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.SMALL_TOOLBAR)
                box.add(icon)
                box.pack_start(Gtk.Label.new(text), False, False, 5)
                menuItem = Gtk.MenuItem()
                menuItem.connect("activate", callback)
            menuItem.add(box)
            menu.append(menuItem)

        menu = Gtk.Menu()

        if self.enableInternetSearch:
            add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/ddg.svg', _("Search DuckDuckGo"), self.search_ddg)
            add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/wikipedia.svg', _("Search Wikipedia"), self.search_wikipedia)

        add_menu_item('accessories-dictionary', _("Search Dictionary"), self.search_dictionary)
        add_menu_item("xapp-edit-find-symbolic", _("Search Computer"), self.Search)
        add_menu_item()
        add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/software.png', _("Find Software"), self.search_mint_software)
        add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/tutorials.png', _("Find Tutorials"), self.search_mint_tutorials)
        add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/hardware.png', _("Find Hardware"), self.search_mint_hardware)
        add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/ideas.png', _("Find Ideas"), self.search_mint_ideas)
        add_menu_item('/usr/lib/linuxmint/mintMenu/search_engines/users.png', _("Find Users"), self.search_mint_users)

        menu.show_all()

        self.mintMenuWin.stopHiding()
        menu.attach_to_widget(self.searchButton, None)
        menu.popup(None, None, None, None, event.button, event.time)

        self.focusSearchEntry(clear = False)

    def search_ddg(self, widget):
        text = urllib.parse.quote_plus(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://duckduckgo.com/?q=%s" % text])
        self.mintMenuWin.hide()

    def search_google(self, widget):
        text = urllib.parse.quote_plus(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://www.google.com/search?q=%s" % text])
        self.mintMenuWin.hide()

    def search_wikipedia(self, widget):
        text = urllib.parse.quote_plus(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://en.wikipedia.org/wiki/Special:Search?search=%s" % text])
        self.mintMenuWin.hide()

    def search_dictionary(self, widget):
        text = self.searchEntry.get_text().strip()
        subprocess.Popen(["mate-dictionary", "%s" % text])
        self.mintMenuWin.hide()

    def search_mint_tutorials(self, widget):
        text = urllib.parse.quote(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://community.linuxmint.com/index.php/tutorial/search/0/%s" % text])
        self.mintMenuWin.hide()

    def search_mint_ideas(self, widget):
        text = urllib.parse.quote(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://community.linuxmint.com/index.php/idea/search/0/%s" % text])
        self.mintMenuWin.hide()

    def search_mint_users(self, widget):
        text = urllib.parse.quote(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://community.linuxmint.com/index.php/user/search/0/%s" % text])
        self.mintMenuWin.hide()

    def search_mint_hardware(self, widget):
        text = urllib.parse.quote(self.searchEntry.get_text().strip())
        subprocess.Popen(["xdg-open", "https://community.linuxmint.com/index.php/hardware/search/0/%s" % text])
        self.mintMenuWin.hide()

    def search_mint_software(self, widget):
        text = urllib.parse.quote(self.searchEntry.get_text())
        subprocess.Popen(["xdg-open", "https://community.linuxmint.com/index.php/software/search/0/%s" % text])
        self.mintMenuWin.hide()

    def add_to_desktop(self, widget, desktopEntry):
        subprocess.Popen(["xdg-desktop-icon", "install", "--novendor", desktopEntry.desktopFile])

    def add_to_panel(self, widget, desktopEntry):
        self.get_panel()
        i = 0
        panel_schema = Gio.Settings.new("org.mate.panel")
        applet_list = panel_schema.get_strv("object-id-list")

        while True:
            test_obj = "object_%d" % i
            if test_obj in applet_list:
                i += 1
            else:
                break

        path = "/org/mate/panel/objects/%s/" % test_obj
        new_schema = Gio.Settings.new_with_path("org.mate.panel.object", path)
        new_schema.set_string("launcher-location", desktopEntry.desktopFile)
        new_schema.set_string("object-type", "launcher")
        new_schema.set_string("toplevel-id", self.panel)
        new_schema.set_int("position", self.panel_position)
        applet_list.append(test_obj)
        panel_schema.set_strv("object-id-list", applet_list)

    def delete_from_menu(self, widget, desktopEntry):
        try:
            os.unlink(desktopEntry.desktopFile)
        except Exception as e:
            print(e)

    def onLaunchApp(self, menu, widget):
        widget.execute()
        self.mintMenuWin.hide()

    def onLaunchOffloadedApp(self, menu, widget):
        widget.execute(offload=True)
        self.mintMenuWin.hide()

    def onPropsApp(self, menu, widget):
        newFileFlag = False
        sysPaths = get_system_item_paths()

        for path in sysPaths:
            path = os.path.join(path, "applications")
            relPath = os.path.relpath(widget.desktopFile, path)

            if widget.desktopFile == os.path.join(path, relPath):
                filePath = os.path.join(get_user_item_path(), relPath)
                (head,tail) = os.path.split(filePath)

                if not os.path.isdir(head):
                    os.makedirs(head)

                if not os.path.isfile(filePath):
                    data = open(widget.desktopFile).read()
                    open(filePath, 'w').write(data)
                    newFileFlag = True
                break

            else:
                filePath = widget.desktopFile

        self.mintMenuWin.hide()
        Gdk.flush()

        editProcess = subprocess.Popen(["/usr/bin/mate-desktop-item-edit", filePath])
        subprocess.Popen.communicate(editProcess)

        if newFileFlag:
            if filecmp.cmp(widget.desktopFile, filePath):
                os.remove(filePath)
            else:
                favoriteChange = 0
                for favorite in self.favorites:
                    if favorite.type == "location":
                        if favorite.desktopFile == widget.desktopFile:
                            favorite.desktopFile = filePath
                            favoriteChange = 1
                if favoriteChange == 1:
                    self.favoritesSave()
                    self.buildFavorites()
        else:
            self.buildFavorites()

    def onUninstallApp(self, menu, widget):
        widget.uninstall()
        self.mintMenuWin.hide()

    def onFavoritesInsertSpace(self, menu, widget, insertBefore):
        if insertBefore:
            self.favoritesAdd(self.favoritesBuildSpace(), widget.position)
        else:
            self.favoritesAdd(self.favoritesBuildSpace(), widget.position + 1)

    def onFavoritesInsertSeparator(self, menu, widget, insertBefore):
        if insertBefore:
            self.favoritesAdd(self.favoritesBuildSeparator(), widget.position)
        else:
            self.favoritesAdd(self.favoritesBuildSeparator(), widget.position + 1)

    def onFavoritesRemove(self, menu, widget):
        self.favoritesRemove(widget.position)

    def onAddToStartup(self, menu, widget):
        widget.addToStartup()

    def onRemoveFromStartup(self, menu, widget):
        widget.removeFromStartup()

    def onAddToFavorites(self, menu, widget):
        self.favoritesAdd(self.favoritesBuildLauncher(widget.desktopFile))

    def onRemoveFromFavorites(self, menu, widget):
        self.favoritesRemoveLocation(widget.desktopFile)

    def ReceiveCallback(self, widget, context, x, y, selection, targetType, time):
        if targetType == self.TARGET_TYPE_TEXT:
            for uri in selection.get_uris():
                self.favoritesAdd(self.favoritesBuildLauncher(uri))

    def Search(self, widget):
        text = self.searchEntry.get_text().strip()
        if text != "":
            for app_button in self.applicationsBox.get_children():
                if(isinstance(app_button, ApplicationLauncher) and app_button.filterText(text)):
                    app_button.execute()
                    self.mintMenuWin.hide()
                    return

            self.mintMenuWin.hide()
            fullstring = self.searchtool.replace("%s", text)
            os.system(fullstring + " &")

    def SearchWithButton(self, widget, event):
        self.Search(widget)

    def do_plugin(self):
        self.Todos()
        self.buildFavorites()

    # Scroll button into view
    def scrollItemIntoView(self, widget, event = None):
        viewport = widget.get_parent()
        while not isinstance(viewport, Gtk.Viewport):
            if not viewport.get_parent():
                return
            viewport = viewport.get_parent()
        aloc = widget.get_allocation()
        viewport.get_vadjustment().clamp_page(aloc.y, aloc.y + aloc.height)

    def favoritesBuildSpace(self):
        space = Gtk.EventBox()
        space.set_size_request(-1, 20)
        space.set_visible_window(False)
        space.connect("button-press-event", self.favPopup)
        space.type = "space"
        space.show()
        return space

    def favoritesBuildSeparator(self):
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(5)
        separator.set_margin_bottom(5)
        separator.type = "separator"

        separator.show_all()
        box = Gtk.EventBox()
        box.type = "separator"
        box.add(separator)
        box.set_visible_window(False)
        box.connect("button-press-event", self.favPopup)
        box.show_all()
        return box

    def favoritesBuildLauncher(self, location):
        try:
            # For Folders and Network Shares
            location = "".join(location.split("%20"))

            if location.startswith("file://"):
                location = location[7:]

            if not os.path.exists(location):
                print("%s does not exist, skipping." % location)
                return None

            # Don't add a location twice
            for fav in self.favorites:
                if fav.type == "location" and fav.desktopFile == location:
                    return None

            favButton = FavApplicationLauncher(location, self.faviconsize, self.swapgeneric)
            if favButton.appExec:
                favButton.show()
                favButton.connect("popup-menu", self.favPopup)
                favButton.connect("button-press-event", self.favPopup)
                favButton.connect("focus-in-event", self.scrollItemIntoView)
                favButton.connect("clicked", RecentHelper.applicationButtonClicked)

                self.mintMenuWin.setTooltip(favButton, favButton.getTooltip())
                favButton.type = "location"
                return favButton
        except Exception as e:
            print("File in favorites not found: '%s': %s" % (location, e))

        return None

    def migrate_favorites(self):
        if self.settings.get_strv("favorite-apps-list") != []:
            return

        default_path = os.path.join("/usr/lib/linuxmint/mintMenu/applications.list")
        path = os.path.join(home, ".linuxmint/mintMenu/applications.list")

        if os.path.isdir(path):
            # dir created by a bug in mint 19.2 beta
            os.system("rm -rf %s" % path)
            return

        if not os.path.exists(path):
            path = default_path

        with open(path) as f:
            self.settings.set_strv("favorite-apps-list", f.readlines())

        try:
            os.replace(path, path + ".deprecated_uses_dconf_now")
        except:
            # This will fail if it was the default path, ignore it.
            pass

    def favoriteAppsChanged(self, setting, key):
        self.buildFavorites()

    def buildFavorites(self):
        try:
            faves = self.settings.get_strv("favorite-apps-list")

            for child in self.favoritesBox:
                child.destroy()

            position = 0
            self.favorites = []

            for app in faves:
                try:
                    app = app.strip()

                    if app[0:9] == "location:":
                        favButton = self.favoritesBuildLauncher(app[9:])
                    elif app == "space":
                        favButton = self.favoritesBuildSpace()
                    elif app == "separator":
                        favButton = self.favoritesBuildSeparator()
                    else:
                        if app.endswith(".desktop"):
                            favButton = self.favoritesBuildLauncher(app)
                        else:
                            favButton = None

                    if favButton:
                        favButton.position = position
                        self.favorites.append(favButton)
                        self.favoritesPositionOnGrid(favButton)
                        favButton.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, self.toFav, Gdk.DragAction.COPY)
                        favButton.drag_dest_set(Gtk.DestDefaults.MOTION |
                                                Gtk.DestDefaults.HIGHLIGHT |
                                                Gtk.DestDefaults.DROP,
                                                self.toFav, Gdk.DragAction.COPY)
                        favButton.connect("drag-data-get", self.on_drag_data_get)
                        favButton.connect("drag-data-received", self.on_drag_data_received)
                        position += 1
                except Exception as e:
                    print("Can't add favorite: %s" % app)
                    print (e)

        except Exception as e:
            print(e)

    def favoritesPositionOnGrid(self, favorite):
        row = 0
        col = 0
        for fav in self.favorites:
            if (fav.type == "separator" or fav.type == "space") and col != 0:
                row += 1
                col = 0
            if fav.position == favorite.position:
                break
            col += 1
            if  fav.type == "separator" or fav.type == "space":
                row += 1
                col = 0
            if col >= self.favCols:
                row += 1
                col = 0

        if favorite.type == "separator" or favorite.type == "space":
            self.favoritesBox.attach(favorite, col, row, self.favCols, 1)
        else:
            self.favoritesBox.attach(favorite, col, row, 1, 1)

    def favoritesReorder(self, oldposition, newposition):
        if oldposition == newposition:
            return
        tmp = self.favorites[oldposition]
        if newposition > oldposition:
            if (self.favorites[newposition - 1].type == "space" or
                self.favorites[newposition - 1].type == "separator") and self.favCols > 1:
                newposition = newposition - 1
            for i in range(oldposition, newposition):
                self.favorites[i] = self.favorites[i + 1]
                self.favorites[i].position = i
        elif newposition < oldposition:
            for i in range(0,  oldposition - newposition):
                self.favorites[oldposition - i] = self.favorites[oldposition - i - 1]
                self.favorites[oldposition - i] .position = oldposition - i
        self.favorites[newposition] = tmp
        self.favorites[newposition].position = newposition

        for fav in self.favorites:
            self.favoritesBox.remove(fav)
            self.favoritesPositionOnGrid(fav)

        self.favoritesSave()

    def favoritesAdd(self, favButton, position = -1):
        if favButton:
            favButton.position = len(self.favorites)
            self.favorites.append(favButton)
            self.favoritesPositionOnGrid(favButton)

            favButton.connect("drag-data-received", self.on_drag_data_received)
            favButton.drag_dest_set(Gtk.DestDefaults.MOTION |
                                    Gtk.DestDefaults.HIGHLIGHT |
                                    Gtk.DestDefaults.DROP,
                                    self.toFav, Gdk.DragAction.COPY)
            favButton.connect("drag-data-get", self.on_drag_data_get)
            favButton.drag_source_set(Gdk.ModifierType.BUTTON1_MASK, self.toFav, Gdk.DragAction.COPY)

            if position >= 0:
                self.favoritesReorder(favButton.position, position)

            self.favoritesSave()

    def favoritesRemove(self, position):
        tmp = self.favorites[position]
        self.favorites.remove(self.favorites[position])
        tmp.destroy()

        for i in range(position, len(self.favorites)):
            self.favorites[i].position = i
            self.favoritesBox.remove(self.favorites[i])
            self.favoritesPositionOnGrid(self.favorites[i])
        self.favoritesSave()

    def favoritesRemoveLocation(self, location):
        for fav in self.favorites:
            if fav.type == "location" and fav.desktopFile == location:
                self.favoritesRemove(fav.position)

    def favoritesSave(self):
        new_faves = []

        for favorite in self.favorites:
            if favorite.type == "location":
                new_faves.append("location:" + favorite.desktopFile)
            else:
                new_faves.append(favorite.type)

        self.settings.set_strv("favorite-apps-list", new_faves)

    def isLocationInFavorites(self, location):
        for fav in self.favorites:
            if fav.type == "location" and fav.desktopFile == location:
                return True
        return False

    def on_drag_data_get(self, widget, context, selection, info, time):
        if info == self.TARGET_TYPE_FAV:
            self.drag_origin = widget.position
            selection.set_text(str(widget.position), -1)

    def on_drag_data_received(self, widget, context, x, y, selection, info, time):
        if info == self.TARGET_TYPE_FAV:
            self.favoritesReorder(int(selection.get_data().decode()), widget.position)

    # def on_icon_theme_changed(self, theme):
    #     print("on_icon_theme_changed")
    #     self.menuChanged(0, 0)

    def menuChanged(self, x, y):
        # print("menuChanged")
        # wait 1s, to avoid building the menu multiple times concurrently
        if self.menuChangedTimer:
            GLib.source_remove(self.menuChangedTimer)

        self.menuChangedTimer = GLib.timeout_add(1000, self.updateBoxes, True)

    #@print_timing
    def updateBoxes(self, menu_has_changed):
        # print("updateBoxes")
        # FIXME: This is really bad!
        if self.rebuildLock:
            return

        self.rebuildLock = True
        self.menuChangedTimer = None

        try:
            self.loadMenuFiles()

            # Find added and removed categories than update the category list
            newCategoryList = self.buildCategoryList()
            addedCategories = []
            removedCategories = []

            # TODO: optimize this!!!
            if not self.categoryList:
                addedCategories = newCategoryList
            else:
                for item in newCategoryList:
                    found = False
                    for item2 in self.categoryList:
                        pass
                        if (item["name"] == item2["name"] and
                            item["icon"] == item2["icon"] and
                            item["tooltip"] == item2["tooltip"] and
                            item["index"] == item2["index"]
                            ):
                            found = True
                            break
                    if not found:
                        addedCategories.append(item)

                for item in self.categoryList:
                    found = False
                    for item2 in newCategoryList:
                        if (item["name"] == item2["name"] and
                            item["icon"] == item2["icon"] and
                            item["tooltip"] == item2["tooltip"] and
                            item["index"] == item2["index"]
                            ):
                            found = True
                            break
                    if not found:
                        removedCategories.append(item)

            if self.showcategoryicons:
                categoryIconSize = self.iconSize
            else:
                categoryIconSize = 0

            for item in removedCategories:
                try:
                    button = item["button"]
                    self.categoryList.remove(item)
                    button.destroy()
                    del item
                except Exception as e:
                    print(e)

            if addedCategories:
                sortedCategoryList = []
                for item in self.categoryList:
                    try:
                        self.categoriesBox.remove(item["button"])
                        sortedCategoryList.append((str(item["index"]) + item["name"], item["button"]))
                    except Exception as e:
                        print(e)

                # Create new category buttons and add them to the list
                for item in addedCategories:
                    try:
                        item["button"] = CategoryButton(item["icon"], categoryIconSize, [item["name"]], item["filter"])

                        if self.categories_mouse_over:
                            startId = item["button"].connect("enter", self.StartFilter, item["filter"])
                            stopId = item["button"].connect("leave", self.StopFilter)
                            item["button"].mouseOverHandlerIds = (startId, stopId)
                        else:
                            item["button"].mouseOverHandlerIds = None

                        item["button"].connect("clicked", self.FilterAndClear, item["filter"])
                        item["button"].connect("focus-in-event", self.categoryBtnFocus, item["filter"])
                        item["button"].show()

                        self.categoryList.append(item)
                        sortedCategoryList.append((str(item["index"]) + item["name"], item["button"]))
                    except Exception as e:
                        print(e)

                sortedCategoryList.sort()

                for item in sortedCategoryList:
                    try:
                        self.categoriesBox.pack_start(item[1], False, False, 0)
                    except Exception as e:
                        print(e)

            # Find added and removed applications add update the application list
            newApplicationList = self.buildApplicationList()
            addedApplications = []
            removedApplications = []

            # TODO: optimize this!!!
            if not self.applicationList:
                addedApplications = newApplicationList
            else:
                for item in newApplicationList:
                    found = False
                    for item2 in self.applicationList:
                        if item["entry"].get_desktop_file_path() == item2["entry"].get_desktop_file_path():
                            found = True
                            break
                    if not found:
                        addedApplications.append(item)

                key = 0
                for item in self.applicationList:
                    found = False
                    for item2 in newApplicationList:
                        if item["entry"].get_desktop_file_path() == item2["entry"].get_desktop_file_path():
                            found = True
                            break
                    if not found:
                        removedApplications.append(key)
                    else:
                        # don't increment the key if this item is going to be removed
                        # because when it is removed the index of all later items is
                        # going to be decreased
                        key += 1

            for key in removedApplications:
                self.applicationList[key]["button"].destroy()
                del self.applicationList[key]
            if addedApplications:
                sortedApplicationList = []
                for item in self.applicationList:
                    self.applicationsBox.remove(item["button"])
                    sortedApplicationList.append((item["button"].appName, item["button"]))
                for item in addedApplications:
                    item["button"] = MenuApplicationLauncher(item["entry"].get_desktop_file_path(),
                            self.iconSize, item["category"], self.showapplicationcomments,
                            highlight=(True and menu_has_changed))
                    if item["button"].appExec:
                        self.mintMenuWin.setTooltip(item["button"], item["button"].getTooltip())
                        item["button"].connect("button-press-event", self.menuPopup)
                        item["button"].connect("focus-in-event", self.scrollItemIntoView)
                        item["button"].connect("clicked", RecentHelper.applicationButtonClicked)
                        if self.activeFilter[0] == 0:
                            item["button"].filterText(self.activeFilter[1])
                        else:
                            item["button"].filterCategory(self.activeFilter[1])
                        item["button"].desktop_file_path = item["entry"].get_desktop_file_path()
                        sortedApplicationList.append((item["button"].appName.upper(), item["button"]))
                        self.applicationList.append(item)
                    else:
                        item["button"].destroy()

                sortedApplicationList.sort()
                launcherNames = [] # Keep track of launcher names so we don't add them twice in the list..
                for item in sortedApplicationList:
                    launcherName = item[0]
                    button = item[1]
                    self.applicationsBox.add(button)
                    if launcherName in launcherNames:
                        button.hide()
                    else:
                        launcherNames.append(launcherName)
        except Exception as e:
            print(e)

        self.rebuildLock = False

    # Reload the menufiles from the filesystem
    def loadMenuFiles(self):
        if len(self.menuFiles) > 0:
            for menu in self.menuFiles:
                menu.tree.disconnect_by_func(self.menuChanged)
            self.menuFiles = []
        for mainitems in ["mate-applications.menu", "mate-settings.menu"]:
            mymenu = Menu(mainitems )
            mymenu.tree.connect("changed", self.menuChanged, None)
            self.menuFiles.append(mymenu)

    # Build a list of all categories in the menu ([{"name", "icon", tooltip"}]
    def buildCategoryList(self):
        newCategoryList = [{"name": _("All"),
                            "icon": "mintmenu-all-applications-symbolic",
                            "tooltip": _("Show all applications"),
                            "filter":"", "index": 0}]
        num = 1
        for menu in self.menuFiles:
            for child in get_contents(menu.directory):
                if isinstance(child, MateMenu.TreeDirectory):
                    name = child.get_name()
                    if child.get_icon() is None:
                        icon = "applications-other"
                    else:
                        icon = child.get_icon().to_string()
                    newCategoryList.append({"name": name,
                                            "icon": icon,
                                            "tooltip": name,
                                            "filter": name,
                                            "index": num})
            num += 1
        return newCategoryList

    # Build a list containing the DesktopEntry object and the category of each application in the menu
    def buildApplicationList(self):
        newApplicationsList = []

        def find_applications_recursively(app_list, directory, catName):
            for item in get_contents(directory):
                if isinstance(item, MateMenu.TreeEntry):
                    app_list.append({"entry": item, "category": catName})
                elif isinstance(item, MateMenu.TreeDirectory):
                    find_applications_recursively(app_list, item, catName)

        for menu in self.menuFiles:
            directory = menu.directory
            for entry in get_contents(directory):
                if isinstance(entry, MateMenu.TreeDirectory) and len(get_contents(entry)):
                    #Entry is a top-level category
                    #catName = entry.get_name()
                    #icon = str(entry.get_icon().to_string())
                    #if (icon == "applications-system" or icon == "applications-other"):
                    #       catName = self.adminMenu
                    for item in get_contents(entry):
                        if isinstance(item, MateMenu.TreeDirectory):
                            find_applications_recursively(newApplicationsList, item, entry.get_name())
                        elif isinstance(item, MateMenu.TreeEntry):
                            newApplicationsList.append({"entry": item, "category": entry.get_name()})
                #elif isinstance(entry, MateMenu.TreeEntry):
                #       if not (entry.get_is_excluded() or entry.get_is_nodisplay()):
                #               print "=======>>> " + item.get_name() + " = top level"
                #               newApplicationsList.append({"entry": item, "category": ""})

        return newApplicationsList
