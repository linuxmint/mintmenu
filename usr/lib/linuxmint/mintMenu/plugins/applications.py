#!/usr/bin/env python

import gtk
import gtk.glade
import gobject
import os
import gconf
import fnmatch
import time
import string
import gettext
import gnomevfs
import threading
import commands

from easybuttons import *
from execute import Execute
from easygconf import EasyGConf
from easyfiles import *

from filemonitor import monitor as filemonitor

import xdg.Menu

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")

# Evil patching
def xdgParsePatched(filename=None):
	# conver to absolute path
	if filename and not os.path.isabs(filename):
		filename = xdg.Menu.__getFileName(filename)

	# use default if no filename given
	if not filename:
		filename = xdg.Menu.__getFileName("applications.menu")

	if not filename:
		raise xdg.Menu.ParsingError(_("File not found"), "/etc/xdg/menus/applications.menu")

	# check if it is a .menu file
	if not os.path.splitext(filename)[1] == ".menu":
		raise xdg.Menu.ParsingError(_("Not a .menu file"), filename)

	# create xml parser
	try:
		doc = xdg.Menu.xml.dom.minidom.parse(filename)
	except xdg.Menu.xml.parsers.expat.ExpatError:
		raise xdg.Menu.ParsingError(_("Not a valid .menu file"), filename)

	# parse menufile
	xdg.Menu.tmp["Root"] = ""
	xdg.Menu.tmp["mergeFiles"] = []
	xdg.Menu.tmp["DirectoryDirs"] = []
	xdg.Menu.tmp["cache"] = xdg.Menu.MenuEntryCache()

	xdg.Menu.__parse(doc, filename, xdg.Menu.tmp["Root"])
	xdg.Menu.__parsemove(xdg.Menu.tmp["Root"])
	xdg.Menu.__postparse(xdg.Menu.tmp["Root"])

	xdg.Menu.tmp["Root"].Doc = doc
	xdg.Menu.tmp["Root"].Filename = filename

	# generate the menu
	xdg.Menu.__genmenuNotOnlyAllocated(xdg.Menu.tmp["Root"])
	xdg.Menu.__genmenuOnlyAllocated(xdg.Menu.tmp["Root"])

	# and finally sort
	xdg.Menu.sort(xdg.Menu.tmp["Root"])
	xdg.Menu.tmp["Root"].Files = xdg.Menu.tmp["mergeFiles"] + [ xdg.Menu.tmp["Root"].Filename ]
	return xdg.Menu.tmp["Root"]

xdg.Menu.parse = xdgParsePatched

class Menu:
	def __init__( self, menu ):
		if isinstance( menu , xdg.Menu.Menu):
			self.directory = menu
		else:
			self.directory = xdg.Menu.parse( menu )

	def getMenus( self, parent = None ):
		if not parent:
			parent = self.directory
		if not parent:
			return

		for menu in parent.getEntries():
			if isinstance( menu, xdg.Menu.Menu ):
				yield menu

	def getItems( self, recursive = False ):
		for item in self.directory.getEntries():
			if isinstance( item, xdg.Menu.MenuEntry ):
				yield item
			elif isinstance( item, xdg.Menu.Menu ):
				for subitem in Menu( item ).getItems( True ):
					yield subitem


class SuggestionButton ( gtk.Button ):

	def __init__( self, iconName, iconSize, label ):
		gtk.Button.__init__( self )
		iconSize = self.get_icon_size(iconSize)
		self.iconName = iconName
		self.set_relief( gtk.RELIEF_NONE )
		self.set_size_request( 10, 10 )
		Align1 = gtk.Alignment( 0, 0.5, 1.0, 0 )
		HBox1 = gtk.HBox()
		labelBox = gtk.VBox( False, 2 )
		self.image = gtk.Image()		
		self.image.set_from_stock( self.iconName, iconSize )
		self.image.show()
		HBox1.pack_start( self.image, False, False, 5 )
		self.label = gtk.Label()
		self.label.set_ellipsize( pango.ELLIPSIZE_END )
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

	def get_icon_size (self, iconSize):
		if isinstance(iconSize, int):
			if iconSize >= 4:
				iconSize = gtk.ICON_SIZE_DIALOG
			elif iconSize == 3:
				iconSize = gtk.ICON_SIZE_DND
			elif iconSize == 2:
				iconSize = gtk.ICON_SIZE_BUTTON
			elif iconSize == 1:
				iconSize = gtk.ICON_SIZE_MENU
		return iconSize

	def set_text( self, text):
		self.label.set_text(text)

	def set_icon_size (self, size):
		size = self.get_icon_size(size)
		self.image.set_from_stock( self.iconName, size )	

