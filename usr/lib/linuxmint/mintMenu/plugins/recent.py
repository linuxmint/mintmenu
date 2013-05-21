import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk, Pango
import sys
import os
import gobject
import datetime
import fcntl
from easygsettings import EasyGSettings
from execute import Execute
from easyfiles import *
from easybuttons import *

class pluginclass:
    """This is the main class for the plugin"""
    """It MUST be named pluginclass"""

    def __init__( self, mintMenuWin, toggleButton, de ):

        self.Win = mintMenuWin
        self.toggleButton = toggleButton
        self.de = de

        self.builder = Gtk.Builder()
        #The Glade file for the plugin
        self.builder.add_from_file (os.path.join( os.path.dirname( __file__ ), "recent.glade" ))

        #Set 'window' property for the plugin (Must be the root widget)
        self.window = self.builder.get_object( "window1" )

        #Set 'heading' property for plugin
        self.heading = _("Recent documents")

        #This should be the first item added to the window in glade
        self.content_holder = self.builder.get_object( "eventbox1" )

        self.recentBox = self.builder.get_object("RecentBox")
        self.recentVBox = self.builder.get_object( "vbox1" )

        #Specify plugin width
        self.width = 250

        #Plugin icon
        self.icon = 'mate-folder.png'

        self.settings = EasyGSettings ("com.linuxmint.mintmenu.plugins.recent")

        self.settings.notifyAdd( 'height', self.RegenPlugin )
        self.settings.notifyAdd( 'width', self.RegenPlugin )
        self.settings.notifyAdd( 'num-recent-docs', self.RegenPlugin )
        self.settings.notifyAdd( 'recent-font-size', self.RegenPlugin )

        self.FileList=[]
        self.RecManagerInstance = Gtk.RecentManager.get_default()
        self.RecManagerInstance.connect("changed", self.DoRecent)

        self.RegenPlugin()
        self.builder.get_object( "RecentTabs" ).set_current_page(1)

        #Connect event handlers
        self.builder.get_object("ClrBtn").connect("clicked", self.clrmenu)

    def wake (self) :
        pass

    def RegenPlugin( self, *args, **kargs ):
        self.GetGSettingsEntries()

    def GetGSettingsEntries( self ):
        self.recenth = self.settings.get( 'int', 'height' )
        self.recentw = self.settings.get( 'int', 'width' )
        self.numentries = self.settings.get( 'int', 'num-recent-docs' )
        self.recentfontsize = self.settings.get( 'int', 'recent-font-size' )

        # Hide vertical dotted separator
        self.hideseparator = self.settings.get( "bool", "hide-separator" )
        # Plugin icon
        self.icon = self.settings.get( "string", 'icon' )
        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.settings.get( "bool", "sticky" )
        self.minimized = self.settings.get( "bool", "minimized" )
        self.RebuildPlugin()

    def SetHidden( self, state ):
        if state == True:
            self.settings.set( "bool", "minimized", True )
        else:
            self.settings.set( "bool", "minimized", False )


    def RebuildPlugin(self):
        self.content_holder.set_size_request(self.recentw, self.recenth )
        self.DoRecent()


    def DoRecent( self, *args, **kargs ):
        for i in self.recentBox.get_children():
            i.destroy()

        self.recentVBox.set_size_request( self.recentw, self.recenth )
        if len( self.recentBox.get_children() ) < self.numentries:
            n=len( self.recentBox.get_children() )-1
        else:
            n=self.numentries-1
        while n >= 0:
            self.recentBox.remove( self.recentBox.get_children()[n] )
            n-=1

        self.FileList, self.IconList = self.GetRecent()
        loc = 0
        for Name in self.FileList:
            if Name != None:
                self.AddRecentBtn( Name, self.IconList[loc] )
            loc = loc + 1
        return True

    def clrmenu(self, *args, **kargs):
        self.RecManagerInstance.purge_items()
        self.DoRecent()
        return

    def AddRecentBtn( self, Name, RecentImage ):
        DispName=os.path.basename( Name )

        AButton = Gtk.Button( "", "ok", True )
        AButton.remove( AButton.get_children()[0] )
        AButton.set_size_request( 200, -1 )
        AButton.set_relief( Gtk.ReliefStyle.NONE )
        AButton.connect( "clicked", self.callback, Name )

        Align1 = Gtk.Alignment()
        Align1.set( 0, 0.5, 0, 0)
        Align1.set_padding( 0, 0, 0, 0 )
        HBox1 = Gtk.HBox( False, 5 )
        VBox1 = Gtk.VBox( False, 2 )

        VBox1.show()

        req = Gtk.Requisition()
        AButton.size_request(req)

        Label1 = Gtk.Label( DispName )
        Label1.set_size_request( req.width-20, -1 )
        Label1.set_ellipsize( Pango.EllipsizeMode.END )
        Label1.show()
        VBox1.add( Label1 )

        ButtonIcon = Gtk.Image()
        ButtonIcon.set_from_pixbuf(RecentImage)
        HBox1.add( ButtonIcon )

        ButtonIcon.show()
        HBox1.add( VBox1 )
        HBox1.show()
        Align1.add( HBox1 )
        Align1.show()
        AButton.add( Align1 )
        AButton.show()

        self.recentBox.pack_start( AButton, False, True, 0 )

    def callback(self, widget, filename=None):
        self.Win.hide()

        x = os.system("gvfs-open \""+filename+"\"")
        if x == 256:
            dia = Gtk.Dialog('File not found!',
                             None,  #the toplevel wgt of your app
                             Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,  #binary flags or'ed together
                             ("Ok", 77))
            dia.vbox.pack_start(Gtk.Label('The location or file could not be found!'), False, False, 0)
            dia.vbox.show_all()
            dia.show()
            result = dia.run()
            if result == 77:
                dia.destroy()



    def GetRecent(self, *args, **kargs):
        FileString=[]
        IconString=[]
        RecentInfo=self.RecManagerInstance.get_items()
        # print RecentInfo[0].get_icon(gtk.ICON_SIZE_MENU)
        count=0
        MaxEntries=self.numentries
        if self.numentries == -1:
            MaxEntries=len(RecentInfo)
        for items in RecentInfo:
            FileString.append(items.get_uri_display())
            IconString.append(items.get_icon(Gtk.IconSize.MENU))
            count+=1
            if count >= MaxEntries:
                break
        return FileString,  IconString


    def ButtonClicked( self, widget, event, Exec ):
        self.press_x = event.x
        self.press_y = event.y
        self.Exec = Exec

    def ButtonReleased( self, w, ev, ev2 ):
        if ev.button == 1:
            if not hasattr( self, "press_x" ) or \
                    not w.drag_check_threshold( int( self.press_x ),
                                                                             int( self.press_y ),
                                                                             int( ev.x ),
                                                                             int( ev.y ) ):
                if self.Win.pinmenu == False:
                    self.Win.wTree.get_widget( "window1" ).hide()
                if "applications" in self.Win.plugins:
                    self.Win.plugins["applications"].wTree.get_widget( "entry1" ).grab_focus()
                Execute( w, self.Exec )

    def do_plugin(self):
        self.DoRecent()
