#!/usr/bin/env python

import gtk
import gtk.glade
import os
import gconf
import gnomevfs
import string
import gettext
import commands
import time

from easybuttons import *
from execute import Execute
from easygconf import EasyGConf
from user import home

# i18n
gettext.install("messages", "/usr/lib/linuxmint/mintMenu/locale")

class pluginclass( object ):
	
	def __init__( self, mintMenuWin, toggleButton ):
		
		self.mintMenuWin = mintMenuWin
		self.toggleButton = toggleButton
		
		# Read GLADE file
		gladefile = os.path.join( os.path.dirname( __file__ ), "places.glade" )
		wTree 	= gtk.glade.XML( gladefile, "mainWindow" )
		self.placesBtnHolder	= wTree.get_widget( "places_button_holder" )
		self.editableBtnHolder 	= wTree.get_widget( "editable_button_holder" )
		self.scrolledWindow=wTree.get_widget("scrolledwindow2")
		# These properties are NECESSARY to maintain consistency

		# Set 'window' property for the plugin (Must be the root widget)
		self.window = wTree.get_widget( "mainWindow" )

		# Set 'heading' property for plugin
		self.heading = _("Places")

		# This should be the first item added to the window in glade
		self.content_holder = wTree.get_widget( "Places" )

		# Items to get custom colors
		self.itemstocolor = [ wTree.get_widget( "viewport2" ) ]

		# Gconf stuff
		self.gconf = EasyGConf( "/apps/mintMenu/plugins/places/" )

		self.gconf.notifyAdd( "icon_size", self.RegenPlugin )
		self.gconf.notifyAdd( "show_computer", self.RegenPlugin )
		self.gconf.notifyAdd( "show_desktop", self.RegenPlugin )
		self.gconf.notifyAdd( "show_home_folder", self.RegenPlugin )
		self.gconf.notifyAdd( "show_trash", self.RegenPlugin )
		self.gconf.notifyAdd( "custom_names", self.RegenPlugin )
		self.gconf.notifyAdd( "allowScrollbar", self.RegenPlugin )
		self.gconf.notifyAdd( "height", self.changePluginSize )
		self.gconf.notifyAdd( "width", self.changePluginSize )		
		self.gconf.bindGconfEntryToVar( "bool", "sticky", self, "sticky" )

		self.GetGconfEntries()
		
		self.content_holder.set_size_request( self.width, self.height )

	def wake (self) :
		if ( self.showtrash == True ):
			self.refreshTrash()

	def destroy( self ):
		self.gconf.notifyRemoveAll()		

	def changePluginSize( self, client, connection_id, entry, args ):
		self.allowScrollbar = self.gconf.get( "bool", "allowScrollbar", False)
		if entry.get_key() == self.gconf.gconfDir+"width":
			self.width = entry.get_value().get_int()
		elif entry.get_key() == self.gconf.gconfDir+"height":
			if (self.allowScrollbar == False):
				self.height = -1
				self.scrolledWindow.set_policy( gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER )
			else:
				self.scrolledWindow.set_policy( gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC )
				self.height = entry.get_value().get_int()

		self.content_holder.set_size_request( self.width, self.height )
		


	def RegenPlugin( self, *args, **kargs ):
		self.GetGconfEntries()
		self.ClearAll()
		self.do_standard_places()
		self.do_custom_places()

	def GetGconfEntries( self ):

		self.width = self.gconf.get( "int", "width", 200 )
		self.allowScrollbar = self.gconf.get( "bool", "allowScrollbar", False)
		self.scrolledWindow.set_policy( gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC )
		self.height = self.gconf.get( "int", "height", 180 )
		self.content_holder.set_size_request( self.width, self.height )
		if (self.allowScrollbar == False):
			self.height = -1
			self.scrolledWindow.set_policy( gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER )
		self.content_holder.set_size_request( self.width, self.height )
		self.execapp = self.gconf.get( "string", "execute_app", "nautilus" )
		self.iconsize = self.gconf.get( "int","icon_size", 2 )
		
		# Check default items
		
		self.showcomputer = self.gconf.get( "bool", "show_computer", True )
		self.showhomefolder = self.gconf.get( "bool", "show_home_folder", True )
		self.shownetwork = self.gconf.get( "bool", "show_network", True )
		self.showdesktop = self.gconf.get( "bool", "show_desktop", True )
		self.showtrash = self.gconf.get( "bool", "show_trash", True )
		
		# Get paths for custom items
		
		self.custompaths = self.gconf.get( "list-string", "custom_paths", [ ] )
		
		# Get names for custom items
		
		self.customnames = self.gconf.get( "list-string", "custom_names", [ ] )

		# Hide vertical dotted separator
		self.hideseparator = self.gconf.get( "bool", "hide_separator", False )
		# Plugin icon
		self.icon = self.gconf.get( "string", 'icon', "gnome-fs-directory.png" )
		# Allow plugin to be minimized to the left plugin pane
		self.sticky = self.gconf.get( "bool", "sticky", False )
		self.minimized = self.gconf.get( "bool", "minimized", False )

	def ClearAll(self):
		for child in self.placesBtnHolder.get_children():
			child.destroy()
		for child in self.editableBtnHolder.get_children():
			child.destroy()

	#Add standard places
	def do_standard_places( self ):		

		if ( self.showcomputer == True ):
			Button1 = easyButton( "computer", self.iconsize, [_("Computer")], -1, -1 )
			Button1.connect( "clicked", self.ButtonClicked, "nautilus --no-desktop computer:" )
			Button1.show()
			self.placesBtnHolder.pack_start( Button1, False, False )
			self.mintMenuWin.setTooltip( Button1, _("Browse all local and remote disks and folders accessible from this computer") )

		if ( self.showhomefolder == True ):
			Button2 = easyButton( "user-home", self.iconsize, [_("Home Folder")], -1, -1 )
			Button2.connect( "clicked", self.ButtonClicked, "nautilus --no-desktop" )
			Button2.show()
			self.placesBtnHolder.pack_start( Button2, False, False )
			self.mintMenuWin.setTooltip( Button2, _("Open your personal folder") )

		if ( self.shownetwork == True ):
			Button3 = easyButton( "network-workgroup", self.iconsize, [_("Network")], -1, -1 )
			Button3.connect( "clicked", self.ButtonClicked, "nautilus --no-desktop network:" )
			Button3.show()
			self.placesBtnHolder.pack_start( Button3, False, False )
			self.mintMenuWin.setTooltip( Button3, _("Browse bookmarked and local network locations") )
		
		if ( self.showdesktop == True ):
			# Determine where the Desktop folder is (could be localized)
			desktopDir = home + "/Desktop"
			try:
				import sys
				sys.path.append('/usr/lib/linuxmint/common')
				from configobj import ConfigObj
				config = ConfigObj(home + "/.config/user-dirs.dirs")
				tmpdesktopDir = config['XDG_DESKTOP_DIR']
				tmpdesktopDir = commands.getoutput("echo " + tmpdesktopDir)			
				if os.path.exists(tmpdesktopDir):
					desktopDir = tmpdesktopDir
			except Exception, detail:
				print detail
			Button4 = easyButton( "gnome-fs-desktop", self.iconsize, [_("Desktop")], -1, -1 )
			Button4.connect( "clicked", self.ButtonClicked, "nautilus " + desktopDir )
			Button4.show()
			self.placesBtnHolder.pack_start( Button4, False, False )
			self.mintMenuWin.setTooltip( Button4, _("Browse items placed on the desktop") )

		if ( self.showtrash == True ):
			self.trashButton = easyButton( "user-trash", self.iconsize, [_("Trash")], -1, -1 )
			self.trashButton.connect( "clicked", self.ButtonClicked, "nautilus --no-desktop trash:" )
			self.trashButton.show()
			self.trashButton.connect( "button-release-event", self.trashPopup )				
			self.refreshTrash()		
			self.placesBtnHolder.pack_start( self.trashButton, False, False )
			self.mintMenuWin.setTooltip( self.trashButton, _("Browse deleted files") )
			
	def do_custom_places( self ):		
		for index in range( len(self.custompaths) ):
			command = ( "nautilus --no-desktop " + self.custompaths[index] )
			currentbutton = easyButton( "folder", self.iconsize, [self.customnames[index]], -1, -1 )
			currentbutton.connect( "clicked", self.ButtonClicked, command )
			currentbutton.show()
			self.placesBtnHolder.pack_start( currentbutton, False, False )

	def trashPopup( self, widget, event ):
		if event.button == 3:
			trashMenu = gtk.Menu()
			emptyTrashMenuItem = gtk.MenuItem(_("Empty trash"))
			trashMenu.append(emptyTrashMenuItem)
			trashMenu.show_all()			
			emptyTrashMenuItem.connect ( "activate", self.emptyTrash, widget )						
			trashMenu.popup( None, None, None, event.button, event.time )

	def emptyTrash( self, menu, widget):				
		os.system("rm -rf " + home + "/.local/share/Trash/info/*")
		os.system("rm -rf " + home + "/.local/share/Trash/files/*")
		self.trashButton.setIcon("user-trash")

	def ButtonClicked( self, widget, Exec ):
		self.mintMenuWin.hide()
		if Exec:
			Execute( Exec )

	def do_plugin( self ):
		self.do_standard_places()
		self.do_custom_places()

	def refreshTrash (self):
			iconName = "user-trash"
			if (os.path.exists(home + "/.local/share/Trash/info")):			
				infoFiles = commands.getoutput("ls " + home + "/.local/share/Trash/info/ | wc -l")				
				if (int(infoFiles) > 0):
					iconName = "user-trash-full"		
			self.trashButton.setIcon(iconName)