class pluginclass( object ):
	TARGET_TYPE_TEXT = 80
	toButton = [ ( "text/uri-list", 0, TARGET_TYPE_TEXT ) ]
	TARGET_TYPE_FAV = 81
	toFav = [ ( "FAVORITES", gtk.TARGET_SAME_APP, TARGET_TYPE_FAV ), ( "text/plain", 0, 100 ), ( "text/uri-list", 0, 101 ) ]
	fromFav = [ ( "FAVORITES", gtk.TARGET_SAME_APP, TARGET_TYPE_FAV ) ]

	def __init__( self, mintMenuWin, toggleButton ):

		self.mintMenuWin = mintMenuWin
		
		self.mainMenus = [ ]

		self.toggleButton = toggleButton	
		# The Glade file for the plugin
		self.gladefile = os.path.join( os.path.dirname( __file__ ), "applications.glade" )

		# Read GLADE file
		self.wTree = gtk.glade.XML( self.gladefile, "mainWindow" )
		self.searchEntry = self.wTree.get_widget( "searchEntry" )
		self.searchButton = self.wTree.get_widget( "searchButton" )
		self.showAllAppsButton = self.wTree.get_widget( "showAllAppsButton" )
		self.showFavoritesButton = self.wTree.get_widget( "showFavoritesButton" )
		self.applicationsBox = self.wTree.get_widget( "applicationsBox" )
		self.categoriesBox = self.wTree.get_widget( "categoriesBox" )
		self.favoritesBox = self.wTree.get_widget( "favoritesBox" )
		self.applicationsScrolledWindow = self.wTree.get_widget( "applicationsScrolledWindow" )		

		#i18n
		self.wTree.get_widget("searchLabel").set_text("<span weight='bold'>" + _("Filter:") + "</span>")
		self.wTree.get_widget("searchLabel").set_use_markup(True)
		self.wTree.get_widget("label6").set_text("<span weight='bold'>" + _("Favorites") + "</span>")
		self.wTree.get_widget("label6").set_use_markup(True)
		self.wTree.get_widget("label7").set_text(_("All applications"))
		self.wTree.get_widget("label2").set_text("<span weight='bold'>" + _("All applications") + "</span>")
		self.wTree.get_widget("label2").set_use_markup(True)
		self.wTree.get_widget("label3").set_text(_("Favorites"))

		self.numApps = 0
		# These properties are NECESSARY to maintain consistency

		# Set 'window' property for the plugin (Must be the root widget)
		self.window = self.wTree.get_widget( "mainWindow" )

		# Set 'heading' property for plugin
		self.heading = _("Applications")

		# This should be the first item added to the window in glade
		self.content_holder = self.wTree.get_widget( "Applications" )

		# Items to get custom colors
		self.itemstocolor = [ self.wTree.get_widget( "viewport1" ), self.wTree.get_widget( "viewport2" ), self.wTree.get_widget( "viewport3" ), self.wTree.get_widget( "notebook2" ) ]

		# Unset all timers
		self.filterTimer = None
		self.menuChangedTimer = None
		# Hookup for text input
		self.content_holder.connect( "key-press-event", self.keyPress )

		self.favoritesBox.connect( "drag_data_received", self.ReceiveCallback )
		self.favoritesBox.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.toButton, gtk.gdk.ACTION_COPY )
		self.showFavoritesButton.connect( "drag_data_received", self.ReceiveCallback )
		self.showFavoritesButton.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.toButton, gtk.gdk.ACTION_COPY )

		self.searchButton.connect( "button_release_event", self.SearchWithButton )

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
		self.menuFileMonitors = []
		
		self.rebuildLock = False
		self.activeFilter = (1, "")

		self.adminMenu = None

		for mainitems in [ "applications.menu", "settings.menu" ]:
			mymenu = Menu( mainitems )
			for f in mymenu.directory.Files:
				self.menuFileMonitors.append( filemonitor.addMonitor(f, self.onMenuChanged, mymenu.directory.Filename ) )
			for f in mymenu.directory.AppDirs:
				self.menuFileMonitors.append( filemonitor.addMonitor(f, self.onMenuChanged, mymenu.directory.Filename ) )

		sizeIcon = 0
		if isinstance(self.iconSize, int):
			if self.iconSize >= 4:
				sizeIcon = gtk.ICON_SIZE_DIALOG
			elif self.iconSize == 3:
				sizeIcon = gtk.ICON_SIZE_DND
			elif self.iconSize == 2:
				sizeIcon = gtk.ICON_SIZE_BUTTON
			elif self.iconSize == 1:
				sizeIcon = gtk.ICON_SIZE_MENU
			elif self.iconSize <= 0:
				return ( 0, 0 )

		#sizeIcon = gtk.icon_size_lookup( sizeIcon )
		
		self.suggestSearchAppButton = SuggestionButton(gtk.STOCK_FIND, self.iconSize, "")		
		self.suggestSearchButton = SuggestionButton(gtk.STOCK_FIND, self.iconSize, "")
		self.suggestShowButton = SuggestionButton(gtk.STOCK_INFO, self.iconSize, "")
		self.suggestInstallButton = SuggestionButton(gtk.STOCK_ADD, self.iconSize, "")

		self.suggestSearchAppButton.connect("clicked", self.search_mint)			
		self.suggestSearchButton.connect("clicked", self.search_apt)	
		self.suggestShowButton.connect("clicked", self.show_apt)	
		self.suggestInstallButton.connect("clicked", self.install_apt)	

	def search_mint(self, widget):
		os.system("/usr/bin/mint-search-portal " + self.suggestion + " &")
		self.mintMenuWin.hide()		

	def search_apt(self, widget):
		os.system("/usr/bin/mint-search-apt " + self.suggestion + " &")
		self.mintMenuWin.hide()

	def show_apt(self, widget):
		os.system("/usr/bin/mint-show-apt " + self.suggestion + " &")
		self.mintMenuWin.hide()

	def install_apt(self, widget):
		os.system("/usr/bin/mint-make-cmd " + self.suggestion + " &")
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

		for mId in self.menuFileMonitors:
			filemonitor.removeMonitor( mId )
	
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

		self.suggestSearchAppButton.set_icon_size( self.iconSize )
		self.suggestSearchButton.set_icon_size( self.iconSize )
		self.suggestShowButton.set_icon_size( self.iconSize )
		self.suggestInstallButton.set_icon_size( self.iconSize )
		
	
	def changeFavIconSize( self, client, connection_id, entry, args ):
		self.faviconsize = entry.get_value().get_int()
		
		for child in self.favoritesBox:
			if isinstance( child, FavApplicationLauncher):
				child.setIconSize( self.faviconsize )
				
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
			elif self.categories_mouse_over and child.mouseOverHandlerIds:
				child.disconnect( child.mouseOverHandlerIds[0] )
				child.disconnect( child.mouseOverHandlerIds[1] )
				child.mouseOverHandlerIds = None
				
	def changeFavCols(self, client, connection_id, entry, args):
		self.favCols = entry.get_value().get_int()
		for fav in self.favorites:
			self.favoritesBox.remove( fav )
			self.favoritesPositionOnGrid( fav )

	def RegenPlugin( self, *args, **kargs ):
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
		self.iconSize = self.gconf.get( "int", "icon_size", 2 )
		self.faviconsize = self.gconf.get( "int", "favicon_size", 3 )
		self.favCols = self.gconf.get( "int", "fav_cols", 2 )
		self.swapgeneric = self.gconf.get( "bool", "swap_generic_name", False )
		self.showcategoryicons = self.gconf.get( "bool", "show_category_icons", True )
		self.categoryhoverdelay = self.gconf.get( "int", "category_hover_delay", 150 )
		self.showapplicationcomments = self.gconf.get( "bool", "show_application_comments", True )
		
		self.lastActiveTab =  self.gconf.get( "int", "last_active_tab", 0 )
		self.defaultTab = self.gconf.get( "int", "default_tab", -1 )


		# Allow plugin to be minimized to the left plugin pane
		self.sticky = self.gconf.get( "bool", "sticky", False )
		self.minimized = self.gconf.get( "bool", "minimized", False )

		# Search tool
		self.searchtool = self.gconf.get( "string", "search_command", "gnome-search-tool --named \"%s\" --start" )
		if self.searchtool == "beagle-search SEARCH_STRING":
			self.searchtool = "gnome-search-tool --named \"%s\" --start"
			self.gconf.set( "string", "search_command", "gnome-search-tool --named \"%s\" --start" )

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

		gobject.idle_add( self.updateBoxes )

	def categoryBtnFocus( self, widget, event, category ):
		self.scrollItemIntoView( widget )
		self.StartFilter( widget, category )

	def StartFilter( self, widget, category ):
		# if there is a timer for a different category running stop it
		if self.filterTimer:
			gobject.source_remove( self.filterTimer )
		self.filterTimer = gobject.timeout_add( self.categoryhoverdelay, self.Filter, widget, category )

	def StopFilter( self, widget ):
		if self.filterTimer:
			gobject.source_remove( self.filterTimer )
			self.filterTimer = None

	def Filter( self, widget, category = None ):
		self.filterTimer = None

		start = time.time()
		#print "FILTER"		
		self.applicationsBox.remove(self.suggestSearchAppButton)
		self.applicationsBox.remove(self.suggestSearchButton)
		self.applicationsBox.remove(self.suggestShowButton)
		self.applicationsBox.remove(self.suggestInstallButton)

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
					self.suggestion = text

					self.applicationsBox.add(self.suggestSearchAppButton)					
					self.suggestSearchAppButton.set_text(_("Search portal for '%s'") % text)
					self.suggestSearchAppButton.set_tooltip_text(_("Search portal for '%s'") % text)					

					self.applicationsBox.add(self.suggestSearchButton)
					self.suggestSearchButton.set_text(_("Search repositories for '%s'") % text)
					self.suggestSearchButton.set_tooltip_text(_("Search repositories for '%s'") % text)

					self.applicationsBox.add(self.suggestShowButton)					
					self.suggestShowButton.set_text(_("Show package '%s'") % text)
					self.suggestShowButton.set_tooltip_text(_("Show package '%s'") % text)

					self.applicationsBox.add(self.suggestInstallButton)
					self.suggestInstallButton.set_text(_("Install package '%s'") % text)
					self.suggestInstallButton.set_tooltip_text(_("Install package '%s'") % text)

				for i in self.categoriesBox.get_children():
					i.set_relief( gtk.RELIEF_NONE )
					
				allButton = self.categoriesBox.get_children()[0];
				allButton.set_relief( gtk.RELIEF_HALF )
				self.activeFilter = (0, text)
		else:
			#print "CATFILTER"
			self.activeFilter = (1, category)
			if category == "":
				for i in self.applicationsBox.get_children():
					i.show_all()
			else:
				for i in self.applicationsBox.get_children():
					i.filterCategory( category )
			for i in self.applicationsBox.get_children():
				i.filterCategory( category )

			for i in self.categoriesBox.get_children():
				i.set_relief( gtk.RELIEF_NONE )
			widget.set_relief( gtk.RELIEF_HALF )
			widget.grab_focus()

			self.searchEntry.set_text( "" )

		self.applicationsScrolledWindow.get_vadjustment().set_value( 0 )
		#print u"Filtertime: ", (time.time() - start), "s"	

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
				launchMenuItem = gtk.MenuItem(_("Launch"))
				removeFromFavMenuItem = gtk.MenuItem(_("Remove from favorites"))
				startupMenuItem = gtk.CheckMenuItem(_("Launch when I log in"))
				separator = gtk.SeparatorMenuItem()
				insertSpaceMenuItem = gtk.MenuItem(_("Insert space"))
				insertSeparatorMenuItem = gtk.MenuItem(_("Insert separator"))
				

				launchMenuItem.connect( "activate", self.onLaunchApp, widget)
				removeFromFavMenuItem.connect( "activate", self.onFavoritesRemove, widget )
				insertSpaceMenuItem.connect( "activate", self.onFavoritesInsertSpace, widget, insertBefore )
				insertSeparatorMenuItem.connect( "activate", self.onFavoritesInsertSeparator, widget, insertBefore )

				mTree.get_widget("favoritesMenu").append(launchMenuItem)
				mTree.get_widget("favoritesMenu").append(removeFromFavMenuItem)
				mTree.get_widget("favoritesMenu").append(startupMenuItem)
				mTree.get_widget("favoritesMenu").append(separator)				
				mTree.get_widget("favoritesMenu").append(insertSpaceMenuItem)
				mTree.get_widget("favoritesMenu").append(insertSeparatorMenuItem)
				mTree.get_widget("favoritesMenu").show_all()

				mTree.get_widget( "favoritesMenu" ).popup( None, None, None, ev.button, ev.time )

				if widget.isInStartup():
					startupMenuItem.set_active( True )
					startupMenuItem.connect( "toggled", self.onRemoveFromStartup, widget )
				else:
					startupMenuItem.set_active( False )
					startupMenuItem.connect( "toggled", self.onAddToStartup, widget )
							
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

	def menuPopup( self, widget, event ):
		if event.button == 3:
			mTree = gtk.glade.XML( self.gladefile, "applicationsMenu" )

			#i18n
			launchMenuItem = gtk.MenuItem(_("Launch"))
			favoriteMenuItem = gtk.CheckMenuItem(_("Show in my favorites"))
			startupMenuItem = gtk.CheckMenuItem(_("Launch when I log in"))
			separator = gtk.SeparatorMenuItem()			
			uninstallMenuItem = gtk.MenuItem(_("Uninstall"))
			mTree.get_widget("applicationsMenu").append(launchMenuItem)
			mTree.get_widget("applicationsMenu").append(favoriteMenuItem)
			mTree.get_widget("applicationsMenu").append(startupMenuItem)
			mTree.get_widget("applicationsMenu").append(separator)
			mTree.get_widget("applicationsMenu").append(uninstallMenuItem)
			mTree.get_widget("applicationsMenu").show_all()

			launchMenuItem.connect( "activate", self.onLaunchApp, widget )
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
			
			mTree.get_widget( "applicationsMenu" ).popup( None, None, None, event.button, event.time )

	def onLaunchApp( self, menu, widget ):
		widget.execute()
		self.mintMenuWin.hide()

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
			self.searchEntry.set_text( "" )
			self.mintMenuWin.hide()
			fullstring = self.searchtool.replace( "%s", text )
			newstring = fullstring.split()
			Execute( newstring )

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
		separator = gtk.EventBox()
		separator.add( gtk.HSeparator() )
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
				ButtonIcon = "gnome-fs-directory"
			
			if location.startswith( "smb" ) or location.startswith( "ssh" ) or location.startswith( "network" ):
				ButtonIcon = "gnome-fs-network"
			
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
					favButton.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.fromFav, gtk.gdk.ACTION_MOVE )
					favButton.connect( "drag_data_get", self.onFavButtonDragReorderGet )
					favButton.drag_source_set( gtk.gdk.BUTTON1_MASK, self.toFav, gtk.gdk.ACTION_MOVE )
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
			favButton.drag_dest_set( gtk.DEST_DEFAULT_MOTION | gtk.DEST_DEFAULT_HIGHLIGHT | gtk.DEST_DEFAULT_DROP, self.toFav, gtk.gdk.ACTION_MOVE )
			favButton.connect( "drag_data_get", self.onFavButtonDragReorderGet )
			favButton.drag_source_set( gtk.gdk.BUTTON1_MASK, self.toFav, gtk.gdk.ACTION_MOVE )
			
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

	def onMenuChanged( self, menu ):
		# wait some miliseconds because there a multiple events send at the same time and we don't want to rebuild the menu for each
		if self.menuChangedTimer:
			gobject.source_remove( self.menuChangedTimer )

		self.menuChangedTimer = gobject.timeout_add( 100, self.updateBoxes )

	def updateBoxes( self ):
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
			
				item["button"].connect( "clicked", self.Filter, item["filter"] )	
				item["button"].connect( "focus-in-event", self.categoryBtnFocus, item["filter"] )
				item["button"].show()

				self.categoryList.append( item )
				sortedCategoryList.append( ( str(item["index"]) + item["name"], item["button"] ) )

			sortedCategoryList.sort()

			for item in sortedCategoryList:
				self.categoriesBox.pack_start( item[1], False )


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
					if item["entry"].filename == item2["entry"].filename:
						found = True
						break
				if not found:
					addedApplications.append(item)

			key = 0
			for item in self.applicationList:
				found = False
				for item2 in newApplicationList:
					if item["entry"].filename == item2["entry"].filename:
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
				item["button"] = MenuApplicationLauncher( item["entry"], self.iconSize, item["category"], self.showapplicationcomments )
				if item["button"].appExec:
					self.mintMenuWin.setTooltip( item["button"], item["button"].getTooltip() )
					item["button"].connect( "button-release-event", self.menuPopup )
					item["button"].connect( "focus-in-event", self.scrollItemIntoView )
					item["button"].connect( "clicked", lambda w: self.mintMenuWin.hide() )
					if self.activeFilter[0] == 0:
						item["button"].filterText( self.activeFilter[1] )
					else:
						item["button"].filterCategory( self.activeFilter[1] )
					sortedApplicationList.append( ( item["button"].appName.upper(), item["button"] ) )
					self.applicationList.append( item )
				else:
					item["button"].destroy()


			sortedApplicationList.sort()
			for item in sortedApplicationList:
				self.applicationsBox.pack_start( item[1], False )
		self.rebuildLock = False


	# Reload the menufiles from the filesystem
	def loadMenuFiles( self ):
		self.menuFiles = []
		for mainitems in [ "applications.menu", "settings.menu" ]:
			self.menuFiles.append( Menu( mainitems) )

	# Build a list of all categories in the menu ( [ { "name", "icon", tooltip" } ]
	def buildCategoryList( self ):
		newCategoryList = [ { "name": _("All"), "icon": self.mintMenuWin.icon, "tooltip": _("Show all applications"), "filter":"", "index": 0 } ]

		num = 1
		for menu in self.menuFiles:
			for child in menu.getMenus():
				icon =  str(child.getIcon())
				if (icon == "preferences-system"):					
					self.adminMenu = child.getName()
				if (icon != "applications-system" and icon != "applications-other"):				
					newCategoryList.append( { "name": child.getName(), "icon": child.getIcon(), "tooltip": child.getName(), "filter": child.getName(), "index": num } )
			num += 1

		return newCategoryList

	# Build a list containing the DesktopEntry object and the category of each application in the menu
	def buildApplicationList( self ):

		newApplicationsList = []

		for menu in self.menuFiles:
			for child in menu.getMenus():
				for application in Menu(child).getItems( True ):
					if isinstance( application, xdg.Menu.MenuEntry ):
						catName = child.getName()						
						icon = str(child.getIcon())						
						if (icon == "applications-system" or icon == "applications-other"):
							catName = self.adminMenu
						newApplicationsList.append( { "entry": application.DesktopEntry, "category": catName } )

		return newApplicationsList
		
