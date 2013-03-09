#!/usr/bin/env python

import sys

import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk


try:
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
from easygsettings import EasyGSettings

class mintMenuConfig( object ):

    def __init__( self ):

        self.path = os.path.abspath( os.path.dirname( sys.argv[0] ) )

        # Load glade file and extract widgets
        self.builder = Gtk.Builder()

        self.builder.add_from_file (os.path.join(self.path, "mintMenuConfig.glade" ))
        self.mainWindow=self.builder.get_object("mainWindow")

        #i18n
        self.mainWindow.set_title(_("Menu preferences"))
        self.mainWindow.set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")

        self.builder.get_object("startWithFavorites").set_label(_("Always start with favorites pane"))
        self.builder.get_object("showButtonIcon").set_label(_("Show button icon"))
        self.builder.get_object("useCustomColors").set_label(_("Use custom colors"))
        self.builder.get_object("showRecentPlugin").set_label(_("Show recent documents plugin"))
        self.builder.get_object("showApplicationsPlugin").set_label(_("Show applications plugin"))
        self.builder.get_object("showSystemPlugin").set_label(_("Show system plugin"))
        self.builder.get_object("showPlacesPlugin").set_label(_("Show places plugin"))

        self.builder.get_object("showAppComments").set_label(_("Show application comments"))
        self.builder.get_object("showCategoryIcons").set_label(_("Show category icons"))
        self.builder.get_object("hover").set_label(_("Hover"))
        self.builder.get_object("use_apt").set_label(_("Search for packages to install"))
        self.builder.get_object("swapGeneric").set_label(_("Swap name and generic name"))

        self.builder.get_object("label11").set_text(_("Border width:"))
        self.builder.get_object("label2").set_text(_("pixels"))

        self.builder.get_object("label8").set_text(_("Opacity:"))
        self.builder.get_object("label9").set_text("%")

        self.builder.get_object("buttonTextLabel").set_text(_("Button text:"))
        self.builder.get_object("label1").set_text(_("Options"))
        self.builder.get_object("label23").set_text(_("Applications"))

        self.builder.get_object("colorsLabel").set_text(_("Theme"))
        self.builder.get_object("favLabel").set_text(_("Favorites"))
        self.builder.get_object("label3").set_text(_("Main button"))

        self.builder.get_object("backgroundColorLabel").set_text(_("Background:"))
        self.builder.get_object("headingColorLabel").set_text(_("Headings:"))
        self.builder.get_object("borderColorLabel").set_text(_("Borders:"))
        self.builder.get_object("themeLabel").set_text(_("Theme:"))

        #self.builder.get_object("applicationsLabel").set_text(_("Applications"))
        #self.builder.get_object("favoritesLabel").set_text(_("Favorites"))
        self.builder.get_object("numberColumnsLabel").set_text(_("Number of columns:"))
        self.builder.get_object("iconSizeLabel").set_text(_("Icon size:"))
        self.builder.get_object("iconSizeLabel2").set_text(_("Icon size:"))
        self.builder.get_object("placesIconSizeLabel").set_text(_("Icon size:"))
        self.builder.get_object("systemIconSizeLabel").set_text(_("Icon size:"))
        self.builder.get_object("hoverLabel").set_text(_("Hover delay (ms):"))
        self.builder.get_object("label4").set_text(_("Button icon:"))
        self.builder.get_object("label5").set_text(_("Search command:"))

        self.builder.get_object("placesLabel").set_text(_("Places"))
        self.builder.get_object("allowscrollbarcheckbutton").set_label(_("Allow Scrollbar"))
        self.builder.get_object("showgtkbookmarkscheckbutton").set_label(_("Show GTK Bookmarks"))
        self.builder.get_object("placesHeightEntryLabel").set_text(_("Height:"))
        self.builder.get_object("defaultPlacesFrameLabel").set_text(_("Toggle Default Places:"))
        self.builder.get_object("computercheckbutton").set_label(_("Computer"))
        self.builder.get_object("homecheckbutton").set_label(_("Home Folder"))
        self.builder.get_object("networkcheckbutton").set_label(_("Network"))
        self.builder.get_object("desktopcheckbutton").set_label(_("Desktop"))
        self.builder.get_object("trashcheckbutton").set_label(_("Trash"))
        self.builder.get_object("customPlacesFrameLabel").set_text(_("Custom Places:"))

        self.builder.get_object("systemLabel").set_text(_("System"))
        self.builder.get_object("allowscrollbarcheckbutton1").set_label(_("Allow Scrollbar"))
        self.builder.get_object("systemHeightEntryLabel").set_text(_("Height:"))
        self.builder.get_object("defaultItemsFrameLabel").set_text(_("Toggle Default Items:"))
        self.builder.get_object("softwaremanagercheckbutton").set_label(_("Software Manager"))
        self.builder.get_object("packagemanagercheckbutton").set_label(_("Package Manager"))
        self.builder.get_object("controlcentercheckbutton").set_label(_("Control Center"))
        self.builder.get_object("terminalcheckbutton").set_label(_("Terminal"))
        self.builder.get_object("lockcheckbutton").set_label(_("Lock Screen"))
        self.builder.get_object("logoutcheckbutton").set_label(_("Log Out"))
        self.builder.get_object("quitcheckbutton").set_label(_("Quit"))

        self.editPlaceDialogTitle = (_("Edit Place"))
        self.newPlaceDialogTitle = (_("New Place"))
        self.folderChooserDialogTitle = (_("Select a folder"))

        self.builder.get_object("hotkey_label").set_text(_("Keyboard shortcut:"))

        self.startWithFavorites = self.builder.get_object( "startWithFavorites" )
        self.showAppComments = self.builder.get_object( "showAppComments" )
        self.useAPT = self.builder.get_object( "use_apt" )
        self.showCategoryIcons = self.builder.get_object( "showCategoryIcons" )
        self.showRecentPlugin = self.builder.get_object( "showRecentPlugin" )
        self.showApplicationsPlugin = self.builder.get_object( "showApplicationsPlugin" )
        self.showSystemPlugin = self.builder.get_object( "showSystemPlugin" )
        self.showPlacesPlugin = self.builder.get_object( "showPlacesPlugin" )
        self.swapGeneric = self.builder.get_object("swapGeneric")
        self.hover = self.builder.get_object( "hover" )
        self.hoverDelay = self.builder.get_object( "hoverDelay" )
        self.iconSize = self.builder.get_object( "iconSize" )
        self.favIconSize = self.builder.get_object( "favIconSize" )
        self.placesIconSize = self.builder.get_object( "placesIconSize" )
        self.systemIconSize = self.builder.get_object( "systemIconSize" )
        self.favCols = self.builder.get_object( "numFavCols" )
        self.borderWidth = self.builder.get_object( "borderWidth" )
        self.opacity = self.builder.get_object( "opacity" )
        self.useCustomColors = self.builder.get_object( "useCustomColors" )
        self.backgroundColor = self.builder.get_object( "backgroundColor" )
        self.borderColor = self.builder.get_object( "borderColor" )
        self.headingColor = self.builder.get_object( "headingColor" )
        self.backgroundColorLabel = self.builder.get_object( "backgroundColorLabel" )
        self.borderColorLabel = self.builder.get_object( "borderColorLabel" )
        self.headingColorLabel = self.builder.get_object( "headingColorLabel" )
        self.showButtonIcon = self.builder.get_object( "showButtonIcon" )
        self.buttonText = self.builder.get_object( "buttonText" )
        self.hotkeyText = self.builder.get_object( "hotkeyText" )
        self.buttonIcon = self.builder.get_object( "buttonIcon" )
        self.buttonIconChooser = self.builder.get_object( "button_icon_chooser" )
        self.image_filter = Gtk.FileFilter()
        self.image_filter.set_name(_("Images"))
        self.image_filter.add_pattern("*.png")
        self.image_filter.add_pattern("*.jpg")
        self.image_filter.add_pattern("*.jpeg")
        self.image_filter.add_pattern("*.bmp")
        self.image_filter.add_pattern("*.ico")
        self.image_filter.add_pattern("*.xpm")
        self.image_filter.add_pattern("*.svg")
        self.buttonIconChooser.add_filter(self.image_filter)
        self.buttonIconChooser.set_filter(self.image_filter)
        self.buttonIconImage = self.builder.get_object("image_button_icon")
        self.searchCommand = self.builder.get_object( "search_command" )
        self.computertoggle = self.builder.get_object( "computercheckbutton" )
        self.homefoldertoggle = self.builder.get_object( "homecheckbutton" )
        self.networktoggle = self.builder.get_object( "networkcheckbutton" )
        self.desktoptoggle = self.builder.get_object( "desktopcheckbutton" )
        self.trashtoggle = self.builder.get_object( "trashcheckbutton" )
        self.customplacestree = self.builder.get_object( "customplacestree" )
        self.allowPlacesScrollbarToggle = self.builder.get_object( "allowscrollbarcheckbutton" )
        self.showgtkbookmarksToggle = self.builder.get_object( "showgtkbookmarkscheckbutton" )
        self.placesHeightButton = self.builder.get_object( "placesHeightSpinButton" )
        if (self.allowPlacesScrollbarToggle.get_active() == False):
            self.placesHeightButton.set_sensitive(False)
        self.allowPlacesScrollbarToggle.connect("toggled", self.togglePlacesHeightEnabled )
        self.softwareManagerToggle = self.builder.get_object( "softwaremanagercheckbutton" )
        self.packageManagerToggle = self.builder.get_object( "packagemanagercheckbutton" )
        self.controlCenterToggle = self.builder.get_object( "controlcentercheckbutton" )
        self.packageManagerToggle = self.builder.get_object( "packagemanagercheckbutton" )
        self.terminalToggle = self.builder.get_object( "terminalcheckbutton" )
        self.lockToggle = self.builder.get_object( "lockcheckbutton" )
        self.logoutToggle = self.builder.get_object( "logoutcheckbutton" )
        self.quitToggle = self.builder.get_object( "quitcheckbutton" )
        self.allowSystemScrollbarToggle = self.builder.get_object( "allowscrollbarcheckbutton1" )
        self.systemHeightButton = self.builder.get_object( "systemHeightSpinButton" )
        if (self.allowSystemScrollbarToggle.get_active() == False): self.systemHeightButton.set_sensitive(False)
        self.allowSystemScrollbarToggle.connect("toggled", self.toggleSystemHeightEnabled )
        if os.path.exists("/usr/lib/linuxmint/mintInstall/icon.svg"):
            self.builder.get_object( "softwaremanagercheckbutton" ).show()
        else:
            self.builder.get_object( "softwaremanagercheckbutton" ).hide()

        self.builder.get_object( "closeButton" ).connect("clicked", Gtk.main_quit )


        self.settings = EasyGSettings( "com.linuxmint.mintmenu" )
        self.settingsApplications = EasyGSettings( "com.linuxmint.mintmenu.plugins.applications" )
        self.settingsPlaces = EasyGSettings( "com.linuxmint.mintmenu.plugins.places" )
        self.settingsSystem = EasyGSettings( "com.linuxmint.mintmenu.plugins.system_management" )

        self.useCustomColors.connect( "toggled", self.toggleUseCustomColors )

        self.bindGconfValueToWidget( self.settings, "bool", "start_with_favorites", self.startWithFavorites, "toggled", self.startWithFavorites.set_active, self.startWithFavorites.get_active )
        self.bindGconfValueToWidget( self.settingsApplications, "bool", "show_application_comments", self.showAppComments, "toggled", self.showAppComments.set_active, self.showAppComments.get_active )
        self.bindGconfValueToWidget( self.settingsApplications, "bool", "use_apt", self.useAPT, "toggled", self.useAPT.set_active, self.useAPT.get_active )
        self.bindGconfValueToWidget( self.settingsApplications, "bool", "show_category_icons", self.showCategoryIcons, "toggled", self.showCategoryIcons.set_active, self.showCategoryIcons.get_active )
        self.bindGconfValueToWidget( self.settingsApplications, "bool", "categories_mouse_over", self.hover, "toggled", self.hover.set_active, self.hover.get_active )
        self.bindGconfValueToWidget( self.settingsApplications, "bool", "swap_generic_name", self.swapGeneric, "toggled", self.swapGeneric.set_active, self.swapGeneric.get_active )

        self.bindGconfValueToWidget( self.settingsApplications, "int", "category_hover_delay", self.hoverDelay, "value-changed", self.hoverDelay.set_value, self.hoverDelay.get_value )
        self.bindGconfValueToWidget( self.settingsApplications, "int", "icon_size", self.iconSize, "value-changed", self.iconSize.set_value, self.iconSize.get_value )
        self.bindGconfValueToWidget( self.settingsApplications, "int", "favicon_size", self.favIconSize, "value-changed", self.favIconSize.set_value, self.favIconSize.get_value )
        self.bindGconfValueToWidget( self.settingsApplications, "int", "fav_cols", self.favCols, "value-changed", self.favCols.set_value, self.favCols.get_value )

        self.bindGconfValueToWidget( self.settingsPlaces, "int", "icon_size", self.placesIconSize, "value-changed", self.placesIconSize.set_value, self.placesIconSize.get_value )
        self.bindGconfValueToWidget( self.settingsSystem, "int", "icon_size", self.systemIconSize, "value-changed", self.systemIconSize.set_value, self.systemIconSize.get_value )

        self.bindGconfValueToWidget( self.settings, "int", "border_width", self.borderWidth, "value-changed", self.borderWidth.set_value, self.borderWidth.get_value_as_int )
        self.bindGconfValueToWidget( self.settings, "int", "opacity", self.opacity, "value-changed", self.opacity.set_value, self.opacity.get_value_as_int )
        self.bindGconfValueToWidget( self.settings, "bool", "use_custom_color", self.useCustomColors, "toggled", self.useCustomColors.set_active, self.useCustomColors.get_active )
        self.bindGconfValueToWidget( self.settings, "color", "custom_color", self.backgroundColor, "color-set", self.backgroundColor.set_color, self.getBackgroundColor )
        self.bindGconfValueToWidget( self.settings, "color", "custom_heading_color", self.headingColor, "color-set", self.headingColor.set_color, self.getHeadingColor )
        self.bindGconfValueToWidget( self.settings, "color", "custom_border_color", self.borderColor, "color-set", self.borderColor.set_color, self.getBorderColor )
        self.bindGconfValueToWidget( self.settings, "bool", "hide_applet_icon", self.showButtonIcon, "toggled", self.setShowButtonIcon, self.getShowButtonIcon )
        self.bindGconfValueToWidget( self.settings, "string", "applet_text", self.buttonText, "changed", self.buttonText.set_text, self.buttonText.get_text )
        self.bindGconfValueToWidget( self.settings, "string", "hot_key", self.hotkeyText, "changed", self.hotkeyText.set_text, self.hotkeyText.get_text )
        self.bindGconfValueToWidget( self.settings, "string", "applet_icon", self.buttonIconChooser, "file-set", self.setButtonIcon, self.buttonIconChooser.get_filename )
        self.bindGconfValueToWidget( self.settingsApplications, "string", "search_command", self.searchCommand, "changed", self.searchCommand.set_text, self.searchCommand.get_text )

        self.getPluginsToggle()
        self.showRecentPlugin.connect("toggled", self.setPluginsLayout )
        self.showApplicationsPlugin.connect("toggled", self.setPluginsLayout )
        self.showSystemPlugin.connect("toggled", self.setPluginsLayout )
        self.showPlacesPlugin.connect("toggled", self.setPluginsLayout )


        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "show_computer", self.computertoggle, "toggled", self.computertoggle.set_active, self.computertoggle.get_active )
        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "show_home_folder", self.homefoldertoggle, "toggled", self.homefoldertoggle.set_active, self.homefoldertoggle.get_active )
        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "show_network", self.networktoggle, "toggled", self.networktoggle.set_active, self.networktoggle.get_active )
        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "show_desktop", self.desktoptoggle, "toggled", self.desktoptoggle.set_active, self.desktoptoggle.get_active )
        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "show_trash", self.trashtoggle, "toggled", self.trashtoggle.set_active, self.trashtoggle.get_active )
        self.bindGconfValueToWidget( self.settingsPlaces, "int", "height", self.placesHeightButton, "value-changed", self.placesHeightButton.set_value, self.placesHeightButton.get_value_as_int )
        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "allowScrollbar", self.allowPlacesScrollbarToggle, "toggled", self.allowPlacesScrollbarToggle.set_active, self.allowPlacesScrollbarToggle.get_active )
        self.bindGconfValueToWidget( self.settingsPlaces, "bool", "show_gtk_bookmarks", self.showgtkbookmarksToggle, "toggled", self.showgtkbookmarksToggle.set_active, self.showgtkbookmarksToggle.get_active )

        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_software_manager", self.softwareManagerToggle, "toggled", self.softwareManagerToggle.set_active, self.softwareManagerToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_package_manager", self.packageManagerToggle, "toggled", self.packageManagerToggle.set_active, self.packageManagerToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_control_center", self.controlCenterToggle, "toggled", self.controlCenterToggle.set_active, self.controlCenterToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_terminal", self.terminalToggle, "toggled", self.terminalToggle.set_active, self.terminalToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_lock_screen", self.lockToggle, "toggled", self.lockToggle.set_active, self.lockToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_logout", self.logoutToggle, "toggled", self.logoutToggle.set_active, self.logoutToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "show_quit", self.quitToggle, "toggled", self.quitToggle.set_active, self.quitToggle.get_active )
        self.bindGconfValueToWidget( self.settingsSystem, "int", "height", self.systemHeightButton, "value-changed", self.systemHeightButton.set_value, self.systemHeightButton.get_value_as_int )
        self.bindGconfValueToWidget( self.settingsSystem, "bool", "allowScrollbar", self.allowSystemScrollbarToggle, "toggled", self.allowSystemScrollbarToggle.set_active, self.allowSystemScrollbarToggle.get_active )

        self.customplacepaths = self.settingsPlaces.get( "list-string", "custom_paths", [ ] )
        self.customplacenames = self.settingsPlaces.get( "list-string", "custom_names", [ ] )

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
        self.builder.get_object("newButton").connect("clicked", self.newPlace)
        self.builder.get_object("editButton").connect("clicked", self.editPlace)
        self.builder.get_object("upButton").connect("clicked", self.moveUp)
        self.builder.get_object("downButton").connect("clicked", self.moveDown)
        self.builder.get_object("removeButton").connect("clicked", self.removePlace)

        #Detect themes and show theme here
        theme_name = commands.getoutput("mateconftool-2 --get /apps/mintMenu/theme_name").strip()
        themes = commands.getoutput("find /usr/share/themes -name gtkrc")
        themes = themes.split("\n")
        model = gtk.ListStore(str, str)
        self.builder.get_object("themesCombo").set_model(model)
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
        self.builder.get_object("themesCombo").set_active_iter(selected_theme)
        self.builder.get_object("themesCombo").connect("changed", self.set_theme)
        self.mainWindow.present()
        self.getBackgroundColor()

    def set_theme(self, widget):
        model = widget.get_model()
        iter = widget.get_active_iter()
        theme_name = model.get_value(iter, 1)
        os.system("mateconftool-2 --type string --set /apps/mintMenu/theme_name \"%s\"" % theme_name)

    def getPluginsToggle(self):
        if (commands.getoutput("mateconftool-2 --get /apps/mintMenu/plugins_list | grep recent | wc -l") == "0"):
            self.showRecentPlugin.set_active(False)
        else:
            self.showRecentPlugin.set_active(True)
        if (commands.getoutput("mateconftool-2 --get /apps/mintMenu/plugins_list | grep applications | wc -l") == "0"):
            self.showApplicationsPlugin.set_active(False)
        else:
            self.showApplicationsPlugin.set_active(True)
        if (commands.getoutput("mateconftool-2 --get /apps/mintMenu/plugins_list | grep system_management | wc -l") == "0"):
            self.showSystemPlugin.set_active(False)
        else:
            self.showSystemPlugin.set_active(True)
        if (commands.getoutput("mateconftool-2 --get /apps/mintMenu/plugins_list | grep places | wc -l") == "0"):
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
        os.system("mateconftool-2 --type list --list-type string --set /apps/mintMenu/plugins_list [%s]" % layout)

    def setShowButtonIcon( self, value ):
        self.showButtonIcon.set_active(not value )

    def setButtonIcon( self, value ):
        self.buttonIconChooser.set_filename(value)
        self.buttonIconImage.set_from_file(value)

    def getShowButtonIcon( self ):
        return not self.showButtonIcon.get_active()

    def bindGSettingsValueToWidget( self, settings, setting_type, key, widget, changeEvent, setter, getter ):
        widget.connect( changeEvent, lambda *args: self.callGetter( settings, setting_type, key, getter ) )

        settings.notifyAdd( key, self.callSetter, args = [ setting_type, setter ] )
        if setting_type == "color":
            setter( Gdk.color_parse( settings.get( setting_type, key ) ) )
        else:
            setter( settings.get( setting_type, key ) )

    def callSetter( self, settings, key, args ):
        if args[0] == "bool":
            args[1]( settings.get_boolean(key) )
        elif args[0] == "string":
            args[1]( settings.get_string(key) )
        elif args[0] == "int":
            args[1]( settings.get_int(key) )
        elif args[0] == "color":
            args[1]( Gdk.color_parse( settings.get_string(key) ) )

    def callGetter( self, settings, setting_type, key, getter ):
        if (setting_type == "int"):
            settings.set( setting_type, key, int(getter()))
        else:
            settings.set( setting_type, key, getter())

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
        self.builder.get_object("label2").set_text(_("Name:"))
        self.builder.get_object("label1").set_text(_("Path:"))
        newPlaceDialog = self.builder.get_object( "editPlaceDialog" )
        folderChooserDialog = self.builder.get_object( "fileChooserDialog" )
        newPlaceDialog.set_transient_for(self.mainWindow)
        newPlaceDialog.set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")
        newPlaceDialog.set_title(self.newPlaceDialogTitle)
        folderChooserDialog.set_title(self.folderChooserDialogTitle)
        newPlaceDialog.set_default_response(Gtk.ResponseType.OK)
        newPlaceName = self.builder.get_object( "nameEntryBox" )
        newPlacePath = self.builder.get_object( "pathEntryBox" )
        folderButton = self.builder.get_object( "folderButton" )
        def chooseFolder(folderButton):
            currentPath = newPlacePath.get_text()
            if (currentPath!=""):
                folderChooserDialog.select_filename(currentPath)
            response = folderChooserDialog.run()
            folderChooserDialog.hide()
            if (response == Gtk.ResponseType.OK):
                newPlacePath.set_text( folderChooserDialog.get_filenames()[0] )
        folderButton.connect("clicked", chooseFolder)

        response = newPlaceDialog.run()
        newPlaceDialog.hide()
        if (response == Gtk.ResponseType.OK ):
            name = newPlaceName.get_text()
            path = newPlacePath.get_text()
            if (name != "" and path !=""):
                self.customplacestreemodel.append( (name, path) )

    def editPlace(self, editButton):
        self.builder.get_object("label2").set_text(_("Name:"))
        self.builder.get_object("label1").set_text(_("Path:"))
        editPlaceDialog = self.builder.get_object( "editPlaceDialog" )
        folderChooserDialog = self.builder.get_object( "fileChooserDialog" )
        editPlaceDialog.set_transient_for(self.mainWindow)
        editPlaceDialog.set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")
        editPlaceDialog.set_title(self.editPlaceDialogTitle)
        folderChooserDialog.set_title(self.folderChooserDialogTitle)
        editPlaceDialog.set_default_response(Gtk.ResponseType.OK)
        editPlaceName = self.builder.get_object( "nameEntryBox" )
        editPlacePath = self.builder.get_object( "pathEntryBox" )
        folderButton = self.builder.get_object( "folderButton" )
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
                if (response == Gtk.ResponseType.OK):
                    editPlacePath.set_text( folderChooserDialog.get_filenames()[0] )
            folderButton.connect("clicked", chooseFolder)
            response = editPlaceDialog.run()
            editPlaceDialog.hide()
            if (response == Gtk.ResponseType.OK):
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
            self.settingsPlaces.set( "list-string", "custom_paths", customplacepaths)
            self.settingsPlaces.set( "list-string", "custom_names", customplacenames)


window = mintMenuConfig()
Gtk.main()
