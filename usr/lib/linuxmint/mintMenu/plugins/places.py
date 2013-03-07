#!/usr/bin/env python

from gi.repository import Gtk, Gio
import os
import string
import gettext
import commands
import time
import ctypes
from ctypes import *

from easybuttons import *
from execute import Execute
from user import home
from urllib import unquote

gtk = CDLL("libgtk-x11-2.0.so.0")

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")

class pluginclass( object ):

    def __init__( self, mintMenuWin, toggleButton, de ):

        self.mintMenuWin = mintMenuWin
        self.toggleButton = toggleButton
        self.de = de

        # Read UI file        
        builder = Gtk.Builder()
        builder.add_from_file(os.path.join( os.path.dirname( __file__ ), "places.glade" ))        
               
        self.placesBtnHolder    = builder.get_object( "places_button_holder" )
        self.editableBtnHolder  = builder.get_object( "editable_button_holder" )
        self.scrolledWindow=builder.get_object("scrolledwindow2")
        # These properties are NECESSARY to maintain consistency

        # Set 'window' property for the plugin (Must be the root widget)
        self.window = builder.get_object( "mainWindow" )

        # Set 'heading' property for plugin
        self.heading = _("Places")

        # This should be the first item added to the window in glade
        self.content_holder = builder.get_object( "Places" )

        # Items to get custom colors
        self.itemstocolor = [ builder.get_object( "viewport2" ) ]

        # Settings        
        self.settings = Gio.Settings.new("com.linuxmint.mintmenu")  

        self.settings.connect( "changed::places-icon-size", self.RegenPlugin )
        self.settings.connect( "changed::places-show-computer", self.RegenPlugin )
        self.settings.connect( "changed::places-show-desktop", self.RegenPlugin )
        self.settings.connect( "changed::places-show-home_folder", self.RegenPlugin )
        self.settings.connect( "changed::places-show-network", self.RegenPlugin )
        self.settings.connect( "changed::places-show-trash", self.RegenPlugin )
        self.settings.connect( "changed::places-custom-names", self.RegenPlugin )
        self.settings.connect( "changed::places-custom-paths", self.RegenPlugin )
        self.settings.connect( "changed::places-allow-scrollbar", self.RegenPlugin )
        self.settings.connect( "changed::places-show-gtk-bookmarks", self.RegenPlugin )
        self.settings.connect( "changed::places-height", self.changePluginSize )
        self.settings.connect( "changed::places-width", self.changePluginSize )        

        self.loadSettings()

        self.content_holder.set_size_request( self.width, self.height )                            

    def wake (self) :
        if ( self.showtrash == True ):
            self.refreshTrash()

    def destroy( self ):
        self.settings.disconnect_all()

    def changePluginSize( self, client, connection_id, entry, args ):
        self.allowScrollbar = self.settings.get_boolean( "places-allow-scrollbar" )
        self.width = self.settings.get_int( "places-width" )               
        if (self.allowScrollbar == False):
            self.height = -1
            self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER )
        else:
            self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC )
            self.height = self.settings.get_int( "places-height" )
        self.content_holder.set_size_request( self.width, self.height )

    def RegenPlugin( self, *args, **kargs ):
        self.loadSettings()
        self.ClearAll()
        self.do_standard_places()
        self.do_custom_places()
        self.do_gtk_bookmarks()

    def loadSettings( self ):
        self.width = self.settings.get_int( "places-width" )
        self.allowScrollbar = self.settings.get_boolean( "places-allow-scrollbar" )
        self.showGTKBookmarks = self.settings.get_boolean( "places-show-gtk-bookmarks" )
        self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC )
        self.height = self.settings.get_int( "places-height" )
        self.content_holder.set_size_request( self.width, self.height )
        if (self.allowScrollbar == False):
            self.height = -1
            self.scrolledWindow.set_policy( Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.NEVER )
        self.content_holder.set_size_request( self.width, self.height )        
        self.iconsize = self.settings.get_int( "places-icon-size" )

        # Check default items

        self.showcomputer = self.settings.get_boolean( "places-show-computer" )
        self.showhomefolder = self.settings.get_boolean( "places-show-home-folder" )
        self.shownetwork = self.settings.get_boolean( "places-show-network" )
        self.showdesktop = self.settings.get_boolean( "places-show-desktop" )
        self.showtrash = self.settings.get_boolean( "places-show-trash" )

        # Get paths for custom items
        self.custompaths = self.settings.get_strv( "places-custom-paths" )

        # Get names for custom items
        self.customnames = self.settings.get_strv( "places-custom-names" )

        # Hide vertical dotted separator
        self.hideseparator = self.settings.get_boolean( "places-hide-separator" )
        # Plugin icon
        self.icon = self.settings.get_string( "places-icon" )
        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.settings.get_boolean( "places-sticky")
        self.minimized = self.settings.get_boolean( "places-minimized")
        
    def ClearAll(self):
        for child in self.placesBtnHolder.get_children():
            child.destroy()
        for child in self.editableBtnHolder.get_children():
            child.destroy()

    #Add standard places
    def do_standard_places( self ):

        if ( self.showcomputer == True ):
            Button1 = easyButton( "computer", self.iconsize, [_("Computer")], -1, -1 )
            if self.de == "mate":
                Button1.connect( "clicked", self.ButtonClicked, "caja computer:" )
            else:
                Button1.connect( "clicked", self.ButtonClicked, "xdg-open /" )
            Button1.show()
            self.placesBtnHolder.pack_start( Button1, False, False, 0)
            self.mintMenuWin.setTooltip( Button1, _("Browse all local and remote disks and folders accessible from this computer") )

        if ( self.showhomefolder == True ):
            Button2 = easyButton( "user-home", self.iconsize, [_("Home Folder")], -1, -1 )
            if self.de == "mate":
                Button2.connect( "clicked", self.ButtonClicked, "caja %s " % home )
            else:
                Button2.connect( "clicked", self.ButtonClicked, "xdg-open %s " % home )
            Button2.show()
            self.placesBtnHolder.pack_start( Button2, False, False, 0)
            self.mintMenuWin.setTooltip( Button2, _("Open your personal folder") )

        if ( self.shownetwork == True and self.de == "mate"):
            mate_settings = Gio.Settings.new("org.mate.interface")
            icon_theme = mate_settings.get_string( "icon-theme" )
            if "Mint-X" in icon_theme:
                Button3 = easyButton( "notification-network-ethernet-connected", self.iconsize, [_("Network")], -1, -1)
            else:
                Button3 = easyButton( "network-workgroup", self.iconsize, [_("Network")], -1, -1)
            if self.de == "mate":
                Button3.connect( "clicked", self.ButtonClicked, "caja network:" )
            else:
                Button3.connect( "clicked", self.ButtonClicked, "xdg-open network:" )
            Button3.show()
            self.placesBtnHolder.pack_start( Button3, False, False, 0)
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
            Button4 = easyButton( "desktop", self.iconsize, [_("Desktop")], -1, -1 )
            if self.de == "mate":
                Button4.connect( "clicked", self.ButtonClicked, "caja \"" + desktopDir + "\"")
            else:
                Button4.connect( "clicked", self.ButtonClicked, "xdg-open \"" + desktopDir + "\"")
            Button4.show()
            self.placesBtnHolder.pack_start( Button4, False, False, 0)
            self.mintMenuWin.setTooltip( Button4, _("Browse items placed on the desktop") )

        if ( self.showtrash == True ):
            self.trashButton = easyButton( "user-trash", self.iconsize, [_("Trash")], -1, -1 )
            if self.de == "xfce":
                self.trashButton.connect( "clicked", self.ButtonClicked, "thunar trash:" )
            elif self.de == "mate":
                self.trashButton.connect( "clicked", self.ButtonClicked, "caja trash:" )
            else:
                self.trashButton.connect( "clicked", self.ButtonClicked, "xdg-open trash:" )
            self.trashButton.show()
            self.trashButton.connect( "button-release-event", self.trashPopup )
            self.refreshTrash()
            self.placesBtnHolder.pack_start( self.trashButton, False, False, 0)
            self.mintMenuWin.setTooltip( self.trashButton, _("Browse deleted files") )

    def do_custom_places( self ):
        for index in range( len(self.custompaths) ):
            path = self.custompaths[index]
            path = path.replace("~", home)
            if self.de == "mate":
                command = ( "caja \"" + path + "\"")
            else:
                command = ( "xdg-open \"" + path + "\"")
            currentbutton = easyButton( "folder", self.iconsize, [self.customnames[index]], -1, -1 )
            currentbutton.connect( "clicked", self.ButtonClicked, command )
            currentbutton.show()
            self.placesBtnHolder.pack_start( currentbutton, False, False, 0)

    def do_gtk_bookmarks( self ):
        if self.showGTKBookmarks:
            bookmarks = {}            
            with open(os.path.expanduser('~/.gtk-bookmarks'), 'r') as f:
                for line in f:
                    #line = line.replace('file://', '')
                    line = line.rstrip()
                    parts = line.split(' ')

                    if len(parts) == 2:
                        bookmarks[parts[1]] = parts[0]
                    elif len(parts) == 1:
                        junk = os.path.split(parts[0])
                        bookmarks[junk[len(junk) - 1]] = parts[0]
                        
            for name, path in bookmarks.iteritems():                          
                name = unquote(name)
                currentbutton = easyButton( "folder", self.iconsize, [name], -1, -1 )
                currentbutton.connect( "clicked", self.launch_gtk_bookmark, path )
                currentbutton.show()
                self.placesBtnHolder.pack_start( currentbutton, False, False )
                
    def launch_gtk_bookmark (self, widget, path):
        self.mintMenuWin.hide()
        if self.de == "mate":
            os.system("caja %s &" % path)        
        else:
            os.system("xdg-open %s &" % path)        

    def trashPopup( self, widget, event ):
        if event.button == 3:
            trashMenu = Gtk.Menu()
            emptyTrashMenuItem = Gtk.MenuItem(_("Empty trash"))
            trashMenu.append(emptyTrashMenuItem)
            trashMenu.show_all()
            emptyTrashMenuItem.connect ( "activate", self.emptyTrash, widget )
            gtk.gtk_menu_popup(trashMenu, None, None, None, None, 3, 0)
            #trashMenu.popup( None, None, None, event.button, event.time )
         #   self.mintMenuWin.grab()
            return True


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
        self.do_gtk_bookmarks()

    def refreshTrash (self):
        iconName = "user-trash"
        if (os.path.exists(home + "/.local/share/Trash/info")):
            infoFiles = commands.getoutput("ls " + home + "/.local/share/Trash/info/ | wc -l")
            if (int(infoFiles) > 0):
                iconName = "user-trash-full"
        self.trashButton.setIcon(iconName)
