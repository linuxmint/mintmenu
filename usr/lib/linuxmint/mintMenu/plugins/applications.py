#!/usr/bin/env python

import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk, GObject, Pango, Gdk

import os
import mateconf
import fnmatch
import time
import string
import gettext
import threading
import commands
import subprocess
import filecmp

from easybuttons import *
from execute import Execute
from easygconf import EasyGConf
from easyfiles import *

#from filemonitor import monitor as filemonitor

#import xdg.Menu
import matemenu

from user import home

GObject.threads_init()

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

# Evil patching
#def xdgParsePatched(filename=None):
#       # conver to absolute path
#       if filename and not os.path.isabs(filename):
#               filename = xdg.Menu.__getFileName(filename)
#
#       # use default if no filename given
#       if not filename:
#               filename = xdg.Menu.__getFileName("applications.menu")
#
#       if not filename:
#               raise xdg.Menu.ParsingError(_("File not found"), "/etc/xdg/menus/applications.menu")
#
#       # check if it is a .menu file
#       if not os.path.splitext(filename)[1] == ".menu":
#               raise xdg.Menu.ParsingError(_("Not a .menu file"), filename)
#
#       # create xml parser
#       try:
#               doc = xdg.Menu.xml.dom.minidom.parse(filename)
#       except xdg.Menu.xml.parsers.expat.ExpatError:
#               raise xdg.Menu.ParsingError(_("Not a valid .menu file"), filename)
#
#       # parse menufile
#       xdg.Menu.tmp["Root"] = ""
#       xdg.Menu.tmp["mergeFiles"] = []
#       xdg.Menu.tmp["DirectoryDirs"] = []
#       xdg.Menu.tmp["cache"] = xdg.Menu.MenuEntryCache()
#
#       xdg.Menu.__parse(doc, filename, xdg.Menu.tmp["Root"])
#       xdg.Menu.__parsemove(xdg.Menu.tmp["Root"])
#       xdg.Menu.__postparse(xdg.Menu.tmp["Root"])
#
#       xdg.Menu.tmp["Root"].Doc = doc
#       xdg.Menu.tmp["Root"].Filename = filename
#
#       # generate the menu
#       xdg.Menu.__genmenuNotOnlyAllocated(xdg.Menu.tmp["Root"])
#       xdg.Menu.__genmenuOnlyAllocated(xdg.Menu.tmp["Root"])
#
#       # and finally sort
#       xdg.Menu.sort(xdg.Menu.tmp["Root"])
#       xdg.Menu.tmp["Root"].Files = xdg.Menu.tmp["mergeFiles"] + [ xdg.Menu.tmp["Root"].Filename ]
#       return xdg.Menu.tmp["Root"]
#
#xdg.Menu.parse = xdgParsePatched

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
    item_dir = None

    if os.environ.has_key('XDG_DATA_DIRS'):
        item_dirs = os.environ['XDG_DATA_DIRS'].split(":")
    else:
        item_dirs = [os.path.join('usr', 'share')]

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
        Align1 = Gtk.Alignment( 0, 0.5, 1.0, 0 )
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
        labelBox.pack_start( self.label )
        labelBox.show()
        HBox1.pack_start( labelBox )
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

