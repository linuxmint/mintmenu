#!/usr/bin/python2

import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk, Pango, Gdk, Gio, GLib

import os
import time
import string
import gettext
import threading
import commands
import subprocess
import filecmp
import ctypes
from ctypes import *
from easybuttons import *
from execute import Execute
from easygsettings import EasyGSettings
from easyfiles import *

gtk = CDLL("libgtk-x11-2.0.so.0")

import matemenu

from user import home

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")

class PackageDescriptor():
    def __init__(self, name, summary, description):
        self.name = name
        self.summary = summary
        self.description = description

def print_timing(func):
    def wrapper(*arg):
        t1 = time.time()
        res = func(*arg)
        t2 = time.time()
        print '%s took %0.3f ms' % (func.func_name, (t2-t1)*1000.0)
        return res
    return wrapper

# Helper function for retrieving the user's location for storing new or modified menu items
def get_user_item_path():
    item_dir = None

    if os.environ.has_key('XDG_DATA_HOME'):
        item_dir = os.path.join(os.environ['XDG_DATA_HOME'], 'applications')
    else:
        item_dir = os.path.join(os.environ['HOME'], '.local', 'share', 'applications')

    if not os.path.isdir(item_dir):
        os.makedirs(item_dir)

    return item_dir

def get_system_item_paths():
    item_dirs = []
    if os.environ.has_key('XDG_DATA_DIRS'):
        item_dirs = os.environ['XDG_DATA_DIRS'].split(":")
    item_dirs.append(os.path.join('/usr', 'share'))
    return item_dirs

def rel_path(target, base=os.curdir):

    if not os.path.exists(target):
        raise OSError, 'Target does not exist: '+target

    if not os.path.isdir(base):
        raise OSError, 'Base is not a directory or does not exist: '+base

    base_list = (os.path.abspath(base)).split(os.sep)
    target_list = (os.path.abspath(target)).split(os.sep)

    for i in range(min(len(base_list), len(target_list))):
        if base_list[i] <> target_list[i]: break
        else:
            i += 1

    rel_list = [os.pardir] * (len(base_list)-i) + target_list[i:]

    return os.path.join(*rel_list)


class Menu:
    def __init__( self, MenuToLookup ):
        self.tree = matemenu.lookup_tree( MenuToLookup )
        self.directory = self.tree.get_root_directory()

    def getMenus( self, parent=None ):
        if parent == None:
            #gives top-level "Applications" item
            yield self.tree.root
        else:
            for menu in parent.get_contents():
                if menu.get_type() == matemenu.TYPE_DIRECTORY and self.__isVisible( menu ):
                    yield menu

    def getItems( self, menu ):
        for item in menu.get_contents():
            if item.get_type() == matemenu.TYPE_ENTRY and item.get_desktop_file_id()[-19:] != '-usercustom.desktop' and self.__isVisible( item ):
                yield item

    def __isVisible( self, item ):
        if item.get_type() == matemenu.TYPE_ENTRY:
            return not ( item.get_is_excluded() or item.get_is_nodisplay() )
        if item.get_type() == matemenu.TYPE_DIRECTORY and len( item.get_contents() ):
            return True



class SuggestionButton ( Gtk.Button ):

    def __init__( self, iconName, iconSize, label ):
        Gtk.Button.__init__( self )
        self.iconName = iconName
        self.set_relief( Gtk.ReliefStyle.NONE )
        self.set_size_request( -1, -1 )
        Align1 = Gtk.Alignment()
        Align1.set( 0, 0.5, 1.0, 0 )
        HBox1 = Gtk.HBox()
        labelBox = Gtk.VBox( False, 2 )
        self.image = Gtk.Image()
        self.image.set_from_stock( self.iconName, iconSize )
        self.image.show()
        HBox1.pack_start( self.image, False, False, 5 )
        self.label = Gtk.Label()
        self.label.set_ellipsize( Pango.EllipsizeMode.END )
        self.label.set_alignment( 0.0, 1.0 )
        self.label.show()
        labelBox.pack_start( self.label, True, True, 2 )
        labelBox.show()
        HBox1.pack_start( labelBox, True, True, 2 )
        HBox1.show()
        Align1.add( HBox1 )
        Align1.show()
        self.add( Align1 )
        self.show()

    def set_image(self, path):
        self.image.set_from_file(path)

    def set_text( self, text):
        self.label.set_markup(text)

    def set_icon_size (self, size):
        self.image.set_from_stock( self.iconName, size )

class TargetEntry(Structure):
    _fields_ = [("target", c_char_p),
                ("flags", c_int),
                ("info", c_int)]

