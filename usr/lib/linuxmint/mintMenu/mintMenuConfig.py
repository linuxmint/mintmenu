#!/usr/bin/env python

import sys

try:
	 import pygtk
	 pygtk.require( "2.0" )
except:
	  pass
try:
	import gtk
	import gtk.glade
	import gettext
	import os
	import commands
except Exception, e:
	print e
	sys.exit( 1 )

PATH = os.path.abspath( os.path.dirname( sys.argv[0] ) )

sys.path.append( os.path.join( PATH , "plugins") )

# i18n
gettext.install("messages", "/usr/lib/linuxmint/mintMenu/locale")

from easybuttons import iconManager
from easygconf import EasyGConf

class mintMenuConfig( object ):
	
	def __init__( self ):

		self.path = os.path.abspath( os.path.dirname( sys.argv[0] ) )

		# Load glade file and extract widgets
		gladefile = os.path.join( self.path, "mintMenuConfig.glade" )
		wTree 	  = gtk.glade.XML( gladefile, "mainWindow" )
	

		#i18n
		wTree.get_widget("mainWindow").set_title(_("mintMenu Preferences"))

		wTree.get_widget("showSidepane").set_label(_("Show sidepane"))
		wTree.get_widget("showButtonIcon").set_label(_("Show button icon"))
		wTree.get_widget("useCustomColors").set_label(_("Use custom colors"))
		wTree.get_widget("showRecentPlugin").set_label(_("Show recent documents"))

		wTree.get_widget("showAppComments").set_label(_("Show application comments"))
		wTree.get_widget("showCategoryIcons").set_label(_("Show category icons"))
		wTree.get_widget("hover").set_label(_("Hover"))
		wTree.get_widget("swapGeneric").set_label(_("Swap name and generic name"))

		wTree.get_widget("label11").set_text(_("Border width:"))
		wTree.get_widget("label2").set_text(_("pixels"))
		wTree.get_widget("buttonTextLabel").set_text(_("Button text:"))
		wTree.get_widget("label1").set_text(_("Options"))
		wTree.get_widget("label23").set_text(_("Applications"))

		wTree.get_widget("colorsLabel").set_text(_("Colors"))
		wTree.get_widget("favLabel").set_text(_("Favorites"))
		wTree.get_widget("label3").set_text(_("Main button"))
		
		wTree.get_widget("backgroundColorLabel").set_text(_("Background:"))
		wTree.get_widget("headingColorLabel").set_text(_("Headings:"))
		wTree.get_widget("borderColorLabel").set_text(_("Borders:"))
		
		#wTree.get_widget("applicationsLabel").set_text(_("Applications"))
		#wTree.get_widget("favoritesLabel").set_text(_("Favorites"))
		wTree.get_widget("numberColumnsLabel").set_text(_("Number of columns:"))
		wTree.get_widget("iconSizeLabel").set_text(_("Icon size:"))
		wTree.get_widget("iconSizeLabel2").set_text(_("Icon size:"))
		wTree.get_widget("label44").set_text(_("Icon size:"))		
		wTree.get_widget("hoverLabel").set_text(_("Hover delay (ms):"))
		wTree.get_widget("label4").set_text(_("Button icon:"))
		wTree.get_widget("label5").set_text(_("Search command:"))

		wTree.get_widget("hotkey_label").set_text(_("Keyboard shortcut:"))

		self.showSidepane = wTree.get_widget( "showSidepane" )
		self.showAppComments = wTree.get_widget( "showAppComments" )
		self.showCategoryIcons = wTree.get_widget( "showCategoryIcons" )
		self.showRecentPlugin = wTree.get_widget( "showRecentPlugin" )
		self.swapGeneric = wTree.get_widget("swapGeneric")
		self.hover = wTree.get_widget( "hover" )
		self.hoverDelay = wTree.get_widget( "hoverDelay" )
		self.bttniconSize = wTree.get_widget( "main_button_icon_size" )
		self.iconSize = wTree.get_widget( "iconSize" )
		self.favIconSize = wTree.get_widget( "favIconSize" )
		self.favCols = wTree.get_widget( "numFavCols" )
		self.borderWidth = wTree.get_widget( "borderWidth" )
		self.useCustomColors = wTree.get_widget( "useCustomColors" )
		self.backgroundColor = wTree.get_widget( "backgroundColor" )
		self.borderColor = wTree.get_widget( "borderColor" )
		self.headingColor = wTree.get_widget( "headingColor" )
		self.backgroundColorLabel = wTree.get_widget( "backgroundColorLabel" )
		self.borderColorLabel = wTree.get_widget( "borderColorLabel" )
		self.headingColorLabel = wTree.get_widget( "headingColorLabel" )
		self.showButtonIcon = wTree.get_widget( "showButtonIcon" )
		self.buttonText = wTree.get_widget( "buttonText" )
		self.hotkeyText = wTree.get_widget( "hotkeyText" )
		self.buttonIcon = wTree.get_widget( "buttonIcon" )	
		self.buttonIconImage = wTree.get_widget( "image_button_icon" )	
		self.searchCommand = wTree.get_widget( "search_command" )		
		wTree.get_widget( "closeButton" ).connect("clicked", gtk.main_quit )

		
		self.gconf = EasyGConf( "/apps/mintMenu/" )
		self.gconfApplications = EasyGConf( "/apps/mintMenu/plugins/applications/" )
		
		self.useCustomColors.connect( "toggled", self.toggleUseCustomColors )
		
		self.bindGconfValueToWidget( self.gconf, "bool", "show_side_pane", self.showSidepane, "toggled", self.showSidepane.set_active, self.showSidepane.get_active )
		self.bindGconfValueToWidget( self.gconfApplications, "bool", "show_application_comments", self.showAppComments, "toggled", self.showAppComments.set_active, self.showAppComments.get_active )
		self.bindGconfValueToWidget( self.gconfApplications, "bool", "show_category_icons", self.showCategoryIcons, "toggled", self.showCategoryIcons.set_active, self.showCategoryIcons.get_active )
		self.bindGconfValueToWidget( self.gconfApplications, "bool", "categories_mouse_over", self.hover, "toggled", self.hover.set_active, self.hover.get_active )
		self.bindGconfValueToWidget( self.gconfApplications, "bool", "swap_generic_name", self.swapGeneric, "toggled", self.swapGeneric.set_active, self.swapGeneric.get_active )

		self.bindGconfValueToWidget( self.gconfApplications, "int", "category_hover_delay", self.hoverDelay, "value-changed", self.hoverDelay.set_value, self.hoverDelay.get_value )
		self.bindGconfValueToWidget( self.gconfApplications, "int", "icon_size", self.iconSize, "value-changed", self.iconSize.set_value, self.iconSize.get_value )
		self.bindGconfValueToWidget( self.gconf, "int", "applet_icon_size", self.bttniconSize, "value-changed", self.bttniconSize.set_value, self.bttniconSize.get_value )				
		self.bindGconfValueToWidget( self.gconfApplications, "int", "favicon_size", self.favIconSize, "value-changed", self.favIconSize.set_value, self.favIconSize.get_value )
		self.bindGconfValueToWidget( self.gconfApplications, "int", "fav_cols", self.favCols, "value-changed", self.favCols.set_value, self.favCols.get_value )

		self.bindGconfValueToWidget( self.gconf, "int", "border_width", self.borderWidth, "value-changed", self.borderWidth.set_value, self.borderWidth.get_value_as_int )
		self.bindGconfValueToWidget( self.gconf, "bool", "use_custom_color", self.useCustomColors, "toggled", self.useCustomColors.set_active, self.useCustomColors.get_active )
		self.bindGconfValueToWidget( self.gconf, "color", "custom_color", self.backgroundColor, "color-set", self.backgroundColor.set_color, self.getBackgroundColor )
		self.bindGconfValueToWidget( self.gconf, "color", "custom_heading_color", self.headingColor, "color-set", self.headingColor.set_color, self.getHeadingColor )
		self.bindGconfValueToWidget( self.gconf, "color", "custom_border_color", self.borderColor, "color-set", self.borderColor.set_color, self.getBorderColor )
		self.bindGconfValueToWidget( self.gconf, "bool", "hide_applet_icon", self.showButtonIcon, "toggled", self.setShowButtonIcon, self.getShowButtonIcon )
		self.bindGconfValueToWidget( self.gconf, "string", "applet_text", self.buttonText, "changed", self.buttonText.set_text, self.buttonText.get_text )
		self.bindGconfValueToWidget( self.gconf, "string", "hot_key", self.hotkeyText, "changed", self.hotkeyText.set_text, self.hotkeyText.get_text )
		self.bindGconfValueToWidget( self.gconf, "string", "applet_icon", self.buttonIcon, "changed", self.setButtonIcon, self.buttonIcon.get_text )		
		self.bindGconfValueToWidget( self.gconfApplications, "string", "search_command", self.searchCommand, "changed", self.searchCommand.set_text, self.searchCommand.get_text )

		self.showRecentPlugin.connect("toggled", self.toggleRecent )
		self.showRecentPlugin.set_active( self.getRecentToggle() )
		
		wTree.get_widget( "mainWindow" ).present()
		
		self.getBackgroundColor()

	def toggleRecent(self, widget):
		if self.showRecentPlugin.get_active():
			os.system("gconftool-2 --type list --list-type string --set /apps/mintMenu/plugins_list [newpane,places,system_management,newpane,applications,newpane,recent]")
		else:
			os.system("gconftool-2 --type list --list-type string --set /apps/mintMenu/plugins_list [newpane,places,system_management,newpane,applications]")

	def getRecentToggle(self):
		if (commands.getoutput("gconftool-2 --get /apps/mintMenu/plugins_list | grep recent | wc -l") == "0"):
			return False
		else:
			return True

	def setShowButtonIcon( self, value ):
		self.showButtonIcon.set_active(not value )	

	def setButtonIcon( self, value ):
		self.buttonIcon.set_text(value)
		self.buttonIconImage.set_from_file(value)

	def getShowButtonIcon( self ):
		return not self.showButtonIcon.get_active()

	def bindGconfValueToWidget( self, gconf, gconfType, gconfPath, widget, changeEvent, setter, getter ):
		widget.connect( changeEvent, lambda *args: self.callGetter( gconf, gconfType, gconfPath, getter ) )

		gconf.notifyAdd( gconfPath, self.callSetter, args = [ gconfType, setter ] )
		if gconfType == "color":
			setter( gtk.gdk.color_parse( gconf.get( gconfType, gconfPath ) ) )
		else:
			setter( gconf.get( gconfType, gconfPath ) )

	def callSetter( self, client, connection_id, entry, args ):
		if args[0] == "bool":
			args[1]( entry.get_value().get_bool() )
		elif args[0] == "string":
			args[1]( entry.get_value().get_string() )
		elif args[0] == "int":
			args[1]( entry.get_value().get_int() )
		elif args[0] == "color":
			args[1]( gtk.gdk.color_parse( entry.get_value().get_string() ) )
		
	def callGetter( self, gconf, gconfType, gconfPath, getter ):
		gconf.set( gconfType, gconfPath, getter() )
		
	def toggleUseCustomColors( self, widget ):
		self.backgroundColor.set_sensitive( widget.get_active() )
		self.borderColor.set_sensitive( widget.get_active() )
		self.headingColor.set_sensitive(  widget.get_active() )
		self.backgroundColorLabel.set_sensitive( widget.get_active() )
		self.borderColorLabel.set_sensitive( widget.get_active() )
		self.headingColorLabel.set_sensitive(  widget.get_active() )
		
	def getBackgroundColor( self ):
		return self.gdkColorToString( self.backgroundColor.get_color() )
	
	def getBorderColor( self ):
		return self.gdkColorToString( self.borderColor.get_color() )
		
	def getHeadingColor( self ):
		return self.gdkColorToString( self.headingColor.get_color() )
		
	def gdkColorToString( self, gdkColor ):
		return "#%.2X%.2X%.2X" % ( gdkColor.red / 256, gdkColor.green / 256, gdkColor.blue / 256 )
		

window = mintMenuConfig()
gtk.main()
