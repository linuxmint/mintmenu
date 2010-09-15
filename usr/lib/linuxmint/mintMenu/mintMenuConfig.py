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
gettext.install("mintmenu", "/usr/share/linuxmint/locale")

from easybuttons import iconManager
from easygconf import EasyGConf

class mintMenuConfig( object ):

    def __init__( self ):

        self.path = os.path.abspath( os.path.dirname( sys.argv[0] ) )

        # Load glade file and extract widgets
        gladefile = os.path.join( self.path, "mintMenuConfig.glade" )
        wTree     = gtk.glade.XML( gladefile, "mainWindow" )
        self.mainWindow=wTree.get_widget("mainWindow")

        #i18n
        self.mainWindow.set_title(_("Menu preferences"))
        self.mainWindow.set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")

        wTree.get_widget("startWithFavorites").set_label(_("Always start with favorites pane"))
        wTree.get_widget("showButtonIcon").set_label(_("Show button icon"))
        wTree.get_widget("useCustomColors").set_label(_("Use custom colors"))
        wTree.get_widget("showRecentPlugin").set_label(_("Show recent documents plugin"))
        wTree.get_widget("showApplicationsPlugin").set_label(_("Show applications plugin"))
        wTree.get_widget("showSystemPlugin").set_label(_("Show system plugin"))
        wTree.get_widget("showPlacesPlugin").set_label(_("Show places plugin"))

        wTree.get_widget("showAppComments").set_label(_("Show application comments"))
        wTree.get_widget("showCategoryIcons").set_label(_("Show category icons"))
        wTree.get_widget("hover").set_label(_("Hover"))
        wTree.get_widget("swapGeneric").set_label(_("Swap name and generic name"))

        wTree.get_widget("label11").set_text(_("Border width:"))
        wTree.get_widget("label2").set_text(_("pixels"))

        wTree.get_widget("label8").set_text(_("Opacity:"))
        wTree.get_widget("label9").set_text("%")

        wTree.get_widget("buttonTextLabel").set_text(_("Button text:"))
        wTree.get_widget("label1").set_text(_("Options"))
        wTree.get_widget("label23").set_text(_("Applications"))

        wTree.get_widget("colorsLabel").set_text(_("Colors"))
        wTree.get_widget("favLabel").set_text(_("Favorites"))
        wTree.get_widget("label3").set_text(_("Main button"))

        wTree.get_widget("backgroundColorLabel").set_text(_("Background:"))
        wTree.get_widget("headingColorLabel").set_text(_("Headings:"))
        wTree.get_widget("borderColorLabel").set_text(_("Borders:"))
        wTree.get_widget("themeLabel").set_text(_("Theme:"))

        #wTree.get_widget("applicationsLabel").set_text(_("Applications"))
        #wTree.get_widget("favoritesLabel").set_text(_("Favorites"))
        wTree.get_widget("numberColumnsLabel").set_text(_("Number of columns:"))
        wTree.get_widget("iconSizeLabel").set_text(_("Icon size:"))
        wTree.get_widget("iconSizeLabel2").set_text(_("Icon size:"))
        wTree.get_widget("label44").set_text(_("Icon size:"))
        wTree.get_widget("hoverLabel").set_text(_("Hover delay (ms):"))
        wTree.get_widget("label4").set_text(_("Button icon:"))
        wTree.get_widget("label5").set_text(_("Search command:"))

        wTree.get_widget("placesLabel").set_text(_("Places"))
        wTree.get_widget("allowscrollbarcheckbutton").set_label(_("Allow Scrollbar"))
        wTree.get_widget("placesHeightEntryLabel").set_text(_("Height:"))
        wTree.get_widget("defaultPlacesFrameLabel").set_text(_("Toggle Default Places:"))
        wTree.get_widget("computercheckbutton").set_label(_("Computer"))
        wTree.get_widget("homecheckbutton").set_label(_("Home Folder"))
        wTree.get_widget("networkcheckbutton").set_label(_("Network"))
        wTree.get_widget("desktopcheckbutton").set_label(_("Desktop"))
        wTree.get_widget("trashcheckbutton").set_label(_("Trash"))
        wTree.get_widget("customPlacesFrameLabel").set_text(_("Custom Places:"))

        wTree.get_widget("systemLabel").set_text(_("System"))
        wTree.get_widget("allowscrollbarcheckbutton1").set_label(_("Allow Scrollbar"))
        wTree.get_widget("systemHeightEntryLabel").set_text(_("Height:"))
        wTree.get_widget("defaultItemsFrameLabel").set_text(_("Toggle Default Items:"))
        wTree.get_widget("softwaremanagercheckbutton").set_label(_("Software Manager"))
        wTree.get_widget("packagemanagercheckbutton").set_label(_("Package Manager"))
        wTree.get_widget("controlcentercheckbutton").set_label(_("Control Center"))
        wTree.get_widget("terminalcheckbutton").set_label(_("Terminal"))
        wTree.get_widget("lockcheckbutton").set_label(_("Lock Screen"))
        wTree.get_widget("logoutcheckbutton").set_label(_("Log Out"))
        wTree.get_widget("quitcheckbutton").set_label(_("Quit"))

        self.editPlaceDialogTitle = (_("Edit Place"))
        self.newPlaceDialogTitle = (_("New Place"))
        self.folderChooserDialogTitle = (_("Select a folder"))

        wTree.get_widget("hotkey_label").set_text(_("Keyboard shortcut:"))

        self.startWithFavorites = wTree.get_widget( "startWithFavorites" )
        self.showAppComments = wTree.get_widget( "showAppComments" )
        self.showCategoryIcons = wTree.get_widget( "showCategoryIcons" )
        self.showRecentPlugin = wTree.get_widget( "showRecentPlugin" )
        self.showApplicationsPlugin = wTree.get_widget( "showApplicationsPlugin" )
        self.showSystemPlugin = wTree.get_widget( "showSystemPlugin" )
        self.showPlacesPlugin = wTree.get_widget( "showPlacesPlugin" )
        self.swapGeneric = wTree.get_widget("swapGeneric")
        self.hover = wTree.get_widget( "hover" )
        self.hoverDelay = wTree.get_widget( "hoverDelay" )
        self.bttniconSize = wTree.get_widget( "main_button_icon_size" )
        self.iconSize = wTree.get_widget( "iconSize" )
        self.favIconSize = wTree.get_widget( "favIconSize" )
        self.favCols = wTree.get_widget( "numFavCols" )
        self.borderWidth = wTree.get_widget( "borderWidth" )
        self.opacity = wTree.get_widget( "opacity" )
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
        self.computertoggle = wTree.get_widget( "computercheckbutton" )
        self.homefoldertoggle = wTree.get_widget( "homecheckbutton" )
        self.networktoggle = wTree.get_widget( "networkcheckbutton" )
        self.desktoptoggle = wTree.get_widget( "desktopcheckbutton" )
        self.trashtoggle = wTree.get_widget( "trashcheckbutton" )
        self.customplacestree = wTree.get_widget( "customplacestree" )
        self.allowPlacesScrollbarToggle = wTree.get_widget( "allowscrollbarcheckbutton" )
        self.placesHeightButton = wTree.get_widget( "placesHeightSpinButton" )
        if (self.allowPlacesScrollbarToggle.get_active() == False):
            self.placesHeightButton.set_sensitive(False)
        self.allowPlacesScrollbarToggle.connect("toggled", self.togglePlacesHeightEnabled )
        self.softwareManagerToggle = wTree.get_widget( "softwaremanagercheckbutton" )
        self.packageManagerToggle = wTree.get_widget( "packagemanagercheckbutton" )
        self.controlCenterToggle = wTree.get_widget( "controlcentercheckbutton" )
        self.packageManagerToggle = wTree.get_widget( "packagemanagercheckbutton" )
        self.terminalToggle = wTree.get_widget( "terminalcheckbutton" )
        self.lockToggle = wTree.get_widget( "lockcheckbutton" )
        self.logoutToggle = wTree.get_widget( "logoutcheckbutton" )
        self.quitToggle = wTree.get_widget( "quitcheckbutton" )
        self.allowSystemScrollbarToggle = wTree.get_widget( "allowscrollbarcheckbutton1" )
        self.systemHeightButton = wTree.get_widget( "systemHeightSpinButton" )
        if (self.allowSystemScrollbarToggle.get_active() == False): self.systemHeightButton.set_sensitive(False)
        self.allowSystemScrollbarToggle.connect("toggled", self.toggleSystemHeightEnabled )
        if os.path.exists("/usr/lib/linuxmint/mintInstall/icon.svg"):
            wTree.get_widget( "softwaremanagercheckbutton" ).show()
        else:
            wTree.get_widget( "softwaremanagercheckbutton" ).hide()

        wTree.get_widget( "closeButton" ).connect("clicked", gtk.main_quit )


        self.gconf = EasyGConf( "/apps/mintMenu/" )
        self.gconfApplications = EasyGConf( "/apps/mintMenu/plugins/applications/" )
        self.gconfPlaces = EasyGConf( "/apps/mintMenu/plugins/places/" )
        self.gconfSystem = EasyGConf( "/apps/mintMenu/plugins/system-management/" )

        self.useCustomColors.connect( "toggled", self.toggleUseCustomColors )

        self.bindGconfValueToWidget( self.gconf, "bool", "start_with_favorites", self.startWithFavorites, "toggled", self.startWithFavorites.set_active, self.startWithFavorites.get_active )
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
        self.bindGconfValueToWidget( self.gconf, "int", "opacity", self.opacity, "value-changed", self.opacity.set_value, self.opacity.get_value_as_int )
        self.bindGconfValueToWidget( self.gconf, "bool", "use_custom_color", self.useCustomColors, "toggled", self.useCustomColors.set_active, self.useCustomColors.get_active )
        self.bindGconfValueToWidget( self.gconf, "color", "custom_color", self.backgroundColor, "color-set", self.backgroundColor.set_color, self.getBackgroundColor )
        self.bindGconfValueToWidget( self.gconf, "color", "custom_heading_color", self.headingColor, "color-set", self.headingColor.set_color, self.getHeadingColor )
        self.bindGconfValueToWidget( self.gconf, "color", "custom_border_color", self.borderColor, "color-set", self.borderColor.set_color, self.getBorderColor )
        self.bindGconfValueToWidget( self.gconf, "bool", "hide_applet_icon", self.showButtonIcon, "toggled", self.setShowButtonIcon, self.getShowButtonIcon )
        self.bindGconfValueToWidget( self.gconf, "string", "applet_text", self.buttonText, "changed", self.buttonText.set_text, self.buttonText.get_text )
        self.bindGconfValueToWidget( self.gconf, "string", "hot_key", self.hotkeyText, "changed", self.hotkeyText.set_text, self.hotkeyText.get_text )
        self.bindGconfValueToWidget( self.gconf, "string", "applet_icon", self.buttonIcon, "changed", self.setButtonIcon, self.buttonIcon.get_text )
        self.bindGconfValueToWidget( self.gconfApplications, "string", "search_command", self.searchCommand, "changed", self.searchCommand.set_text, self.searchCommand.get_text )

        self.getPluginsToggle()
        self.showRecentPlugin.connect("toggled", self.setPluginsLayout )
        self.showApplicationsPlugin.connect("toggled", self.setPluginsLayout )
        self.showSystemPlugin.connect("toggled", self.setPluginsLayout )
        self.showPlacesPlugin.connect("toggled", self.setPluginsLayout )


        self.bindGconfValueToWidget( self.gconfPlaces, "bool", "show_computer", self.computertoggle, "toggled", self.computertoggle.set_active, self.computertoggle.get_active )
        self.bindGconfValueToWidget( self.gconfPlaces, "bool", "show_home_folder", self.homefoldertoggle, "toggled", self.homefoldertoggle.set_active, self.homefoldertoggle.get_active )
        self.bindGconfValueToWidget( self.gconfPlaces, "bool", "show_network", self.networktoggle, "toggled", self.networktoggle.set_active, self.networktoggle.get_active )
        self.bindGconfValueToWidget( self.gconfPlaces, "bool", "show_desktop", self.desktoptoggle, "toggled", self.desktoptoggle.set_active, self.desktoptoggle.get_active )
        self.bindGconfValueToWidget( self.gconfPlaces, "bool", "show_trash", self.trashtoggle, "toggled", self.trashtoggle.set_active, self.trashtoggle.get_active )
        self.bindGconfValueToWidget( self.gconfPlaces, "int", "height", self.placesHeightButton, "value-changed", self.placesHeightButton.set_value, self.placesHeightButton.get_value_as_int )
        self.bindGconfValueToWidget( self.gconfPlaces, "bool", "allowScrollbar", self.allowPlacesScrollbarToggle, "toggled", self.allowPlacesScrollbarToggle.set_active, self.allowPlacesScrollbarToggle.get_active )

        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_software_manager", self.softwareManagerToggle, "toggled", self.softwareManagerToggle.set_active, self.softwareManagerToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_package_manager", self.packageManagerToggle, "toggled", self.packageManagerToggle.set_active, self.packageManagerToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_control_center", self.controlCenterToggle, "toggled", self.controlCenterToggle.set_active, self.controlCenterToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_terminal", self.terminalToggle, "toggled", self.terminalToggle.set_active, self.terminalToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_lock_screen", self.lockToggle, "toggled", self.lockToggle.set_active, self.lockToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_logout", self.logoutToggle, "toggled", self.logoutToggle.set_active, self.logoutToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "show_quit", self.quitToggle, "toggled", self.quitToggle.set_active, self.quitToggle.get_active )
        self.bindGconfValueToWidget( self.gconfSystem, "int", "height", self.systemHeightButton, "value-changed", self.systemHeightButton.set_value, self.systemHeightButton.get_value_as_int )
        self.bindGconfValueToWidget( self.gconfSystem, "bool", "allowScrollbar", self.allowSystemScrollbarToggle, "toggled", self.allowSystemScrollbarToggle.set_active, self.allowSystemScrollbarToggle.get_active )

        self.customplacepaths = self.gconfPlaces.get( "list-string", "custom_paths", [ ] )
        self.customplacenames = self.gconfPlaces.get( "list-string", "custom_names", [ ] )

        self.customplacestreemodel = gtk.ListStore( str, str)
        self.cell = gtk.CellRendererText()

        for count in range( len(self.customplacepaths) ):
            self.customplacestreemodel.append( [ self.customplacenames[count], self.customplacepaths[count] ] )

        self.customplacestreemodel.connect("row-changed", self.updatePlacesGconf)
        self.customplacestreemodel.connect("row-deleted", self.updatePlacesGconf)
        self.customplacestreemodel.connect("rows-reordered", self.updatePlacesGconf)
        self.customplacestree.set_model( self.customplacestreemodel )
        self.namescolumn = gtk.TreeViewColumn( _("Name"), self.cell, text = 0 )
        self.placescolumn = gtk.TreeViewColumn( _("Path"), self.cell, text = 1 )
        self.customplacestree.append_column( self.namescolumn )
        self.customplacestree.append_column( self.placescolumn )
        wTree.get_widget("newButton").connect("clicked", self.newPlace)
        wTree.get_widget("editButton").connect("clicked", self.editPlace)
        wTree.get_widget("upButton").connect("clicked", self.moveUp)
        wTree.get_widget("downButton").connect("clicked", self.moveDown)
        wTree.get_widget("removeButton").connect("clicked", self.removePlace)
        
        #Detect themes and show theme here
        theme_name = commands.getoutput("gconftool-2 --get /apps/mintMenu/theme_name").strip()
        themes = commands.getoutput("find /usr/share/themes -name gtkrc")
        themes = themes.split("\n")
        model = gtk.ListStore(str, str)   
        wTree.get_widget("themesCombo").set_model(model)
        selected_theme = model.append([_("Desktop theme"), "default"])
        for theme in themes:
            if theme.startswith("/usr/share/themes") and theme.endswith("/gtk-2.0/gtkrc"):
                theme = theme.replace("/usr/share/themes/", "")
                theme = theme.replace("gtk-2.0", "")
                theme = theme.replace("gtkrc", "")
                theme = theme.replace("/", "")
                theme = theme.strip()
                iter = model.append([theme, theme])
                if theme == theme_name:
                    selected_theme = iter
        wTree.get_widget("themesCombo").set_active_iter(selected_theme)
        wTree.get_widget("themesCombo").connect("changed", self.set_theme)
        self.mainWindow.present()
        self.getBackgroundColor()
        
    def set_theme(self, widget):
        model = widget.get_model()
        iter = widget.get_active_iter()
        theme_name = model.get_value(iter, 1)
        os.system("gconftool-2 --type string --set /apps/mintMenu/theme_name \"%s\"" % theme_name)

    def getPluginsToggle(self):
        if (commands.getoutput("gconftool-2 --get /apps/mintMenu/plugins_list | grep recent | wc -l") == "0"):
            self.showRecentPlugin.set_active(False)
        else:
            self.showRecentPlugin.set_active(True)
        if (commands.getoutput("gconftool-2 --get /apps/mintMenu/plugins_list | grep applications | wc -l") == "0"):
            self.showApplicationsPlugin.set_active(False)
        else:
            self.showApplicationsPlugin.set_active(True)
        if (commands.getoutput("gconftool-2 --get /apps/mintMenu/plugins_list | grep system_management | wc -l") == "0"):
            self.showSystemPlugin.set_active(False)
        else:
            self.showSystemPlugin.set_active(True)
        if (commands.getoutput("gconftool-2 --get /apps/mintMenu/plugins_list | grep places | wc -l") == "0"):
            self.showPlacesPlugin.set_active(False)
        else:
            self.showPlacesPlugin.set_active(True)

    def setPluginsLayout (self, widget):
        visiblePlugins = []
        if self.showPlacesPlugin.get_active():
            visiblePlugins.append("places")
        if self.showSystemPlugin.get_active():
            visiblePlugins.append("system_management")
        if self.showApplicationsPlugin.get_active():
            if self.showPlacesPlugin.get_active() or self.showSystemPlugin.get_active():
                visiblePlugins.append("newpane")
            visiblePlugins.append("applications")
        if self.showRecentPlugin.get_active():
            if self.showApplicationsPlugin.get_active() or self.showPlacesPlugin.get_active() or self.showSystemPlugin.get_active():
                visiblePlugins.append("newpane")
            visiblePlugins.append("recent")
        layout = ""
        for plugin in visiblePlugins:
            layout = layout + plugin + ","            
        if len(layout) > 0 and layout[-1] == ",":
            layout = layout[0:-1]
        os.system("gconftool-2 --type list --list-type string --set /apps/mintMenu/plugins_list [%s]" % layout)

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

    def moveUp( self, upButton ):

        treeselection = self.customplacestree.get_selection()
        currentiter = (treeselection.get_selected())[1]

        if ( treeselection != None ):

            lagiter = self.customplacestreemodel.get_iter_first()
            nextiter = self.customplacestreemodel.get_iter_first()

            while ( (self.customplacestreemodel.get_path(nextiter) != self.customplacestreemodel.get_path(currentiter)) & (nextiter != None)):
                lagiter = nextiter
                nextiter = self.customplacestreemodel.iter_next(nextiter)

            if (nextiter != None):
                self.customplacestreemodel.swap(currentiter, lagiter)

        return

    def newPlace(self, newButton):
        gladefile = os.path.join( self.path, "mintMenuConfig.glade" )
        wTree = gtk.glade.XML( gladefile, "editPlaceDialog" )
        wTree.get_widget("label2").set_text(_("Name:"))
        wTree.get_widget("label1").set_text(_("Path:"))
        folderChooserTree = gtk.glade.XML( gladefile, "fileChooserDialog" )
        newPlaceDialog = wTree.get_widget( "editPlaceDialog" )
        folderChooserDialog = folderChooserTree.get_widget( "fileChooserDialog" )
        newPlaceDialog.set_transient_for(self.mainWindow)
        newPlaceDialog.set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")
        newPlaceDialog.set_title(self.newPlaceDialogTitle)
        folderChooserDialog.set_title(self.folderChooserDialogTitle)
        newPlaceDialog.set_default_response(gtk.RESPONSE_OK)
        newPlaceName = wTree.get_widget( "nameEntryBox" )
        newPlacePath = wTree.get_widget( "pathEntryBox" )
        folderButton = wTree.get_widget( "folderButton" )
        def chooseFolder(folderButton):
            currentPath = newPlacePath.get_text()
            if (currentPath!=""):
                folderChooserDialog.select_filename(currentPath)
            response = folderChooserDialog.run()
            folderChooserDialog.hide()
            if (response == gtk.RESPONSE_OK):
                newPlacePath.set_text( folderChooserDialog.get_filenames()[0] )
        folderButton.connect("clicked", chooseFolder)

        response = newPlaceDialog.run()
        newPlaceDialog.hide()
        if (response == gtk.RESPONSE_OK ):
            name = newPlaceName.get_text()
            path = newPlacePath.get_text()
            if (name != "" and path !=""):
                self.customplacestreemodel.append( (name, path) )

    def editPlace(self, editButton):
        gladefile = os.path.join( self.path, "mintMenuConfig.glade" )
        wTree = gtk.glade.XML( gladefile, "editPlaceDialog" )
        wTree.get_widget("label2").set_text(_("Name:"))
        wTree.get_widget("label1").set_text(_("Path:"))
        folderChooserTree = gtk.glade.XML( gladefile, "fileChooserDialog" )
        editPlaceDialog = wTree.get_widget( "editPlaceDialog" )
        folderChooserDialog = folderChooserTree.get_widget( "fileChooserDialog" )
        editPlaceDialog.set_transient_for(self.mainWindow)
        editPlaceDialog.set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")
        editPlaceDialog.set_title(self.editPlaceDialogTitle)
        folderChooserDialog.set_title(self.folderChooserDialogTitle)
        editPlaceDialog.set_default_response(gtk.RESPONSE_OK)
        editPlaceName = wTree.get_widget( "nameEntryBox" )
        editPlacePath = wTree.get_widget( "pathEntryBox" )
        folderButton = wTree.get_widget( "folderButton" )
        treeselection = self.customplacestree.get_selection()
        currentiter = (treeselection.get_selected())[1]

        if (currentiter != None):

            initName = self.customplacestreemodel.get_value(currentiter, 0)
            initPath = self.customplacestreemodel.get_value(currentiter, 1)

            editPlaceName.set_text(initName)
            editPlacePath.set_text(initPath)
            def chooseFolder(folderButton):
                currentPath = editPlacePath.get_text()
                if (currentPath!=""):
                    folderChooserDialog.select_filename(currentPath)
                response = folderChooserDialog.run()
                folderChooserDialog.hide()
                if (response == gtk.RESPONSE_OK):
                    editPlacePath.set_text( folderChooserDialog.get_filenames()[0] )
            folderButton.connect("clicked", chooseFolder)
            response = editPlaceDialog.run()
            editPlaceDialog.hide()
            if (response == gtk.RESPONSE_OK):
                name = editPlaceName.get_text()
                path = editPlacePath.get_text()
                if (name != "" and path != ""):
                    self.customplacestreemodel.set_value(currentiter, 0, name)
                    self.customplacestreemodel.set_value(currentiter, 1, path)

    def moveDown(self, downButton):

        treeselection = self.customplacestree.get_selection()
        currentiter = (treeselection.get_selected())[1]

        nextiter = self.customplacestreemodel.iter_next(currentiter)

        if (nextiter != None):
            self.customplacestreemodel.swap(currentiter, nextiter)

        return


    def removePlace(self, removeButton):

        treeselection = self.customplacestree.get_selection()
        currentiter = (treeselection.get_selected())[1]

        if (currentiter != None):
            self.customplacestreemodel.remove(currentiter)

        return

    def togglePlacesHeightEnabled(self, toggle):
        if (toggle.get_active() == True):
            self.placesHeightButton.set_sensitive(True)
        else:
            self.placesHeightButton.set_sensitive(False)

    def toggleSystemHeightEnabled(self, toggle):
        if (toggle.get_active() == True):
            self.systemHeightButton.set_sensitive(True)
        else:
            self.systemHeightButton.set_sensitive(False)

    def updatePlacesGconf(self, treemodel, path, iter = None, new_order = None):
# Do only if not partway though an append operation; Append = insert+change+change and each creates a signal
        if ((iter == None) or (self.customplacestreemodel.get_value(iter, 1) != None)):
            treeiter = self.customplacestreemodel.get_iter_first()
            customplacenames = [ ]
            customplacepaths = [ ]
            while( treeiter != None ):
                customplacenames = customplacenames + [ self.customplacestreemodel.get_value(treeiter, 0 ) ]
                customplacepaths = customplacepaths + [ self.customplacestreemodel.get_value(treeiter, 1 ) ]
                treeiter = self.customplacestreemodel.iter_next(treeiter)
            self.gconfPlaces.set( "list-string", "custom_paths", customplacepaths)
            self.gconfPlaces.set( "list-string", "custom_names", customplacenames)


window = mintMenuConfig()
gtk.main()
