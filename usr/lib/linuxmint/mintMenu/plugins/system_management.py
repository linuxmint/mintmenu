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
		if entry.get_key() == self.gconf.gconfDir+"width":
			self.width = entry.get_value().get_int()
		elif entry.get_key() == self.gconf.gconfDir+"height":
			self.heigth = entry.get_value().get_int()

		self.content_holder.set_size_request( self.width, self.height )


	def RegenPlugin( self, *args, **kargs ):
		self.GetGconfEntries()
		self.ClearAll()
		self.do_standard_items()

	def GetGconfEntries( self ):

		self.width = self.gconf.get( "int", "width", 200 )
		self.height = self.gconf.get( "int", "height", 180 )
		self.iconsize = self.gconf.get( "int","icon_size", 2 )

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

		Button1 = easyButton( "/usr/lib/linuxmint/mintSystem/icon.png", self.iconsize, [_("Software manager")], -1, -1 )
		Button1.connect( "clicked", self.ButtonClicked, "mintinstall" )
		Button1.show()
		self.systemBtnHolder.pack_start( Button1, False, False )
		self.mintMenuWin.setTooltip( Button1, _("Browse and install available software") )

		Button2 = easyButton( "synaptic", self.iconsize, [_("Package manager")], -1, -1 )
		Button2.connect( "clicked", self.ButtonClicked, "gksu /usr/sbin/synaptic" )
		Button2.show()
		self.systemBtnHolder.pack_start( Button2, False, False )
		self.mintMenuWin.setTooltip( Button2, _("Install, remove and upgrade software packages") )

		Button3 = easyButton( "gtk-preferences", self.iconsize, [_("Control center")], -1, -1 )
		Button3.connect( "clicked", self.ButtonClicked, "gnome-control-center" )
		Button3.show()
		self.systemBtnHolder.pack_start( Button3, False, False )
		self.mintMenuWin.setTooltip( Button3, _("Configure your system") )
		
		Button4 = easyButton( "gnome-terminal", self.iconsize, [_("Terminal")], -1, -1 )
		Button4.connect( "clicked", self.ButtonClicked, "x-terminal-emulator" )
		Button4.show()
		self.systemBtnHolder.pack_start( Button4, False, False )
		self.mintMenuWin.setTooltip( Button4, _("Use the command line") )

		Button5 = easyButton( "system-log-out", self.iconsize, [_("Logout")], -1, -1 )
		Button5.connect( "clicked", self.ButtonClicked, "gnome-session-save --logout-dialog" )
		Button5.show()
		self.systemBtnHolder.pack_start( Button5, False, False )
		self.mintMenuWin.setTooltip( Button5, _("Log out or switch user") )

		Button6 = easyButton( "system-shutdown", self.iconsize, [_("Quit")], -1, -1 )
		Button6.connect( "clicked", self.ButtonClicked, "gnome-session-save --shutdown-dialog" )
		Button6.show()
		self.systemBtnHolder.pack_start( Button6, False, False )
		self.mintMenuWin.setTooltip( Button6, _("Shutdown, restart, suspend or hibernate") )

	def ButtonClicked( self, widget, Exec ):
		self.mintMenuWin.hide()
		if Exec:
			Execute( Exec )

	def do_plugin( self ):
		   self.do_standard_items()