class pluginclass( object ):
    TARGET_TYPE_TEXT = 80
    array2 = TargetEntry * 2
    toButton = array2( ("text/uri-list", 0, TARGET_TYPE_TEXT), ("text/uri-list", 0, TARGET_TYPE_TEXT) )
    TARGET_TYPE_FAV = 81
    array = TargetEntry * 3
    toFav = array( ( "FAVORITES", Gtk.TargetFlags.SAME_APP, 81 ), ( "text/plain", 0, 100 ), ( "text/uri-list", 0, 101 ) )
    array1 = TargetEntry * 2
    fromFav = array1( ("FAVORITES", Gtk.TargetFlags.SAME_APP, 81), ("FAVORITES", Gtk.TargetFlags.SAME_APP, 81) )

    @print_timing
    def __init__( self, mintMenuWin, toggleButton, de ):
        self.mintMenuWin = mintMenuWin

        self.mainMenus = [ ]

        self.toggleButton = toggleButton
        self.de = de

        self.builder = Gtk.Builder()
        # The Glade file for the plugin
        self.builder.add_from_file (os.path.join( os.path.dirname( __file__ ), "applications.glade" ))

        # Read GLADE file
        self.searchEntry =self.builder.get_object( "searchEntry" )
        self.searchButton =self.builder.get_object( "searchButton" )
        self.showAllAppsButton =self.builder.get_object( "showAllAppsButton" )
        self.showFavoritesButton =self.builder.get_object( "showFavoritesButton" )
        self.applicationsBox =self.builder.get_object( "applicationsBox" )
        self.categoriesBox =self.builder.get_object( "categoriesBox" )
        self.favoritesBox =self.builder.get_object( "favoritesBox" )
        self.applicationsScrolledWindow =self.builder.get_object( "applicationsScrolledWindow" )

        #i18n
        self.builder.get_object("searchLabel").set_text("<span weight='bold'>" + _("Search:") + "</span>")
        self.builder.get_object("searchLabel").set_use_markup(True)
        self.builder.get_object("label6").set_text(_("Favorites"))
        self.builder.get_object("label3").set_text(_("Favorites"))
        self.builder.get_object("label7").set_text(_("All applications"))
        self.builder.get_object("label2").set_text(_("Applications"))

        self.headingstocolor = [self.builder.get_object("label6"),self.builder.get_object("label2")]

        self.numApps = 0
        # These properties are NECESSARY to maintain consistency

        # Set 'window' property for the plugin (Must be the root widget)
        self.window =self.builder.get_object( "mainWindow" )

        # Set 'heading' property for plugin
        self.heading = ""#_("Applications")

        # This should be the first item added to the window in glade
        self.content_holder =self.builder.get_object( "Applications" )

        # Items to get custom colors
        self.itemstocolor = [self.builder.get_object( "viewport1" ),self.builder.get_object( "viewport2" ),self.builder.get_object( "viewport3" ) ]

        # Unset all timers
        self.filterTimer = None
        self.menuChangedTimer = None
        # Hookup for text input
        self.content_holder.connect( "key-press-event", self.keyPress )

        self.favoritesBox.connect( "drag-data-received", self.ReceiveCallback )

        gtk.gtk_drag_dest_set.argtypes = [c_void_p, c_ushort, c_void_p, c_int, c_ushort]
        gtk.gtk_drag_dest_set ( hash(self.favoritesBox), Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP,  self.toButton, 2, Gdk.DragAction.COPY )
        self.showFavoritesButton.connect( "drag-data-received", self.ReceiveCallback )
        gtk.gtk_drag_dest_set ( hash(self.showFavoritesButton), Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP, self.toButton, 2, Gdk.DragAction.COPY )

       # self.searchButton.connect( "button_release_event", self.SearchWithButton )
        try:
        # GSettings stuff
            self.settings = EasyGSettings( "com.linuxmint.mintmenu.plugins.applications" )
            self.GetGSettingsEntries()
            self.settings.notifyAdd( "icon-size", self.changeIconSize )
            self.settings.notifyAdd( "favicon-size", self.changeFavIconSize )
            self.settings.notifyAdd( "height", self.changePluginSize )
            self.settings.notifyAdd( "width", self.changePluginSize )
            self.settings.notifyAdd( "categories-mouse-over", self.changeCategoriesMouseOver )
            self.settings.notifyAdd( "swap-generic-name", self.changeSwapGenericName )
            self.settings.notifyAdd( "show-category-icons", self.changeShowCategoryIcons )
            self.settings.notifyAdd( "show-application-comments", self.changeShowApplicationComments )
            self.settings.notifyAdd( "use-apt", self.switchAPTUsage)
            self.settings.notifyAdd( "fav-cols", self.changeFavCols )
            self.settings.notifyAdd( "remember-filter", self.changeRememberFilter)
            self.settings.notifyAdd( "enable-internet-search", self.changeEnableInternetSearch)

            self.settings.bindGSettingsEntryToVar( "int", "category-hover-delay", self, "categoryhoverdelay" )
            self.settings.bindGSettingsEntryToVar( "bool", "do-not-filter", self, "donotfilterapps" )
            self.settings.bindGSettingsEntryToVar( "bool", "enable-internet-search", self, "enableInternetSearch" )
            self.settings.bindGSettingsEntryToVar( "string", "search-command", self, "searchtool" )
            self.settings.bindGSettingsEntryToVar( "int", "default-tab", self, "defaultTab" )
        except Exception, detail:
            print detail
        self.currentFavCol = 0
        self.favorites = []

        self.content_holder.set_size_request( self.width, self.height )
        self.categoriesBox.set_size_request( self.width / 3, -1 )
        self.applicationsBox.set_size_request( self.width / 2, -1 )

        self.buildingButtonList = False
        self.stopBuildingButtonList = False

        self.categoryList = []
        self.applicationList = []

        #dirty ugly hack, to get favorites drag origin position
        self.drag_origin = None

        self.rebuildLock = False
        self.activeFilter = (1, "", self.searchEntry)

        self.adminMenu = None

        for mainitems in [ "mate-applications.menu", "mate-settings.menu" ]:
            mymenu = Menu( mainitems )
            mymenu.tree.add_monitor( self.menuChanged, None )

        self.refresh_apt_cache()
        self.suggestions = []
        self.current_suggestion = None
        self.panel = "top"
        self.panel_position = -1

        self.builder.get_object("searchButton").connect( "button-press-event", self.searchPopup )

        self.icon_theme = Gtk.IconTheme.get_default();
        self.icon_theme.connect("changed", self.on_icon_theme_changed)


    def refresh_apt_cache(self):
        if self.useAPT:
            os.system("mkdir -p %s/.linuxmint/mintMenu/" % home)
            os.system("/usr/lib/linuxmint/mintMenu/plugins/get_apt_cache.py > %s/.linuxmint/mintMenu/apt.cache &" % home)

    def get_panel(self):
        panelsettings = Gio.Settings.new("org.mate.panel")
        applet_list = panelsettings.get_strv("object-id-list")
        for applet in applet_list:
            object_schema = Gio.Settings.new_with_path("org.mate.panel.object", "/org/mate/panel/objects/%s/" % (applet))
            keys = object_schema.list_keys()
            if "applet-iid" in keys:
                iid = object_schema.get_string("applet-iid")
                if iid is not None and iid.find("MintMenu") != -1:
                    self.panel = object_schema.get_string("toplevel-id")
                    self.panel_position = object_schema.get_int("position") + 1

    def apturl_install(self, widget, pkg_name):
        if os.path.exists("/usr/bin/apturl"):
            os.system("/usr/bin/apturl apt://%s &" % pkg_name)
        else:
            os.system("xdg-open apt://" + pkg_name + " &")
        self.mintMenuWin.hide()

    def __del__( self ):
        print u"Applications plugin deleted"

    def wake (self) :
        pass

    def destroy( self ):
        self.content_holder.destroy()
        self.searchEntry.destroy()
        self.searchButton.destroy()
        self.showAllAppsButton.destroy()
        self.showFavoritesButton.destroy()
        self.applicationsBox.destroy()
        self.categoriesBox.destroy()
        self.favoritesBox.destroy()

        self.settings.notifyRemoveAll()

    def changePluginSize( self, settings, key, args ):
        if key == "width":
            self.width = settings.get_int(key)
            self.categoriesBox.set_size_request( self.width / 3, -1 )
            self.applicationsBox.set_size_request( self.width / 2, -1 )

        elif key == "height":
            self.heigth = settings.get_int(key)
        self.content_holder.set_size_request( self.width, self.height )

    def changeSwapGenericName( self, settings, key, args ):
        self.swapgeneric = settings.get_boolean(key)

        for child in self.favoritesBox:
            if isinstance( child, FavApplicationLauncher):
                child.setSwapGeneric( self.swapgeneric )

    def changeShowCategoryIcons( self, settings, key, args ):
        self.showcategoryicons = settings.get_boolean(key)

        if self.showcategoryicons:
            categoryIconSize = self.iconSize
        else:
            categoryIconSize = 0

        for child in self.categoriesBox:
            child.setIconSize( categoryIconSize )

    def changeIconSize( self, settings, key, args ):
        self.iconSize = settings.get_int(key)

        if self.showcategoryicons:
            categoryIconSize = self.iconSize
        else:
            categoryIconSize = 0

        for child in self.categoriesBox:
            child.setIconSize( categoryIconSize )

        for child in self.applicationsBox:
            try:
                child.setIconSize( self.iconSize )
            except:
                pass

    def changeFavIconSize( self, settings, key, args ):
        self.faviconsize = settings.get_int(key)

        for child in self.favoritesBox:
            if isinstance( child, FavApplicationLauncher):
                child.setIconSize( self.faviconsize )

    def switchAPTUsage( self, settings, key, args ):
        self.useAPT = settings.get_boolean(key)
        self.refresh_apt_cache()

    def changeRememberFilter( self, settings, key, args):
        self.rememberFilter = settings.get_boolean(key)

    def changeEnableInternetSearch( self, settings, key, args):
        self.enableInternetSearch = settings.get_boolean(key)

    def changeShowApplicationComments( self, settings, key, args ):
        self.showapplicationcomments = settings.get_boolean(key)
        for child in self.applicationsBox:
            child.setShowComment( self.showapplicationcomments )

    def changeCategoriesMouseOver( self, settings, key, args ):
        self.categories_mouse_over = settings.get_boolean(key)
        for child in self.categoriesBox:
            if self.categories_mouse_over and not child.mouseOverHandlerIds:
                startId = child.connect( "enter", self.StartFilter, child.filter )
                stopId = child.connect( "leave", self.StopFilter )
                child.mouseOverHandlerIds = ( startId, stopId )
            elif not self.categories_mouse_over and child.mouseOverHandlerIds:
                child.disconnect( child.mouseOverHandlerIds[0] )
                child.disconnect( child.mouseOverHandlerIds[1] )
                child.mouseOverHandlerIds = None

    def changeFavCols(self, settings, key, args):
        self.favCols = settings.get_int(key)
        for fav in self.favorites:
            self.favoritesBox.remove( fav )
            self.favoritesPositionOnGrid( fav )

    def RegenPlugin( self, *args, **kargs ):
        self.refresh_apt_cache()

        # save old config - this is necessary because the app will notified when it sets the default values and you don't want the to reload itself several times
        oldcategories_mouse_over = self.categories_mouse_over
        oldiconsize = self.iconSize
        oldfaviconsize = self.faviconsize
        oldswapgeneric = self.swapgeneric
        oldshowcategoryicons = self.showcategoryicons
        oldcategoryhoverdelay = self.categoryhoverdelay
        oldsticky = self.sticky
        oldminimized = self.minimized
        oldicon = self.icon
        oldhideseparator = self.hideseparator
        oldshowapplicationcomments = self.showapplicationcomments

        self.GetGSettingsEntries()

        # if the config hasn't changed return
        if oldcategories_mouse_over == self.categories_mouse_over and oldiconsize == self.iconSize and oldfaviconsize == self.faviconsize and oldswapgeneric == self.swapgeneric and oldshowcategoryicons == self.showcategoryicons and oldcategoryhoverdelay == self.categoryhoverdelay and oldsticky == self.sticky and oldminimized == self.minimized and oldicon == self.icon and oldhideseparator == self.hideseparator and oldshowapplicationcomments == self.showapplicationcomments:
            return

        self.Todos()
        self.buildFavorites()
        self.RebuildPlugin()

    def GetGSettingsEntries( self ):

        self.categories_mouse_over = self.settings.get( "bool", "categories-mouse-over")
        self.width = self.settings.get( "int", "width")
        self.height = self.settings.get( "int", "height")
        self.donotfilterapps = self.settings.get( "bool", "do-not-filter")
        self.iconSize = self.settings.get( "int", "icon-size")
        self.faviconsize = self.settings.get( "int", "favicon-size")
        self.favCols = self.settings.get( "int", "fav-cols")
        self.swapgeneric = self.settings.get( "bool", "swap-generic-name")
        self.showcategoryicons = self.settings.get( "bool", "show-category-icons")
        self.categoryhoverdelay = self.settings.get( "int", "category-hover-delay")
        self.showapplicationcomments = self.settings.get( "bool", "show-application-comments")
        self.useAPT = self.settings.get( "bool", "use-apt")
        self.rememberFilter = self.settings.get( "bool", "remember-filter")
        self.enableInternetSearch = self.settings.get( "bool", "enable-internet-search")

        self.lastActiveTab =  self.settings.get( "int", "last-active-tab")
        self.defaultTab = self.settings.get( "int", "default-tab")


        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.settings.get( "bool", "sticky")
        self.minimized = self.settings.get( "bool", "minimized")

        # Search tool
        self.searchtool = self.settings.get( "string", "search-command")
        if self.searchtool == "beagle-search SEARCH_STRING":
            self.searchtool = "mate-search-tool --named \"%s\" --start"
            self.settings.set( "string", "search-command", "mate-search-tool --named \"%s\" --start" )

        # Plugin icon
        self.icon = self.settings.get( "string", "icon" )

        # Hide vertical dotted separator
        self.hideseparator = self.settings.get( "bool", "hide-separator")

    def SetHidden( self, state ):
        if state == True:
            self.settings.set( "bool", "minimized", True )
        else:
            self.settings.set( "bool", "minimized", False )

    def RebuildPlugin(self):
        self.content_holder.set_size_request( self.width, self.height )

    def checkMintMenuFolder( self ):
        if os.path.exists( os.path.join( os.path.expanduser( "~" ), ".linuxmint", "mintMenu", "applications" ) ):
            return True
        try:
            os.makedirs( os.path.join( os.path.expanduser( "~" ), ".linuxmint", "mintMenu", "applications" ) )
            return True
        except:
            pass

        return False

    def onShowMenu( self ):
        if len( self.favorites ):
            if self.defaultTab == -1:
                self.changeTab( self.lastActiveTab)
            else:
                self.changeTab( (self.defaultTab - 1) * -1   )
        else:
            self.changeTab( 1 )

        self.searchEntry.select_region( 0, -1 )
        if self.rememberFilter and self.searchEntry.get_text().strip() != "":
            self.Filter(self.activeFilter[2], self.activeFilter[1])

    def onHideMenu( self ):
        self.settings.set( "int", "last-active-tab", self.lastActiveTab )

    def changeTab( self, tabNum, clear = True ):
        notebook = self.builder.get_object( "notebook2" )
        if tabNum == 0:
            notebook.set_current_page( 0 )
        elif tabNum == 1:
            notebook.set_current_page( 1 )

        self.focusSearchEntry(clear)
        self.lastActiveTab = tabNum


    def Todos( self ):
        self.searchEntry.connect( "popup-menu", self.blockOnPopup )
        self.searchEntry.connect( "button-press-event", self.blockOnRightPress )
        self.searchEntry.connect( "changed", self.Filter )
        self.searchEntry.connect( "activate", self.Search )
        self.showAllAppsButton.connect( "clicked", lambda widget: self.changeTab( 1 ) )
        self.showFavoritesButton.connect( "clicked", lambda widget: self.changeTab( 0 ) )
        self.buildButtonList()

    def blockOnPopup( self, *args ):
        self.mintMenuWin.stopHiding()
        return False

    def blockOnRightPress( self, widget, event ):
        if event.button == 3:
            self.mintMenuWin.stopHiding()
        return False

    def focusSearchEntry( self, clear = True ):
        # grab_focus() does select all text,
        # restoring the original selection is somehow broken, so just select the end
        # of the existing text, that's the most likely candidate anyhow
        self.searchEntry.grab_focus()
        if self.rememberFilter or not clear:
            gtk.gtk_editable_set_position.argtypes = [c_void_p, c_int]
            gtk.gtk_editable_set_position(hash(self.searchEntry), -1)
        else:
            self.searchEntry.set_text("")

    def buildButtonList( self ):
        if self.buildingButtonList:
            self.stopBuildingButtonList = True
            GLib.timeout_add( 100, self.buildButtonList )
            return

        self.stopBuildingButtonList = False

        self.updateBoxes(False)

    def categoryBtnFocus( self, widget, event, category ):
        self.scrollItemIntoView( widget )
        self.StartFilter( widget, category )

    def StartFilter( self, widget, category ):
        # if there is a timer for a different category running stop it
        if self.filterTimer:
            GLib.source_remove( self.filterTimer )
        self.filterTimer = GLib.timeout_add( self.categoryhoverdelay, self.Filter, widget, category )

    def StopFilter( self, widget ):
        if self.filterTimer:
            GLib.source_remove( self.filterTimer )
            self.filterTimer = None

    def add_search_suggestions(self, text):

        text = "<b>%s</b>" % text

        if self.enableInternetSearch:
            suggestionButton = SuggestionButton(Gtk.STOCK_ADD, self.iconSize, "")
            suggestionButton.connect("clicked", self.search_ddg)
            suggestionButton.set_text(_("Search DuckDuckGo for %s") % text)
            suggestionButton.set_image("/usr/lib/linuxmint/mintMenu/search_engines/ddg.png")
            self.applicationsBox.add(suggestionButton)
            self.suggestions.append(suggestionButton)

            suggestionButton = SuggestionButton(Gtk.STOCK_ADD, self.iconSize, "")
            suggestionButton.connect("clicked", self.search_wikipedia)
            suggestionButton.set_text(_("Search Wikipedia for %s") % text)
            suggestionButton.set_image("/usr/lib/linuxmint/mintMenu/search_engines/wikipedia.ico")
            self.applicationsBox.add(suggestionButton)
            self.suggestions.append(suggestionButton)

            separator = Gtk.EventBox()
            separator.add(Gtk.HSeparator())
            separator.set_visible_window(False)
            separator.set_size_request(-1, 20)
            separator.type = "separator"
            separator.show_all()
            self.applicationsBox.add(separator)
            self.suggestions.append(separator)

        suggestionButton = SuggestionButton(Gtk.STOCK_ADD, self.iconSize, "")
        suggestionButton.connect("clicked", self.search_dictionary)
        suggestionButton.set_text(_("Lookup %s in Dictionary") % text)
        suggestionButton.set_image("/usr/lib/linuxmint/mintMenu/search_engines/dictionary.png")
        self.applicationsBox.add(suggestionButton)
        self.suggestions.append(suggestionButton)

        suggestionButton = SuggestionButton(Gtk.STOCK_FIND, self.iconSize, "")
        suggestionButton.connect("clicked", self.Search)
        suggestionButton.set_text(_("Search Computer for %s") % text)
        self.applicationsBox.add(suggestionButton)
        self.suggestions.append(suggestionButton)

        #self.last_separator = gtk.EventBox()
        #self.last_separator.add(gtk.HSeparator())
        #self.last_separator.set_size_request(-1, 20)
        #self.last_separator.type = "separator"
        #self.mintMenuWin.SetPaneColors( [  self.last_separator ] )
        #self.last_separator.show_all()
        #self.applicationsBox.add(self.last_separator)
        #self.suggestions.append(self.last_separator)

    def add_apt_filter_results(self, keyword):
        try:
            # Wait to see if the keyword has changed.. before doing anything
            current_keyword = keyword
            current_keyword = self.searchEntry.get_text()
            if keyword != current_keyword:
                return
            found_packages = []
            found_in_name = []
            found_elsewhere = []
            keywords = keyword.split(" ")
            command = "cat %(home)s/.linuxmint/mintMenu/apt.cache" % {'home':home}
            for word in keywords:
                command = "%(command)s | grep %(word)s" % {'command':command, 'word':word}
            pkgs = commands.getoutput(command)
            pkgs = pkgs.split("\n")
            num_pkg_found = 0
            for pkg in pkgs:
                values = string.split(pkg, "###")
                if len(values) == 4:
                    status = values[0]
                    if (status == "ERROR"):
                        print "Could not refresh APT cache"
                    elif (status == "CACHE"):
                        name = values[1]
                        summary = values[2]
                        description = values[3].replace("~~~", "\n")
                        package = PackageDescriptor(name, summary, description)
                        #See if all keywords are in the name (so we put these results at the top of the list)
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
                        num_pkg_found+=1
                    else:
                        print "Invalid status code: " + status

            found_packages.extend(found_in_name)
            found_packages.extend(found_elsewhere)
            if keyword == self.searchEntry.get_text() and len(found_packages) > 0:
                last_separator = Gtk.EventBox()
                last_separator.add(Gtk.HSeparator())
                last_separator.set_visible_window(False)
                last_separator.set_size_request(-1, 20)
                last_separator.type = "separator"
                last_separator.show_all()
                self.applicationsBox.add(last_separator)
                self.suggestions.append(last_separator)
                #Reduce the number of results to 10 max... it takes a HUGE amount of time to add the GTK box in the menu otherwise..
                if len(found_packages) > 10:
                    found_packages = found_packages[:10]
                for pkg in found_packages:
                    name = pkg.name
                    for word in keywords:
                        if word != "":
                            name = name.replace(word, "<b>%s</b>" % word);
                    suggestionButton = SuggestionButton(Gtk.STOCK_ADD, self.iconSize, "")
                    suggestionButton.connect("clicked", self.apturl_install, pkg.name)
                    suggestionButton.set_text(_("Install package '%s'") % name)
                    suggestionButton.set_tooltip_text("%s\n\n%s\n\n%s" % (pkg.name, pkg.summary, pkg.description))
                    suggestionButton.set_icon_size(self.iconSize)
                    self.applicationsBox.add(suggestionButton)
                    self.suggestions.append(suggestionButton)
                    #if cache != self.current_results:
                    #    self.current_results.append(pkg)

            #if len(found_packages) == 0:
            #    gtk.gdk.threads_enter()
            #    try:
            #        self.applicationsBox.remove(self.last_separator)
            #        self.suggestions.remove(self.last_separator)
            #    finally:
            #        gtk.gdk.threads_leave()

        except Exception, detail:
            print detail


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
                last_separator = Gtk.EventBox()
                last_separator.add(Gtk.HSeparator())
                last_separator.set_visible_window(False)
                last_separator.set_size_request(-1, 20)
                last_separator.type = "separator"
                last_separator.show_all()
                self.applicationsBox.add(last_separator)
                self.suggestions.append(last_separator)

            for pkg in found_packages:
                name = pkg.name
                for word in keywords:
                    if word != "":
                        name = name.replace(word, "<b>%s</b>" % word);
                suggestionButton = SuggestionButton(Gtk.STOCK_ADD, self.iconSize, "")
                suggestionButton.connect("clicked", self.apturl_install, pkg.name)
                suggestionButton.set_text(_("Install package '%s'") % name)
                suggestionButton.set_tooltip_text("%s\n\n%s\n\n%s" % (pkg.name, pkg.summary.capitalize(), pkg.description))
                suggestionButton.set_icon_size(self.iconSize)
                self.applicationsBox.add(suggestionButton)
                self.suggestions.append(suggestionButton)

            #if len(found_packages) == 0:
            #    self.applicationsBox.remove(self.last_separator)
            #    self.suggestions.remove(self.last_separator)

        except Exception, detail:
            print detail

    def Filter( self, widget, category = None ):
        self.filterTimer = None

        for suggestion in self.suggestions:
            self.applicationsBox.remove(suggestion)
        self.suggestions = []

        if widget == self.searchEntry:
            if self.donotfilterapps:
                widget.set_text( "" )
            else:
                text = widget.get_text()
                if self.lastActiveTab != 1:
                    self.changeTab( 1, clear = False )
                text = widget.get_text()
                showns = False # Are any app shown?
                shownList = []
                for i in self.applicationsBox.get_children():
                    shown = i.filterText( text )
                    if (shown):
                        dupe = False
                        for item in shownList:
                            if i.desktopFile == item.desktopFile:
                                dupe = True
                        if dupe:
                            i.hide()
                        else:
                            shownList.append(i)
                            #if this is the first matching item
                            #focus it
                            if(not showns):
                                i.grab_focus()
                            showns = True
                if (not showns and os.path.exists("/usr/bin/mintinstall")):
                    if len(text) >= 3:
                        if self.current_suggestion is not None and self.current_suggestion in text:
                            # We're restricting our search...
                            self.add_search_suggestions(text)
                            #if (len(self.current_results) > 0):
                                #self.add_apt_filter_results_sync(self.current_results, text)
                            #else:
                            GLib.timeout_add (300, self.add_apt_filter_results, text)
                        else:
                            self.current_results = []
                            self.add_search_suggestions(text)
                            GLib.timeout_add (300, self.add_apt_filter_results, text)

                        self.current_suggestion = text
                    else:
                        self.current_suggestion = None
                        self.current_results = []
                else:
                    self.current_suggestion = None
                    self.current_results = []

                for i in self.categoriesBox.get_children():
                    i.released()
                    i.set_relief( Gtk.ReliefStyle.NONE )

                allButton = self.categoriesBox.get_children()[0];
                allButton.set_relief( Gtk.ReliefStyle.HALF )
                self.activeFilter = (0, text, widget)
        else:
            #print "CATFILTER"
            self.activeFilter = (1, category, widget)
            if category == "":
                listedDesktopFiles = []
                for i in self.applicationsBox.get_children():
                    if not i.desktop_file_path in listedDesktopFiles:
                        listedDesktopFiles.append( i.desktop_file_path )
                        i.show_all()
                    else:
                        i.hide()
            else:
                for i in self.applicationsBox.get_children():
                    i.filterCategory( category )

            for i in self.categoriesBox.get_children():
                i.released()
                i.set_relief( Gtk.ReliefStyle.NONE )
            widget.set_relief( Gtk.ReliefStyle.HALF )

        self.applicationsScrolledWindow.get_vadjustment().set_value( 0 )

    def FilterAndClear( self, widget, category = None ):
        self.searchEntry.set_text( "" )
        self.Filter( widget, category )

    # Forward all text to the search box
    def keyPress( self, widget, event ):

        if event.string.strip() != "" or event.keyval == Gdk.KEY_BackSpace:
            self.searchEntry.grab_focus()
            gtk.gtk_editable_set_position.argtypes = [c_void_p, c_int]
            gtk.gtk_editable_set_position(hash(self.searchEntry), -1)
            self.searchEntry.event( event )
            return True


        if event.keyval == Gdk.KEY_space:
            self.searchEntry.event( event )
            return True

        if event.keyval == Gdk.KEY_Down and self.searchEntry.is_focus():
            self.applicationsBox.get_children()[0].grab_focus()

        return False

    def favPopup( self, widget, ev ):
        if ev.button == 3:
            if ev.y > widget.get_allocation().height / 2:
                insertBefore = False
            else:
                insertBefore = True

            if widget.type == "location":
                mTree = Gtk.Menu()
                mTree.set_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                                 Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
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
                removeFromFavMenuItem = Gtk.MenuItem(_("Remove from favorites"))
                separator4 = Gtk.SeparatorMenuItem()
                propsMenuItem = Gtk.MenuItem(_("Edit properties"))

                desktopMenuItem.connect("activate", self.add_to_desktop, widget)
                panelMenuItem.connect("activate", self.add_to_panel, widget)
                insertSpaceMenuItem.connect( "activate", self.onFavoritesInsertSpace, widget, insertBefore )
                insertSeparatorMenuItem.connect( "activate", self.onFavoritesInsertSeparator, widget, insertBefore )
                if widget.isInStartup():
                    startupMenuItem.set_active( True )
                    startupMenuItem.connect( "toggled", self.onRemoveFromStartup, widget )
                else:
                    startupMenuItem.set_active( False )
                    startupMenuItem.connect( "toggled", self.onAddToStartup, widget )
                launchMenuItem.connect( "activate", self.onLaunchApp, widget)
                removeFromFavMenuItem.connect( "activate", self.onFavoritesRemove, widget )
                propsMenuItem.connect( "activate", self.onPropsApp, widget)

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
                mTree.append(removeFromFavMenuItem)
                mTree.append(separator4)
                mTree.append(propsMenuItem)

                mTree.show_all()
                self.mintMenuWin.stopHiding()
                gtk.gtk_menu_popup.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p, c_uint, c_uint]
                gtk.gtk_menu_popup(hash(mTree), None, None, None, None, ev.button, ev.time)
            else:
                mTree = Gtk.Menu()
                mTree.set_events(Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.POINTER_MOTION_HINT_MASK |
                                 Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)

                #i18n
                removeMenuItem = Gtk.MenuItem(_("Remove"))
                insertSpaceMenuItem = Gtk.MenuItem(_("Insert space"))
                insertSeparatorMenuItem = Gtk.MenuItem(_("Insert separator"))
                mTree.append(removeMenuItem)
                mTree.append(insertSpaceMenuItem)
                mTree.append(insertSeparatorMenuItem)
                mTree.show_all()

                removeMenuItem.connect( "activate", self.onFavoritesRemove, widget )
                insertSpaceMenuItem.connect( "activate", self.onFavoritesInsertSpace, widget, insertBefore )
                insertSeparatorMenuItem.connect( "activate", self.onFavoritesInsertSeparator, widget, insertBefore )
                self.mintMenuWin.stopHiding()
                gtk.gtk_menu_popup.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p, c_uint, c_uint]
                gtk.gtk_menu_popup(hash(mTree), None, None, None, None, ev.button, ev.time)

    def menuPopup( self, widget, event ):
        if event.button == 3:
            mTree = Gtk.Menu()
            #i18n
            desktopMenuItem = Gtk.MenuItem(_("Add to desktop"))
            panelMenuItem = Gtk.MenuItem(_("Add to panel"))
            separator1 = Gtk.SeparatorMenuItem()
            favoriteMenuItem = Gtk.CheckMenuItem(_("Show in my favorites"))
            startupMenuItem = Gtk.CheckMenuItem(_("Launch when I log in"))
            separator2 = Gtk.SeparatorMenuItem()
            launchMenuItem = Gtk.MenuItem(_("Launch"))
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
            mTree.append(uninstallMenuItem)
            if home in widget.desktopFile:
                mTree.append(deleteMenuItem)
                deleteMenuItem.connect("activate", self.delete_from_menu, widget)

            mTree.append(separator3)

            mTree.append(propsMenuItem)

            mTree.show_all()

            desktopMenuItem.connect("activate", self.add_to_desktop, widget)
            panelMenuItem.connect("activate", self.add_to_panel, widget)

            launchMenuItem.connect( "activate", self.onLaunchApp, widget )
            propsMenuItem.connect( "activate", self.onPropsApp, widget)
            uninstallMenuItem.connect ( "activate", self.onUninstallApp, widget )

            if self.isLocationInFavorites( widget.desktopFile ):
                favoriteMenuItem.set_active( True )
                favoriteMenuItem.connect( "toggled", self.onRemoveFromFavorites, widget )
            else:
                favoriteMenuItem.set_active( False )
                favoriteMenuItem.connect( "toggled", self.onAddToFavorites, widget )

            if widget.isInStartup():
                startupMenuItem.set_active( True )
                startupMenuItem.connect( "toggled", self.onRemoveFromStartup, widget )
            else:
                startupMenuItem.set_active( False )
                startupMenuItem.connect( "toggled", self.onAddToStartup, widget )

            self.mintMenuWin.stopHiding()
            gtk.gtk_menu_popup.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p, c_uint, c_uint]
            gtk.gtk_menu_popup(hash(mTree), None, None, None, None, event.button, event.time)


    def searchPopup( self, widget=None, event=None ):
        menu = Gtk.Menu()

        if self.enableInternetSearch:

            menuItem = Gtk.ImageMenuItem(_("Search DuckDuckGo"))
            img = Gtk.Image()
            img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/ddg.png')
            menuItem.set_image(img)
            menuItem.connect("activate", self.search_ddg)
            menu.append(menuItem)

            menuItem = Gtk.ImageMenuItem(_("Search Wikipedia"))
            img = Gtk.Image()
            img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/wikipedia.ico')
            menuItem.set_image(img)
            menuItem.connect("activate", self.search_wikipedia)
            menu.append(menuItem)

            menuItem = Gtk.SeparatorMenuItem()
            menu.append(menuItem)

        menuItem = Gtk.ImageMenuItem(_("Lookup Dictionary"))
        img = Gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/dictionary.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_dictionary)
        menu.append(menuItem)

        menuItem = Gtk.ImageMenuItem(_("Search Computer"))
        img = Gtk.Image()
        img.set_from_stock(Gtk.STOCK_FIND, self.iconSize)
        menuItem.set_image(img)
        menuItem.connect("activate", self.Search)
        menu.append(menuItem)

        menuItem = Gtk.SeparatorMenuItem()
        menu.append(menuItem)

        menuItem = Gtk.ImageMenuItem(_("Find Software"))
        img = Gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/software.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_software)
        menu.append(menuItem)

        menuItem = Gtk.ImageMenuItem(_("Find Tutorials"))
        img = Gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/tutorials.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_tutorials)
        menu.append(menuItem)

        menuItem = Gtk.ImageMenuItem(_("Find Hardware"))
        img = Gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/hardware.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_hardware)
        menu.append(menuItem)

        menuItem =Gtk.ImageMenuItem(_("Find Ideas"))
        img = Gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/ideas.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_ideas)
        menu.append(menuItem)

        menuItem = Gtk.ImageMenuItem(_("Find Users"))
        img = Gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/users.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_users)
        menu.append(menuItem)

        menu.show_all()

        self.mintMenuWin.stopHiding()
        gtk.gtk_menu_popup.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p, c_void_p, c_uint, c_uint]
        gtk.gtk_menu_popup(hash(menu), None, None, None, None, event.button, event.time)

        #menu.attach_to_widget(self.searchButton, None)
        #menu.reposition()
        #menu.reposition()
        #self.mintMenuWin.grab()
        self.focusSearchEntry(clear = False)
        return True

    def pos_func(self, menu=None):
        rect = self.searchButton.get_allocation()
        x = rect.x + rect.width
        y = rect.y + rect.height
        return (x, y, False)

    def search_ddg(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "+")
        os.system("xdg-open \"https://duckduckgo.com/?q=%s&t=lm&ia=web\" &" % text)
        self.mintMenuWin.hide()

    def search_wikipedia(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "+")
        os.system("xdg-open \"http://en.wikipedia.org/wiki/Special:Search?search=" + text + "\" &")
        self.mintMenuWin.hide()

    def search_dictionary(self, widget):
        text = self.searchEntry.get_text()
        os.system("mate-dictionary \"" + text + "\" &")
        self.mintMenuWin.hide()

    def search_mint_tutorials(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "%20")
        os.system("xdg-open \"http://community.linuxmint.com/index.php/tutorial/search/0/" + text + "\" &")
        self.mintMenuWin.hide()

    def search_mint_ideas(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "%20")
        os.system("xdg-open \"http://community.linuxmint.com/index.php/idea/search/0/" + text + "\" &")
        self.mintMenuWin.hide()

    def search_mint_users(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "%20")
        os.system("xdg-open \"http://community.linuxmint.com/index.php/user/search/0/" + text + "\" &")
        self.mintMenuWin.hide()

    def search_mint_hardware(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "%20")
        os.system("xdg-open \"http://community.linuxmint.com/index.php/hardware/search/0/" + text + "\" &")
        self.mintMenuWin.hide()

    def search_mint_software(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "%20")
        os.system("xdg-open \"http://community.linuxmint.com/index.php/software/search/0/" + text + "\" &")
        self.mintMenuWin.hide()

    def add_to_desktop(self, widget, desktopEntry):
        os.system("xdg-desktop-icon install --novendor %s" % desktopEntry.desktopFile)

    def add_to_panel(self, widget, desktopEntry):
        self.get_panel()
        i = 0
        panel_schema = Gio.Settings.new("org.mate.panel")
        applet_list = panel_schema.get_strv("object-id-list")

        while True:
            test_obj = "object_%d" % (i)
            if test_obj in applet_list:
                i += 1
            else:
                break

        path = "/org/mate/panel/objects/%s/" % (test_obj)
        new_schema = Gio.Settings.new_with_path("org.mate.panel.object", path)
        new_schema.set_string("launcher-location", desktopEntry.desktopFile)
        new_schema.set_string("object-type", "launcher")
        new_schema.set_string("toplevel-id", self.panel)
        new_schema.set_int("position", self.panel_position)
        applet_list.append(test_obj)
        panel_schema.set_strv("object-id-list", applet_list)

    def delete_from_menu(self, widget, desktopEntry):
        try:
            os.system("rm \"%s\" &" % desktopEntry.desktopFile)
        except Exception, detail:
            print detail

    def onLaunchApp( self, menu, widget ):
        widget.execute()
        self.mintMenuWin.hide()

    def onPropsApp( self, menu, widget ):

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


    def onUninstallApp( self, menu, widget ):
        widget.uninstall()
        self.mintMenuWin.hide()

    def onFavoritesInsertSpace( self, menu, widget, insertBefore ):
        if insertBefore:
            self.favoritesAdd( self.favoritesBuildSpace(), widget.position )
        else:
            self.favoritesAdd( self.favoritesBuildSpace(), widget.position + 1 )

    def onFavoritesInsertSeparator( self, menu, widget, insertBefore ):
        if insertBefore:
            self.favoritesAdd( self.favoritesBuildSeparator(), widget.position )
        else:
            self.favoritesAdd( self.favoritesBuildSeparator(), widget.position + 1 )

    def onFavoritesRemove( self, menu, widget ):
        self.favoritesRemove( widget.position )

    def onAddToStartup( self, menu, widget ):
        widget.addToStartup()

    def onRemoveFromStartup( self, menu, widget ):
        widget.removeFromStartup()

    def onAddToFavorites( self, menu, widget  ):
        self.favoritesAdd( self.favoritesBuildLauncher( widget.desktopFile ) )

    def onRemoveFromFavorites( self, menu, widget ):
        self.favoritesRemoveLocation( widget.desktopFile )

    def ReceiveCallback( self, widget, context, x, y, selection, targetType, time ):
        if targetType == self.TARGET_TYPE_TEXT:
            for uri in selection.get_uris():
                self.favoritesAdd( self.favoritesBuildLauncher( uri ) )

    def Search( self, widget ):

        text = self.searchEntry.get_text().strip()
        if text != "":
            for app_button in self.applicationsBox.get_children():
                if( isinstance(app_button, ApplicationLauncher) and app_button.filterText( text ) ):
                    app_button.execute()
                    self.mintMenuWin.hide()
                    return

            self.mintMenuWin.hide()
            fullstring = self.searchtool.replace( "%s", text )
            os.system(fullstring + " &")

    def SearchWithButton( self, widget, event ):
        self.Search( widget )

    def do_plugin( self ):
        self.Todos()
        self.buildFavorites()

    # Scroll button into view
    def scrollItemIntoView( self, widget, event = None ):
        viewport = widget.parent
        while not isinstance( viewport, Gtk.Viewport ):
            if not viewport.parent:
                return
            viewport = viewport.parent
        aloc = widget.get_allocation()
        viewport.get_vadjustment().clamp_page(aloc.y, aloc.y + aloc.height)

    def favoritesBuildSpace( self ):
        space = Gtk.EventBox()
        space.set_size_request( -1, 20 )
        space.set_visible_window(False)
        space.connect( "button-press-event", self.favPopup )
        space.type = "space"

        space.show()

        return space

    def favoritesBuildSeparator( self ):
        separator = Gtk.HSeparator()
        separator.set_size_request( -1, 20 )
        separator.type = "separator"

        separator.show_all()
        box = Gtk.EventBox()
        box.type = "separator"
        box.add(separator)
        box.set_visible_window(False)
        box.connect( "button-press-event", self.favPopup )
        box.show_all()
        return box

    def favoritesBuildLauncher( self, location ):
        try:
            ButtonIcon = None
            # For Folders and Network Shares
            location = string.join( location.split( "%20" ) )

            if location.startswith( "file" ):
                ButtonIcon = "mate-fs-directory"

            if location.startswith( "smb" ) or location.startswith( "ssh" ) or location.startswith( "network" ):
                ButtonIcon = "mate-fs-network"

            #For Special locations
            if location == "x-nautilus-desktop:///computer":
                location = "/usr/share/applications/nautilus-computer.desktop"
            elif location == "x-nautilus-desktop:///home":
                location =  "/usr/share/applications/nautilus-home.desktop"
            elif location == "x-nautilus-desktop:///network":
                location = "/usr/share/applications/network-scheme.desktop"
            elif location.startswith( "x-nautilus-desktop:///" ):
                location = "/usr/share/applications/nautilus-computer.desktop"

            if location.startswith( "file://" ):
                location = location[7:]

            # Don't add a location twice
            for fav in self.favorites:
                if fav.type == "location" and fav.desktopFile == location:
                    return None

            favButton = FavApplicationLauncher( location, self.faviconsize, self.swapgeneric )
            if favButton.appExec:
                favButton.show()
                favButton.connect( "popup-menu", self.favPopup )
                favButton.connect( "button-press-event", self.favPopup )
                favButton.connect( "focus-in-event", self.scrollItemIntoView )
                favButton.connect( "clicked", lambda w: self.mintMenuWin.hide() )

                self.mintMenuWin.setTooltip( favButton, favButton.getTooltip() )
                favButton.type = "location"
                return favButton
        except Exception, e:
            print u"File in favorites not found: '" + location + "'", e

        return None

    def buildFavorites( self ):
        try:
            if (not os.path.exists(home + "/.linuxmint/mintMenu/applications.list")):
                os.system("mkdir -p " + home + "/.linuxmint/mintMenu/applications")
                os.system("cp /usr/lib/linuxmint/mintMenu/applications.list " + home + "/.linuxmint/mintMenu/applications.list")

            applicationsFile = open ( os.path.join( os.path.expanduser( "~" ), ".linuxmint", "mintMenu", "applications.list" ), "r" )
            applicationsList = applicationsFile.readlines()

            self.favorites =  []

            for child in self.favoritesBox:
                child.destroy()

            position = 0

            for app in applicationsList :
                app = app.strip()

                if app[0:9] == "location:":
                    favButton = self.favoritesBuildLauncher( app[9:] )
                elif app == "space":
                    favButton = self.favoritesBuildSpace()
                elif app == "separator":
                    favButton = self.favoritesBuildSeparator()
                else:
                    if ( app.endswith( ".desktop" ) ):
                        favButton = self.favoritesBuildLauncher( app )
                    else:
                        favButton = None


                if favButton:
                    favButton.position = position
                    self.favorites.append( favButton )
                    self.favoritesPositionOnGrid( favButton )
                    favButton.connect( "drag-data-received", self.onFavButtonDragReorder )
                    gtk.gtk_drag_dest_set.argtypes = [c_void_p, c_ushort, c_void_p, c_int, c_ushort]
                    gtk.gtk_drag_dest_set( hash(favButton), Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP, self.fromFav, 2, Gdk.DragAction.COPY )
                    favButton.connect( "drag-data-get", self.onFavButtonDragReorderGet )
                    gtk.gtk_drag_source_set.argtypes = [c_void_p, c_ushort, c_void_p, c_int, c_ushort]
                    gtk.gtk_drag_source_set( hash(favButton), Gdk.ModifierType.BUTTON1_MASK, self.toFav, 3, Gdk.DragAction.COPY )
                    position += 1

            self.favoritesSave()
        except Exception, e:
            print e

    def favoritesGetNumRows( self ):
        rows = 0
        col = 0
        for fav in self.favorites:
            if  ( fav.type == "separator" or fav.type == "space" ) and col != 0:
                rows += 1
                col = 0
            col += 1
            if  fav.type == "separator" or fav.type == "space":
                rows += 1
                col = 0

            if col >= self.favCols:
                rows += 1
                col = 0
        return rows

    def favoritesPositionOnGrid( self, favorite ):
        row = 0
        col = 0
        for fav in self.favorites:
            if  ( fav.type == "separator" or fav.type == "space" ) and col != 0:
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
            self.favoritesBox.attach( favorite, col, col + self.favCols, row, row + 1, yoptions = 0 )
        else:
            self.favoritesBox.attach( favorite, col, col + 1, row, row + 1, yoptions = 0 )

    def favoritesReorder( self, oldposition, newposition ):
        if oldposition == newposition:
            return
        tmp = self.favorites[ oldposition ]
        if newposition > oldposition:
            if ( self.favorites[ newposition - 1 ].type == "space" or self.favorites[ newposition - 1 ].type == "separator" ) and self.favCols > 1:
                newposition = newposition - 1
            for i in range( oldposition, newposition ):
                self.favorites[ i ] = self.favorites[ i + 1 ]
                self.favorites[ i ].position = i
        elif newposition < oldposition:
            for i in range( 0,  oldposition - newposition ):
                self.favorites[ oldposition - i ] = self.favorites[ oldposition - i - 1 ]
                self.favorites[ oldposition - i ] .position = oldposition - i
        self.favorites[ newposition ] = tmp
        self.favorites[ newposition ].position = newposition

        for fav in self.favorites:
            self.favoritesBox.remove( fav )
            self.favoritesPositionOnGrid( fav )

        self.favoritesSave()
        self.favoritesBox.resize( self.favoritesGetNumRows(), self.favCols )

    def favoritesAdd( self, favButton, position = -1 ):
        if favButton:
            favButton.position = len( self.favorites )
            self.favorites.append( favButton )
            self.favoritesPositionOnGrid( favButton )

            favButton.connect( "drag-data-received", self.onFavButtonDragReorder )
            gtk.gtk_drag_dest_set.argtypes = [c_void_p, c_ushort, c_void_p, c_int, c_ushort]
            gtk.gtk_drag_dest_set( hash(favButton), Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP, self.toFav, 3, Gdk.DragAction.COPY )
            favButton.connect( "drag-data-get", self.onFavButtonDragReorderGet )
            gtk.gtk_drag_source_set.argtypes = [c_void_p, c_ushort, c_void_p, c_int, c_ushort]
            gtk.gtk_drag_source_set ( hash(favButton), Gdk.ModifierType.BUTTON1_MASK, self.toFav, 3, Gdk.DragAction.COPY )

            if position >= 0:
                self.favoritesReorder( favButton.position, position )

            self.favoritesSave()

    def favoritesRemove( self, position ):
        tmp = self.favorites[ position ]
        self.favorites.remove( self.favorites[ position ] )
        tmp.destroy()

        for i in range( position, len( self.favorites ) ):
            self.favorites[ i ].position = i
            self.favoritesBox.remove( self.favorites[ i ] )
            self.favoritesPositionOnGrid( self.favorites[ i ] )
        self.favoritesSave()
        self.favoritesBox.resize( self.favoritesGetNumRows(), self.favCols )

    def favoritesRemoveLocation( self, location ):
        for fav in self.favorites:
            if fav.type == "location" and fav.desktopFile == location:
                self.favoritesRemove( fav.position )

    def favoritesSave( self ):
        try:
            self.checkMintMenuFolder()
            appListFile = open( os.path.join( os.path.expanduser( "~"), ".linuxmint", "mintMenu", "applications.list" ) , "w" )

            for favorite in self.favorites:
                if favorite.type == "location":
                    appListFile.write( "location:" + favorite.desktopFile + "\n" )
                else:
                    appListFile.write( favorite.type + "\n" )

            appListFile.close( )
        except Exception, e:
            msgDlg = Gtk.MessageDialog( None, gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, _("Couldn't save favorites. Check if you have write access to ~/.linuxmint/mintMenu")+"\n(" + e.__str__() + ")" )
            msgDlg.run();
            msgDlg.destroy();

    def isLocationInFavorites( self, location ):
        for fav in self.favorites:
            if fav.type == "location" and fav.desktopFile == location:
                return True

        return False

    def onFavButtonDragReorderGet( self, widget, context, selection, targetType, eventTime ):
        if targetType == self.TARGET_TYPE_FAV:
            self.drag_origin = widget.position
            selection.set( selection.target, 8, str(widget.position))

    def onFavButtonDragReorder( self, widget, context, x, y, selection, targetType, time  ):
        if targetType == self.TARGET_TYPE_FAV:
            #self.favoritesReorder( int(selection.data), widget.position )
            self.favoritesReorder( self.drag_origin, widget.position )

    def on_icon_theme_changed(self, theme):
        print "on_icon_theme_changed"
        self.menuChanged (0, 0)

    def menuChanged( self, x, y ):
        print ("menuChanged")
        # wait 1s, to avoid building the menu multiple times concurrently
        if self.menuChangedTimer:
            GLib.source_remove( self.menuChangedTimer )

        self.menuChangedTimer = GLib.timeout_add( 1000, self.updateBoxes, True )

    def updateBoxes( self, menu_has_changed ):
        print ("updateBoxes")
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
                        if item["name"] == item2["name"] and item["icon"] == item2["icon"] and item["tooltip"] == item2["tooltip"] and item["index"] == item2["index"]:
                            found = True
                            break
                    if not found:
                        addedCategories.append(item)

                for item in self.categoryList:
                    found = False
                    for item2 in newCategoryList:
                        if item["name"] == item2["name"] and item["icon"] == item2["icon"] and item["tooltip"] == item2["tooltip"] and item["index"] == item2["index"]:
                            found = True
                            break
                    if not found:
                        removedCategories.append( item )

            if self.showcategoryicons == True:
                categoryIconSize = self.iconSize
            else:
                categoryIconSize = 0

            for item in removedCategories:
                try:
                    button = item["button"]
                    self.categoryList.remove(item)
                    button.destroy()
                    del item
                except Exception, e:
                    print e

            if addedCategories:
                sortedCategoryList = []
                for item in self.categoryList:
                    try:
                        self.categoriesBox.remove( item["button"] )
                        sortedCategoryList.append( ( str(item["index"]) + item["name"], item["button"] ) )
                    except Exception, e:
                        print e

                # Create new category buttons and add the to the list
                for item in addedCategories:
                    try:
                        item["button"] = CategoryButton( item["icon"], categoryIconSize, [ item["name"] ], item["filter"] )
                        self.mintMenuWin.setTooltip( item["button"], item["tooltip"] )

                        if self.categories_mouse_over:
                            startId = item["button"].connect( "enter", self.StartFilter, item["filter"] )
                            stopId = item["button"].connect( "leave", self.StopFilter )
                            item["button"].mouseOverHandlerIds = ( startId, stopId )
                        else:
                            item["button"].mouseOverHandlerIds = None

                        item["button"].connect( "clicked", self.FilterAndClear, item["filter"] )
                        item["button"].connect( "focus-in-event", self.categoryBtnFocus, item["filter"] )
                        item["button"].show()

                        self.categoryList.append( item )
                        sortedCategoryList.append( ( str(item["index"]) + item["name"], item["button"] ) )
                    except Exception, e:
                        print e

                sortedCategoryList.sort()

                for item in sortedCategoryList:
                    try:
                        self.categoriesBox.pack_start( item[1], False, False, 0 )
                    except Exception, e:
                        print e


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
                    self.applicationsBox.remove( item["button"] )
                    sortedApplicationList.append( ( item["button"].appName, item["button"] ) )
                for item in addedApplications:
                    item["button"] = MenuApplicationLauncher( item["entry"].get_desktop_file_path(), self.iconSize, item["category"], self.showapplicationcomments, highlight=(True and menu_has_changed) )
                    if item["button"].appExec:
                        self.mintMenuWin.setTooltip( item["button"], item["button"].getTooltip() )
                        item["button"].connect( "button-press-event", self.menuPopup )
                        item["button"].connect( "focus-in-event", self.scrollItemIntoView )
                        item["button"].connect( "clicked", lambda w: self.mintMenuWin.hide() )
                        if self.activeFilter[0] == 0:
                            item["button"].filterText( self.activeFilter[1] )
                        else:
                            item["button"].filterCategory( self.activeFilter[1] )
                        item["button"].desktop_file_path = item["entry"].get_desktop_file_path()
                        sortedApplicationList.append( ( item["button"].appName.upper(), item["button"] ) )
                        self.applicationList.append( item )
                    else:
                        item["button"].destroy()


                sortedApplicationList.sort()
                launcherNames = [] # Keep track of launcher names so we don't add them twice in the list..
                for item in sortedApplicationList:
                    launcherName = item[0]
                    button = item[1]
                    self.applicationsBox.pack_start( button, False, False, 0 )
                    if launcherName in launcherNames:
                        button.hide()
                    else:
                        launcherNames.append(launcherName)
        except Exception, e:
            print e

        self.rebuildLock = False

    # Reload the menufiles from the filesystem
    def loadMenuFiles( self ):
        self.menuFiles = []
        for mainitems in [ "mate-applications.menu", "mate-settings.menu" ]:
            self.menuFiles.append( Menu( mainitems) )

    # Build a list of all categories in the menu ( [ { "name", "icon", tooltip" } ]
    def buildCategoryList( self ):
        newCategoryList = [ { "name": _("All"), "icon": "stock_select-all", "tooltip": _("Show all applications"), "filter":"", "index": 0 } ]

        num = 1

        for menu in self.menuFiles:
            for child in menu.directory.get_contents():
                if child.get_type() == matemenu.TYPE_DIRECTORY:
                    icon =  str(child.icon)
                    #if (icon == "preferences-system"):
                    #       self.adminMenu = child.name
                    #if (icon != "applications-system" and icon != "applications-other"):
                    newCategoryList.append( { "name": child.name, "icon": child.icon, "tooltip": child.name, "filter": child.name, "index": num } )
            num += 1

        return newCategoryList

    # Build a list containing the DesktopEntry object and the category of each application in the menu
    def buildApplicationList( self ):

        newApplicationsList = []

        def find_applications_recursively(app_list, directory, catName):
            for item in directory.get_contents():
                if item.get_type() == matemenu.TYPE_ENTRY:
                    print "=======>>> " + str(item.name) + " = " + str(catName)
                    app_list.append( { "entry": item, "category": catName } )
                elif item.get_type() == matemenu.TYPE_DIRECTORY:
                    find_applications_recursively(app_list, item, catName)

        for menu in self.menuFiles:
            directory = menu.directory
            for entry in directory.get_contents():
                if entry.get_type() == matemenu.TYPE_DIRECTORY and len(entry.get_contents()):
                    #Entry is a top-level category
                    #catName = entry.name
                    #icon = str(entry.icon)
                    #if (icon == "applications-system" or icon == "applications-other"):
                    #       catName = self.adminMenu
                    for item in entry.get_contents():
                        if item.get_type() == matemenu.TYPE_DIRECTORY:
                            find_applications_recursively(newApplicationsList, item, entry.name)
                        elif item.get_type() == matemenu.TYPE_ENTRY:
                            newApplicationsList.append( { "entry": item, "category": entry.name } )
                #elif entry.get_type() == matemenu.TYPE_ENTRY:
                #       if not (entry.get_is_excluded() or entry.get_is_nodisplay()):
                #               print "=======>>> " + item.name + " = top level"
                #               newApplicationsList.append( { "entry": item, "category": "" } )

        return newApplicationsList