class pluginclass( object ):
    TARGET_TYPE_TEXT = 80
    toButton = [ ( "text/uri-list", 0, TARGET_TYPE_TEXT ) ]
    TARGET_TYPE_FAV = 81
    toFav = [ ( "FAVORITES", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_FAV ), ( "text/plain", 0, 100 ), ( "text/uri-list", 0, 101 ) ]
    fromFav = [ ( "FAVORITES", Gtk.TargetFlags.SAME_APP, TARGET_TYPE_FAV ) ]

    @print_timing
    def __init__( self, mintMenuWin, toggleButton, de ):
        self.mintMenuWin = mintMenuWin

        self.mainMenus = [ ]

        self.toggleButton = toggleButton
        self.de = de
        
        builder = Gtk.Builder()
        # The Glade file for the plugin
        builder.add_from_file (os.path.join( os.path.dirname( __file__ ), "applications.glade" ))

        # Read GLADE file
        self.wTree = builder.get_object( "mainWindow" )
        self.searchEntry = builder.get_object( "searchEntry" )
        self.searchButton = builder.get_object( "searchButton" )
        self.showAllAppsButton = builder.get_object( "showAllAppsButton" )
        self.showFavoritesButton = builder.get_object( "showFavoritesButton" )
        self.applicationsBox = builder.get_object( "applicationsBox" )
        self.categoriesBox = builder.get_object( "categoriesBox" )
        self.favoritesBox = builder.get_object( "favoritesBox" )
        self.applicationsScrolledWindow = builder.get_object( "applicationsScrolledWindow" )

        #i18n
        builder.get_object("searchLabel").set_text("<span weight='bold'>" + _("Search:") + "</span>")
        builder.get_object("searchLabel").set_use_markup(True)
        builder.get_object("label6").set_text(_("Favorites"))
        builder.get_object("label3").set_text(_("Favorites"))
        builder.get_object("label7").set_text(_("All applications"))
        builder.get_object("label2").set_text(_("Applications"))                
        
        self.mintMenuWin.SetHeadingStyle( [builder.get_object("label6"), builder.get_object("label2")] )

        self.numApps = 0
        # These properties are NECESSARY to maintain consistency

        # Set 'window' property for the plugin (Must be the root widget)
        self.window = builder.get_object( "mainWindow" )

        # Set 'heading' property for plugin
        self.heading = ""#_("Applications")

        # This should be the first item added to the window in glade
        self.content_holder = builder.get_object( "Applications" )

        # Items to get custom colors
        self.itemstocolor = [ builder.get_object( "viewport1" ), builder.get_object( "viewport2" ), builder.get_object( "viewport3" ), builder.get_object( "notebook2" ) ]

        # Unset all timers
        self.filterTimer = None
        self.menuChangedTimer = None
        # Hookup for text input
        self.content_holder.connect( "key-press-event", self.keyPress )

        self.favoritesBox.connect( "drag_data_received", self.ReceiveCallback )
        self.favoritesBox.drag_dest_set( Gtk.DestDefaults.MOTION | Gtk.DestDefaults.HIGHLIGHT | Gtk.DestDefaults.DROP, self.toButton, gtk.gdk.ACTION_COPY )
        self.showFavoritesButton.connect( "drag_data_received", self.ReceiveCallback )
        self.showFavoritesButton.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.toButton, gtk.gdk.ACTION_COPY )

       # self.searchButton.connect( "button_release_event", self.SearchWithButton )

        self.gconfHandlers = []
        # Gconf stuff
        self.gconf = EasyGConf( "/apps/mintMenu/plugins/applications/" )
        self.GetGconfEntries()
        self.gconf.notifyAdd( "icon_size", self.changeIconSize )
        self.gconf.notifyAdd( "favicon_size", self.changeFavIconSize )
        self.gconf.notifyAdd( "height", self.changePluginSize )
        self.gconf.notifyAdd( "width", self.changePluginSize )
        self.gconf.notifyAdd( "categories_mouse_over", self.changeCategoriesMouseOver )
        self.gconf.notifyAdd( "swap_generic_name", self.changeSwapGenericName )
        self.gconf.notifyAdd( "show_category_icons", self.changeShowCategoryIcons )
        self.gconf.notifyAdd( "show_application_comments", self.changeShowApplicationComments )
        self.gconf.notifyAdd( "use_apt", self.switchAPTUsage)
        self.gconf.notifyAdd( "fav_cols", self.changeFavCols )

        self.gconf.bindGconfEntryToVar( "int", "category_hover_delay", self, "categoryhoverdelay" )
        self.gconf.bindGconfEntryToVar( "bool", "do_not_filter", self, "donotfilterapps" )
        self.gconf.bindGconfEntryToVar( "string", "search_command", self, "searchtool" )
        self.gconf.bindGconfEntryToVar( "int", "default_tab", self, "defaultTab" )

        self.currentFavCol = 0
        self.favorites = []

        self.content_holder.set_size_request( self.width, self.height )
        self.categoriesBox.set_size_request( self.width / 3, -1 )
        self.applicationsBox.set_size_request( self.width / 2, -1 )

        self.buildingButtonList = False
        self.stopBuildingButtonList = False

        self.categoryList = []
        self.applicationList = []
        #self.menuFileMonitors = []

        self.rebuildLock = False
        self.activeFilter = (1, "")

        self.adminMenu = None

        for mainitems in [ "mate-applications.menu", "mate-settings.menu" ]:
            mymenu = Menu( mainitems )
            mymenu.tree.add_monitor( self.menuChanged, None )
            #for f in mymenu.directory.Files:
            #       self.menuFileMonitors.append( filemonitor.addMonitor(f, self.onMenuChanged, mymenu.directory.Filename ) )
            #for f in mymenu.directory.AppDirs:
            #       self.menuFileMonitors.append( filemonitor.addMonitor(f, self.onMenuChanged, mymenu.directory.Filename ) )
                        
        self.refresh_apt_cache()        
        self.suggestions = []
        self.current_suggestion = None
        self.get_panel()
        
        builder.get_object("searchButton").connect( "button-release-event", self.searchPopup )        

    def refresh_apt_cache(self):
        if self.useAPT:
            os.system("mkdir -p %s/.linuxmint/mintMenu/" % home)
            os.system("/usr/lib/linuxmint/mintMenu/plugins/get_apt_cache.py > %s/.linuxmint/mintMenu/apt.cache &" % home)            

    def get_panel(self):
        self.panel = None
        self.panel_position = 0
        appletidlist = mateconf.client_get_default().get_list("/apps/panel/general/applet_id_list", "string")
        for applet in appletidlist:
            bonobo_id = mateconf.client_get_default().get_string("/apps/panel/applets/" + applet + "/applet_iid")
            if bonobo_id == "OAFIID:MATE_mintMenu":
                self.panel = mateconf.client_get_default().get_string("/apps/panel/applets/" + applet + "/toplevel_id")
                self.panel_position = mateconf.client_get_default().get_int("/apps/panel/applets/" + applet + "/position") + 1
      
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

        self.gconf.notifyRemoveAll()

        #for mId in self.menuFileMonitors:
        #    filemonitor.removeMonitor( mId )

    def changePluginSize( self, client, connection_id, entry, args ):
        if entry.get_key() == self.gconf.gconfDir+"width":
            self.width = entry.get_value().get_int()
            self.categoriesBox.set_size_request( self.width / 3, -1 )
            self.applicationsBox.set_size_request( self.width / 2, -1 )

        elif entry.get_key() == self.gconf.gconfDir+"height":
            self.heigth = entry.get_value().get_int()
        self.content_holder.set_size_request( self.width, self.height )

    def changeSwapGenericName( self, client, connection_id, entry, args ):
        self.swapgeneric = entry.get_value().get_bool()

        for child in self.favoritesBox:
            if isinstance( child, FavApplicationLauncher):
                child.setSwapGeneric( self.swapgeneric )

    def changeShowCategoryIcons( self, client, connection_id, entry, args ):
        self.showcategoryicons = entry.get_value().get_bool()

        if self.showcategoryicons:
            categoryIconSize = self.iconSize
        else:
            categoryIconSize = 0

        for child in self.categoriesBox:
            child.setIconSize( categoryIconSize )

    def changeIconSize( self, client, connection_id, entry, args ):
        self.iconSize = entry.get_value().get_int()

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

    def changeFavIconSize( self, client, connection_id, entry, args ):
        self.faviconsize = entry.get_value().get_int()

        for child in self.favoritesBox:
            if isinstance( child, FavApplicationLauncher):
                child.setIconSize( self.faviconsize )
                
    def switchAPTUsage( self, client, connection_id, entry, args ):
        self.useAPT = entry.get_value().get_bool()        
        self.refresh_apt_cache()

    def changeShowApplicationComments( self, client, connection_id, entry, args ):
        self.showapplicationcomments = entry.get_value().get_bool()
        for child in self.applicationsBox:
            child.setShowComment( self.showapplicationcomments )

    def changeCategoriesMouseOver( self, client, connection_id, entry, args ):
        self.categories_mouse_over = entry.get_value().get_bool()
        for child in self.categoriesBox:
            if self.categories_mouse_over and not child.mouseOverHandlerIds:
                startId = child.connect( "enter", self.StartFilter, child.filter )
                stopId = child.connect( "leave", self.StopFilter )
                child.mouseOverHandlerIds = ( startId, stopId )
            elif not self.categories_mouse_over and child.mouseOverHandlerIds:
                child.disconnect( child.mouseOverHandlerIds[0] )
                child.disconnect( child.mouseOverHandlerIds[1] )
                child.mouseOverHandlerIds = None

    def changeFavCols(self, client, connection_id, entry, args):
        self.favCols = entry.get_value().get_int()
        for fav in self.favorites:
            self.favoritesBox.remove( fav )
            self.favoritesPositionOnGrid( fav )

    def RegenPlugin( self, *args, **kargs ):            
        self.refresh_apt_cache()
        
        # save old config - this is necessary because the app will notified when it sets the default values and you don't want the to reload itself several times
        oldcategories_mouse_over = self.categories_mouse_over
        oldtotalrecent = self.totalrecent
        oldsticky = self.sticky
        oldminimized = self.minimized
        oldicon = self.icon
        oldhideseparator = self.hideseparator
        oldshowapplicationcomments = self.showapplicationcomments

        self.GetGconfEntries()

        # if the config hasn't changed return
        if oldcategories_mouse_over == self.categories_mouse_over and oldiconsize == self.iconSize and oldfaviconsize == self.faviconsize and oldtotalrecent == self.totalrecent and oldswapgeneric == self.swapgeneric and oldshowcategoryicons == self.showcategoryicons and oldcategoryhoverdelay == self.categoryhoverdelay and oldsticky == self.sticky and oldminimized == self.minimized and oldicon == self.icon and oldhideseparator == self.hideseparator and oldshowapplicationcomments == self.showapplicationcomments:
            return

        self.Todos()
        self.buildFavorites()
        self.RebuildPlugin()

    def GetGconfEntries( self ):

        self.categories_mouse_over = self.gconf.get( "bool", "categories_mouse_over", True )
        self.width = self.gconf.get( "int", "width", 480 )
        self.height = self.gconf.get( "int", "height", 410 )
        self.donotfilterapps = self.gconf.get( "bool", "do_not_filter", False )
        self.iconSize = self.gconf.get( "int", "icon_size", 22 )
        self.faviconsize = self.gconf.get( "int", "favicon_size", 48 )
        self.favCols = self.gconf.get( "int", "fav_cols", 2 )
        self.swapgeneric = self.gconf.get( "bool", "swap_generic_name", False )
        self.showcategoryicons = self.gconf.get( "bool", "show_category_icons", True )
        self.categoryhoverdelay = self.gconf.get( "int", "category_hover_delay", 150 )
        self.showapplicationcomments = self.gconf.get( "bool", "show_application_comments", True )
        self.useAPT = self.gconf.get( "bool", "use_apt", True )

        self.lastActiveTab =  self.gconf.get( "int", "last_active_tab", 0 )
        self.defaultTab = self.gconf.get( "int", "default_tab", -1 )


        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.gconf.get( "bool", "sticky", False )
        self.minimized = self.gconf.get( "bool", "minimized", False )

        # Search tool
        self.searchtool = self.gconf.get( "string", "search_command", "mate-search-tool --named \"%s\" --start" )
        if self.searchtool == "beagle-search SEARCH_STRING":
            self.searchtool = "mate-search-tool --named \"%s\" --start"
            self.gconf.set( "string", "search_command", "mate-search-tool --named \"%s\" --start" )

        # Plugin icon
        self.icon = self.gconf.get( "string", "icon", "applications-accessories" )

        # Hide vertical dotted separator
        self.hideseparator = self.gconf.get( "bool", "hide_separator", False )

    def SetHidden( self, state ):
        if state == True:
            self.gconf.set( "bool", "minimized", True )
        else:
            self.gconf.set( "bool", "minimized", False )

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

    def onHideMenu( self ):
        self.gconf.set( "int", "last_active_tab", self.lastActiveTab )

    def changeTab( self, tabNum ):
        notebook = self.wTree.get_widget( "notebook2" )
        if tabNum == 0:
            notebook.set_current_page( 0 )
        elif tabNum == 1:
            notebook.set_current_page( 1 )

        self.lastActiveTab = tabNum

        self.focusSearchEntry()

    def Todos( self ):

        self.searchEntry.connect( "changed", self.Filter )
        self.searchEntry.connect( "activate", self.Search )
        self.showAllAppsButton.connect( "clicked", lambda widget: self.changeTab( 1 ) )
        self.showFavoritesButton.connect( "clicked", lambda widget: self.changeTab( 0 ) )
        self.buildButtonList()

    def focusSearchEntry( self ):
        # grab_focus() does select all text, as this is an unwanted behaviour we restore the old selection
        sel = self.searchEntry.get_selection_bounds()
        if len(sel) == 0: # no selection
            sel = ( self.searchEntry.get_position(), self.searchEntry.get_position() )
        self.searchEntry.grab_focus()
        self.searchEntry.select_region( sel[0], sel[1] )

    def buildButtonList( self ):         
        if self.buildingButtonList:
            self.stopBuildingButtonList = True
            gobject.timeout_add( 100, self.buildButtonList )
            return

        self.stopBuildingButtonList = False

        self.updateBoxes(False)

    def categoryBtnFocus( self, widget, event, category ):
        self.scrollItemIntoView( widget )
        self.StartFilter( widget, category )

    def StartFilter( self, widget, category ):
        # if there is a timer for a different category running stop it
        if self.filterTimer:
            GObject.source_remove( self.filterTimer )
        self.filterTimer = GObject.timeout_add( self.categoryhoverdelay, self.Filter, widget, category )

    def StopFilter( self, widget ):
        if self.filterTimer:
            GObject.source_remove( self.filterTimer )
            self.filterTimer = None

    def add_search_suggestions(self, text):
        
        text = "<b>%s</b>" % text
        
        suggestionButton = SuggestionButton(Gtk.STOCK_ADD, self.iconSize, "")
        suggestionButton.connect("clicked", self.search_google)
        suggestionButton.set_text(_("Search Google for %s") % text)
        suggestionButton.set_image("/usr/lib/linuxmint/mintMenu/search_engines/google.ico")
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
        separator.set_size_request(-1, 20)       
        separator.type = "separator"        
        self.mintMenuWin.SetPaneColors( [ separator ] )
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
            time.sleep(0.3)
            current_keyword = keyword
            gtk.gdk.threads_enter()
            try:
                current_keyword = self.searchEntry.get_text()
            finally:
                gtk.gdk.threads_leave()
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
                if num_pkg_found >= 3:
                    break
            found_packages.extend(found_in_name)
            found_packages.extend(found_elsewhere)
            gtk.gdk.threads_enter()                                    
            try:
                if keyword == self.searchEntry.get_text() and len(found_packages) > 0:         
                    last_separator = gtk.EventBox()
                    last_separator.add(gtk.HSeparator())
                    last_separator.set_size_request(-1, 20)       
                    last_separator.type = "separator"   
                    self.mintMenuWin.SetPaneColors( [  last_separator ] )     
                    last_separator.show_all()
                    self.applicationsBox.add(last_separator)
                    self.suggestions.append(last_separator)
                    for pkg in found_packages:                        
                        name = pkg.name
                        for word in keywords: 
                            if word != "":             
                                name = name.replace(word, "<b>%s</b>" % word);
                        suggestionButton = SuggestionButton(gtk.STOCK_ADD, self.iconSize, "")
                        suggestionButton.connect("clicked", self.apturl_install, pkg.name)
                        suggestionButton.set_text(_("Install package '%s'") % name)
                        suggestionButton.set_tooltip_text("%s\n\n%s\n\n%s" % (pkg.name, pkg.summary, pkg.description))
                        suggestionButton.set_icon_size(self.iconSize)
                        self.applicationsBox.add(suggestionButton)
                        self.suggestions.append(suggestionButton)
                        #if cache != self.current_results:
                        #    self.current_results.append(pkg)
            finally:        
                gtk.gdk.threads_leave()            
                        
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
                    last_separator = gtk.EventBox()
                    last_separator.add(gtk.HSeparator())
                    last_separator.set_size_request(-1, 20)       
                    last_separator.type = "separator"   
                    self.mintMenuWin.SetPaneColors( [  last_separator ] )     
                    last_separator.show_all()
                    self.applicationsBox.add(last_separator)
                    self.suggestions.append(last_separator)
            
            for pkg in found_packages:
                name = pkg.name
                for word in keywords:
                    if word != "":                    
                        name = name.replace(word, "<b>%s</b>" % word);
                suggestionButton = SuggestionButton(gtk.STOCK_ADD, self.iconSize, "")
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
                self.changeTab( 1 )
                text = widget.get_text()
                showns = False # Are any app shown?
                for i in self.applicationsBox.get_children():
                    shown = i.filterText( text )
                    if (shown):
                        showns = True
                
                if (not showns and os.path.exists("/usr/lib/linuxmint/mintInstall/icon.svg")):
                    if len(text) >= 3:
                        if self.current_suggestion is not None and self.current_suggestion in text:
                            # We're restricting our search... 
                            self.add_search_suggestions(text)
                            #if (len(self.current_results) > 0):
                                #self.add_apt_filter_results_sync(self.current_results, text)
                            #else:
                            thr = threading.Thread(name="mint-menu-apt-filter", group=None, target=self.add_apt_filter_results, args=([text]), kwargs={})
                            thr.start()  
                        else:
                            self.current_results = []  
                            self.add_search_suggestions(text) 
                            thr = threading.Thread(name="mint-menu-apt-filter", group=None, target=self.add_apt_filter_results, args=([text]), kwargs={})
                            thr.start()                                    
                        self.current_suggestion = text
                    else:
                        self.current_suggestion = None
                        self.current_results = []
                else:
                    self.current_suggestion = None
                    self.current_results = []

                for i in self.categoriesBox.get_children():
                    i.set_relief( gtk.RELIEF_NONE )

                allButton = self.categoriesBox.get_children()[0];
                allButton.set_relief( gtk.RELIEF_HALF )
                self.activeFilter = (0, text)
        else:
            #print "CATFILTER"
            self.activeFilter = (1, category)
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
                i.set_relief( gtk.RELIEF_NONE )
            widget.set_relief( gtk.RELIEF_HALF )
            widget.grab_focus()

            self.searchEntry.set_text( "" )
   
        self.applicationsScrolledWindow.get_vadjustment().set_value( 0 )
        
    # Forward all text to the search box
    def keyPress( self, widget, event ):
        if event.string.strip() != "" or event.keyval == gtk.keysyms.BackSpace:
            self.searchEntry.event( event )
            return True

        if event.keyval == gtk.keysyms.Down and self.searchEntry.is_focus():
            self.applicationsBox.get_children()[0].grab_focus()

        return False

    def favPopup( self, widget, ev ):
        if ev.button == 3:
            if ev.y > widget.get_allocation().height / 2:
                insertBefore = False
            else:
                insertBefore = True

            if widget.type == "location":
                mTree = gtk.glade.XML( self.gladefile, "favoritesMenu" )
                #i18n

                desktopMenuItem = gtk.MenuItem(_("Add to desktop"))
                panelMenuItem = gtk.MenuItem(_("Add to panel"))
                separator1 = gtk.SeparatorMenuItem()
                insertSpaceMenuItem = gtk.MenuItem(_("Insert space"))
                insertSeparatorMenuItem = gtk.MenuItem(_("Insert separator"))
                separator2 = gtk.SeparatorMenuItem()
                startupMenuItem = gtk.CheckMenuItem(_("Launch when I log in"))
                separator3 = gtk.SeparatorMenuItem()
                launchMenuItem = gtk.MenuItem(_("Launch"))
                removeFromFavMenuItem = gtk.MenuItem(_("Remove from favorites"))
                separator4 = gtk.SeparatorMenuItem()
                propsMenuItem = gtk.MenuItem(_("Edit properties"))

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
                    mTree.get_widget("favoritesMenu").append(desktopMenuItem)
                    mTree.get_widget("favoritesMenu").append(panelMenuItem)
                    mTree.get_widget("favoritesMenu").append(separator1)
                mTree.get_widget("favoritesMenu").append(insertSpaceMenuItem)
                mTree.get_widget("favoritesMenu").append(insertSeparatorMenuItem)
                mTree.get_widget("favoritesMenu").append(separator2)
                mTree.get_widget("favoritesMenu").append(startupMenuItem)
                mTree.get_widget("favoritesMenu").append(separator3)
                mTree.get_widget("favoritesMenu").append(launchMenuItem)
                mTree.get_widget("favoritesMenu").append(removeFromFavMenuItem)
                mTree.get_widget("favoritesMenu").append(separator4)
                mTree.get_widget("favoritesMenu").append(propsMenuItem)

                mTree.get_widget("favoritesMenu").show_all()

                mTree.get_widget( "favoritesMenu" ).popup( None, None, None, ev.button, ev.time )
                self.mintMenuWin.grab()

            else:
                mTree = gtk.glade.XML( self.gladefile, "favoritesMenuExtra" )
                #i18n
                removeMenuItem = gtk.MenuItem(_("Remove"))
                insertSpaceMenuItem = gtk.MenuItem(_("Insert space"))
                insertSeparatorMenuItem = gtk.MenuItem(_("Insert separator"))
                mTree.get_widget("favoritesMenuExtra").append(removeMenuItem)
                mTree.get_widget("favoritesMenuExtra").append(insertSpaceMenuItem)
                mTree.get_widget("favoritesMenuExtra").append(insertSeparatorMenuItem)
                mTree.get_widget("favoritesMenuExtra").show_all()

                removeMenuItem.connect( "activate", self.onFavoritesRemove, widget )
                insertSpaceMenuItem.connect( "activate", self.onFavoritesInsertSpace, widget, insertBefore )
                insertSeparatorMenuItem.connect( "activate", self.onFavoritesInsertSeparator, widget, insertBefore )
                mTree.get_widget( "favoritesMenuExtra" ).popup( None, None, None, ev.button, ev.time )
                self.mintMenuWin.grab()

    def menuPopup( self, widget, event ):
        if event.button == 3:
            mTree = gtk.glade.XML( self.gladefile, "applicationsMenu" )

            #i18n
            desktopMenuItem = gtk.MenuItem(_("Add to desktop"))
            panelMenuItem = gtk.MenuItem(_("Add to panel"))
            separator1 = gtk.SeparatorMenuItem()
            favoriteMenuItem = gtk.CheckMenuItem(_("Show in my favorites"))
            startupMenuItem = gtk.CheckMenuItem(_("Launch when I log in"))
            separator2 = gtk.SeparatorMenuItem()
            launchMenuItem = gtk.MenuItem(_("Launch"))
            uninstallMenuItem = gtk.MenuItem(_("Uninstall"))
            deleteMenuItem = gtk.MenuItem(_("Delete from menu"))
            separator3 = gtk.SeparatorMenuItem()
            propsMenuItem = gtk.MenuItem(_("Edit properties"))

            if self.de == "mate":
                mTree.get_widget("applicationsMenu").append(desktopMenuItem)
                mTree.get_widget("applicationsMenu").append(panelMenuItem)
                mTree.get_widget("applicationsMenu").append(separator1)

            mTree.get_widget("applicationsMenu").append(favoriteMenuItem)
            mTree.get_widget("applicationsMenu").append(startupMenuItem)

            mTree.get_widget("applicationsMenu").append(separator2)

            mTree.get_widget("applicationsMenu").append(launchMenuItem)
            mTree.get_widget("applicationsMenu").append(uninstallMenuItem)
            if home in widget.desktopFile:
                mTree.get_widget("applicationsMenu").append(deleteMenuItem)
                deleteMenuItem.connect("activate", self.delete_from_menu, widget)

            mTree.get_widget("applicationsMenu").append(separator3)

            mTree.get_widget("applicationsMenu").append(propsMenuItem)

            mTree.get_widget("applicationsMenu").show_all()

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

            mTree.get_widget( "applicationsMenu" ).connect( 'deactivate', self.onMenuPopupDeactivate)
            mTree.get_widget( "applicationsMenu" ).popup( None, None, None, event.button, event.time )
            
    def onMenuPopupDeactivate( self, widget):
        self.mintMenuWin.grab()
    
    def searchPopup( self, widget=None, event=None ):    
        menu = gtk.Menu()   
             
        menuItem = gtk.ImageMenuItem(_("Search Google"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/google.ico')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_google)
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Search Wikipedia"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/wikipedia.ico')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_wikipedia)
        menu.append(menuItem)
        
        menuItem = gtk.SeparatorMenuItem()
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Lookup Dictionary"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/dictionary.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_dictionary)
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Search Computer"))
        img = gtk.Image()
        img.set_from_stock(gtk.STOCK_FIND, self.iconSize)
        menuItem.set_image(img)
        menuItem.connect("activate", self.Search)
        menu.append(menuItem)
        
        menuItem = gtk.SeparatorMenuItem()
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Find Software"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/software.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_software)
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Find Tutorials"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/tutorials.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_tutorials)
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Find Hardware"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/hardware.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_hardware)
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Find Ideas"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/ideas.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_ideas)
        menu.append(menuItem)
        
        menuItem = gtk.ImageMenuItem(_("Find Users"))
        img = gtk.Image()
        img.set_from_file('/usr/lib/linuxmint/mintMenu/search_engines/users.png')
        menuItem.set_image(img)
        menuItem.connect("activate", self.search_mint_users)
        menu.append(menuItem)
        
        menu.show_all()
        #menu.popup( None, None, self.pos_func, 3, 0)
        menu.popup( None, None, None, 3, 0)
        #menu.attach_to_widget(self.searchButton, None)
        #menu.reposition()
        #menu.reposition()
        self.mintMenuWin.grab()
        self.focusSearchEntry()
        
    def pos_func(self, menu=None):
        rect = self.searchButton.get_allocation()
        x = rect.x + rect.width
        y = rect.y + rect.height
        return (x, y, False)
        
    def search_google(self, widget):
        text = self.searchEntry.get_text()
        text = text.replace(" ", "+")
        os.system("xdg-open \"http://www.google.com/cse?cx=002683415331144861350%3Atsq8didf9x0&ie=utf-8&sa=Search&q=" + text + "\" &")     
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
        try:
            # Determine where the Desktop folder is (could be localized)
            import sys, commands
            sys.path.append('/usr/lib/linuxmint/common')
            from configobj import ConfigObj
            config = ConfigObj(home + "/.config/user-dirs.dirs")
            desktopDir = home + "/Desktop"
            tmpdesktopDir = config['XDG_DESKTOP_DIR']
            tmpdesktopDir = commands.getoutput("echo " + tmpdesktopDir)
            if os.path.exists(tmpdesktopDir):
                desktopDir = tmpdesktopDir
            # Copy the desktop file to the desktop
            os.system("cp \"%s\" \"%s/\"" % (desktopEntry.desktopFile, desktopDir))
            os.system("chmod a+rx %s/*.desktop" % (desktopDir))
        except Exception, detail:
            print detail

    def add_to_panel(self, widget, desktopEntry):
        import random
        object_name = "mintmenu_"+''.join([random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for x in xrange(8)])
        new_directory = home + "/.mate2/panel2.d/default/launchers/"
        os.system("mkdir -p " + new_directory)
        new_file = new_directory + object_name

        # Copy the desktop file to the panels directory
        os.system("cp \"%s\" \"%s\"" % (desktopEntry.desktopFile, new_file))
        os.system("chmod a+rx %s" % (new_file))

        # Add to Gnome/GConf
        object_dir = "/apps/panel/objects/"
        object_client = mateconf.client_get_default()

        object_client.set_string(object_dir + object_name +"/"+ "menu_path", "applications:/")
        object_client.set_bool(object_dir + object_name +"/"+ "locked", False)
        object_client.set_int(object_dir + object_name +"/"+ "position", self.panel_position)
        object_client.set_string(object_dir + object_name +"/"+ "object_type", "launcher-object")
        object_client.set_bool(object_dir + object_name +"/"+ "panel_right_stick", False)
        object_client.set_bool(object_dir + object_name +"/"+ "use_menu_path", False)
        object_client.set_string(object_dir + object_name +"/"+ "launcher_location", new_file)
        object_client.set_string(object_dir + object_name +"/"+ "custom_icon", "")
        object_client.set_string(object_dir + object_name +"/"+ "tooltip", "")
        object_client.set_string(object_dir + object_name +"/"+ "action_type", "lock")
        object_client.set_bool(object_dir + object_name +"/"+ "use_custom_icon", False)
        object_client.set_string(object_dir + object_name +"/"+ "attached_toplevel_id", "")
        object_client.set_string(object_dir + object_name +"/"+ "bonobo_iid", "")
        object_client.set_string(object_dir + object_name +"/"+ "toplevel_id", self.panel)

        launchers_list = object_client.get_list("/apps/panel/general/object_id_list", "string")
        launchers_list.append(object_name)
        object_client.set_list("/apps/panel/general/object_id_list", mateconf.VALUE_STRING, launchers_list)

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

            path += "applications"

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
        gtk.gdk.flush()

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
        while not isinstance( viewport, gtk.Viewport ):
            if not viewport.parent:
                return
            viewport = viewport.parent
        aloc = widget.get_allocation()
        viewport.get_vadjustment().clamp_page(aloc.y, aloc.y + aloc.height)

    def favoritesBuildSpace( self ):
        space = gtk.EventBox()
        space.set_size_request( -1, 20 )
        space.connect( "button_release_event", self.favPopup )
        space.type = "space"

        self.mintMenuWin.SetPaneColors( [ space ] )
        space.show()

        return space

    def favoritesBuildSeparator( self ):
        separator = gtk.HSeparator()
        #separator.add( gtk.HSeparator() )
        separator.set_size_request( -1, 20 )
        separator.connect( "button_release_event", self.favPopup )
        separator.type = "separator"

        self.mintMenuWin.SetPaneColors( [ separator ] )
        separator.show_all()
        return separator

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
                favButton.connect( "button_release_event", self.favPopup )
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
            from user import home
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
                    favButton.connect( "drag_data_received", self.onFavButtonDragReorder )
                    favButton.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.fromFav, gtk.gdk.ACTION_COPY )
                    favButton.connect( "drag_data_get", self.onFavButtonDragReorderGet )
                    favButton.drag_source_set( gtk.gdk.BUTTON1_MASK, self.toFav, gtk.gdk.ACTION_COPY )
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

            favButton.connect( "drag_data_received", self.onFavButtonDragReorder )
            favButton.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.toFav, gtk.gdk.ACTION_COPY )
            favButton.connect( "drag_data_get", self.onFavButtonDragReorderGet )
            favButton.drag_source_set( gtk.gdk.BUTTON1_MASK, self.toFav, gtk.gdk.ACTION_COPY )

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
            msgDlg = gtk.MessageDialog( None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, _("Couldn't save favorites. Check if you have write access to ~/.linuxmint/mintMenu")+"\n(" + e.__str__() + ")" )
            msgDlg.run();
            msgDlg.destroy();

    def isLocationInFavorites( self, location ):
        for fav in self.favorites:
            if fav.type == "location" and fav.desktopFile == location:
                return True

        return False

    def onFavButtonDragReorderGet( self, widget, context, selection, targetType, eventTime ):
        if targetType == self.TARGET_TYPE_FAV:
            selection.set( selection.target, 8, str(widget.position) )

    def onFavButtonDragReorder( self, widget, context, x, y, selection, targetType, time  ):
        if targetType == self.TARGET_TYPE_FAV:
            self.favoritesReorder( int(selection.data), widget.position )

    def menuChanged( self, x, y ):
        # wait some miliseconds because there a multiple events send at the same time and we don't want to rebuild the menu for each
        if self.menuChangedTimer:
            gobject.source_remove( self.menuChangedTimer )

        self.menuChangedTimer = gobject.timeout_add( 100, self.updateBoxes, True )

    def updateBoxes( self, menu_has_changed ):        
        # FIXME: This is really bad!
        if self.rebuildLock:            
            return

        self.rebuildLock = True

        self.menuChangedTimer = None
        
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

            key = 0
            for item in self.categoryList:
                found = False
                for item2 in newCategoryList:
                    if item["name"] == item2["name"] and item["icon"] == item2["icon"] and item["tooltip"] == item2["tooltip"] and item["index"] == item2["index"]:
                        found = True
                        break
                if not found:
                    removedCategories.append( key )
                else:
                    key += 1

        if self.showcategoryicons == True:
            categoryIconSize = self.iconSize
        else:
            categoryIconSize = 0

        for key in removedCategories:
            self.categoryList[key]["button"].destroy()
            del self.categoryList[key]

        if addedCategories:
            sortedCategoryList = []
            for item in self.categoryList:
                self.categoriesBox.remove( item["button"] )
                sortedCategoryList.append( ( str(item["index"]) + item["name"], item["button"] ) )

            # Create new category buttons and add the to the list
            for item in addedCategories:
                item["button"] = CategoryButton( item["icon"], categoryIconSize, [ item["name"] ], item["filter"] )
                self.mintMenuWin.setTooltip( item["button"], item["tooltip"] )

                if self.categories_mouse_over:
                    startId = item["button"].connect( "enter", self.StartFilter, item["filter"] )
                    stopId = item["button"].connect( "leave", self.StopFilter )
                    item["button"].mouseOverHandlerIds = ( startId, stopId )
                else:
                    item["button"].mouseOverHandlerIds = None

                item["button"].connect( "clicked", self.Filter, item["filter"] )
                item["button"].connect( "focus-in-event", self.categoryBtnFocus, item["filter"] )
                item["button"].show()

                self.categoryList.append( item )
                sortedCategoryList.append( ( str(item["index"]) + item["name"], item["button"] ) )
            sortedCategoryList.sort()

            for item in sortedCategoryList:
                self.categoriesBox.pack_start( item[1], False, False, 0 )


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
            for item in sortedApplicationList:
                self.applicationsBox.pack_start( item[1], False, False, 0 )
                      
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
