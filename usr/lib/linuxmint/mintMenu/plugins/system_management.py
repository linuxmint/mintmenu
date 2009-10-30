#!/usr/bin/env python

import gtk
import gtk.glade
import os
import gconf
import gnomevfs
import string
import gettext

from easybuttons import *
from execute import Execute
from easygconf import EasyGConf

# i18n
gettext.install("messages", "/usr/lib/linuxmint/mintMenu/locale")

class pluginclass( object ):
	
	def __init__( self, mintMenuWin, toggleButton ):
		
		self.mintMenuWin = mintMenuWin
		self.toggleButton = toggleButton
		
		# Read GLADE file
		gladefile 				= os.path.join( os.path.dirname( __file__ ), "system_management.glade" )
		wTree 					= gtk.glade.XML( gladefile, "mainWindow" )
		self.systemBtnHolder	= wTree.get_widget( "system_button_holder" )
		self.editableBtnHolder 	= wTree.get_widget( "editable_button_holder" )
		self.scrolledWindow = wTree.get_widget( "scrolledwindow2" )

		# These properties are NECESSARY to maintain consistency

		# Set 'window' property for the plugin (Must be the root widget)
		self.window = wTree.get_widget( "mainWindow" )

		# Set 'heading' property for plugin
		self.heading = _("System")

		# This should be the first item added to the window in glade
		self.content_holder = wTree.get_widget( "System" )

		# Items to get custom colors
		self.itemstocolor = [ wTree.get_widget( "viewport2" ) ]

		# Gconf stuff
		self.gconf = EasyGConf( "/apps/mintMenu/plugins/system-management/" )

		self.gconf.notifyAdd( "icon_size", self.RegenPlugin )
		self.gconf.notifyAdd( "show_control_center", self.RegenPlugin )
		self.gconf.notifyAdd( "show_lock_screen", self.RegenPlugin )
		self.gconf.notifyAdd( "show_logout", self.RegenPlugin )
		self.gconf.notifyAdd( "show_package_manager", self.RegenPlugin )
		self.gconf.notifyAdd( "show_software_manager", self.RegenPlugin )
		self.gconf.notifyAdd( "show_terminal", self.RegenPlugin )
		self.gconf.notifyAdd( "show_quit", self.RegenPlugin )
		self.gconf.notifyAdd( "allowScrollbar", self.changePluginSize )
		self.gconf.notifyAdd( "allowScrollbar", self.RegenPlugin )
		self.gconf.notifyAdd( "height", self.changePluginSize )
		self.gconf.notifyAdd( "width", self.changePluginSize )		
		self.gconf.bindGconfEntryToVar( "bool", "sticky", self, "sticky" )

		self.GetGconfEntries()
		
		self.content_holder.set_size_request( self.width, self.height )

	def destroy( self ):
		self.gconf.notifyRemoveAll()

	def wake (self) :
		pass

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
		self.do_standard_items()

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
		self.iconsize = self.gconf.get( "int","icon_size", 2 )

		# Check toggles

		self.showSoftwareManager = self.gconf.get( "bool", "show_software_manager", True )
		self.showPackageManager = self.gconf.get( "bool", "show_package_manager", True )
		self.showControlCenter = self.gconf.get( "bool", "show_control_center", True )
		self.showTerminal = self.gconf.get( "bool", "show_terminal", True )
		self.showLockScreen = self.gconf.get( "bool", "show_lock_screen", True )
		self.showLogout = self.gconf.get( "bool", "show_logout", True )
		self.showQuit = self.gconf.get( "bool", "show_quit", True )

		# Hide vertical dotted separator
		self.hideseparator = self.gconf.get( "bool", "hide_separator", False )
		# Plugin icon
		self.icon = self.gconf.get( "string", 'icon', "preferences-system" )
		# Allow plugin to be minimized to the left plugin pane
		self.sticky = self.gconf.get( "bool", "sticky", False )
		self.minimized = self.gconf.get( "bool", "minimized", False )

	def ClearAll(self):
		for child in self.systemBtnHolder.get_children():
			child.destroy()
		for child in self.editableBtnHolder.get_children():
			child.destroy()

	#Add standard items
	def do_standard_items( self ):		

		if ( self.showSoftwareManager == True ):
			if os.path.exists("/usr/lib/linuxmint/mintInstall/icon.svg"):
				Button1 = easyButton( "/usr/lib/linuxmint/mintInstall/icon.svg", self.iconsize, [_("Software manager")], -1, -1 )
				Button1.connect( "clicked", self.ButtonClicked, "mintinstall" )
				Button1.show()
				self.systemBtnHolder.pack_start( Button1, False, False )
				self.mintMenuWin.setTooltip( Button1, _("Browse and install available software") )

		if ( self.showPackageManager == True ):
			Button2 = easyButton( "synaptic", self.iconsize, [_("Package manager")], -1, -1 )
			Button2.connect( "clicked", self.ButtonClicked, "gksu /usr/sbin/synaptic" )
			Button2.show()
			self.systemBtnHolder.pack_start( Button2, False, False )
			self.mintMenuWin.setTooltip( Button2, _("Install, remove and upgrade software packages") )

		if ( self.showControlCenter == True ):
			Button3 = easyButton( "gtk-preferences", self.iconsize, [_("Control center")], -1, -1 )
			Button3.connect( "clicked", self.ButtonClicked, "gnome-control-center" )
			Button3.show()
			self.systemBtnHolder.pack_start( Button3, False, False )
			self.mintMenuWin.setTooltip( Button3, _("Configure your system") )
		
		if ( self.showTerminal == True ):
			Button4 = easyButton( "gnome-terminal", self.iconsize, [_("Terminal")], -1, -1 )
			Button4.connect( "clicked", self.ButtonClicked, "x-terminal-emulator" )
			Button4.show()
			self.systemBtnHolder.pack_start( Button4, False, False )
			self.mintMenuWin.setTooltip( Button4, _("Use the command line") )

		if ( self.showLockScreen == True ):
			Button5 = easyButton( "system-lock-screen", self.iconsize, [_("Lock Screen")], -1, -1 )
			Button5.connect( "clicked", self.ButtonClicked, "xdg-screensaver lock" )
			Button5.show()
			self.systemBtnHolder.pack_start( Button5, False, False )
			self.mintMenuWin.setTooltip( Button5, _("Requires password to unlock") )

		if ( self.showLogout == True ):
			Button6 = easyButton( "system-log-out", self.iconsize, [_("Logout")], -1, -1 )
			Button6.connect( "clicked", self.ButtonClicked, "gnome-session-save --logout-dialog" )
			Button6.show()
			self.systemBtnHolder.pack_start( Button6, False, False )
			self.mintMenuWin.setTooltip( Button6, _("Log out or switch user") )

		if ( self.showQuit == True ):
			Button7 = easyButton( "system-shutdown", self.iconsize, [_("Quit")], -1, -1 )
			Button7.connect( "clicked", self.ButtonClicked, "gnome-session-save --shutdown-dialog" )
			Button7.show()
			self.systemBtnHolder.pack_start( Button7, False, False )
			self.mintMenuWin.setTooltip( Button7, _("Shutdown, restart, suspend or hibernate") )

	def ButtonClicked( self, widget, Exec ):
		self.mintMenuWin.hide()
		if Exec:
			Execute( Exec )

	def do_plugin( self ):
		   self.do_standard_items()


