import gtk
import gtk.glade
import sys
import os
import gobject
import datetime
import mateconf
import fcntl
import pango
from execute import Execute
from easygconf import *
from easyfiles import *
from easybuttons import *



class pluginclass:
    """This is the main class for the plugin"""
    """It MUST be named pluginclass"""

    def __init__( self, mintMenuWin, toggleButton, de ):

        self.Win = mintMenuWin
        self.toggleButton = toggleButton
        self.de = de

        #The Glade file for the plugin
        self.gladefile = os.path.join( os.path.dirname( __file__ ), "recent.glade" )

        #Read GLADE file
        self.wTree = gtk.glade.XML( self.gladefile, "window1" )

        #Set 'window' property for the plugin (Must be the root widget)
        self.window = self.wTree.get_widget( "window1" )

        #Set 'heading' property for plugin
        self.heading = _("Recent documents")

        #This should be the first item added to the window in glade
        self.content_holder = self.wTree.get_widget( "eventbox1" )

        #Specify plugin width
        self.width = 250

        #Plugin icon
        self.icon = 'mate-folder.png'

        self.gconf_dir = '/apps/mintMenu/plugins/recent'
        self.client = mateconf.client_get_default()
        self.client.add_dir( '/apps/mintMenu/plugins/recent', mateconf.CLIENT_PRELOAD_NONE )
        self.client.notify_add( '/apps/mintMenu/plugins/recent/height', self.RegenPlugin )
        self.client.notify_add( '/apps/mintMenu/plugins/recent/width', self.RegenPlugin )
        self.client.notify_add( '/apps/mintMenu/plugins/recent/num_recent_docs_to_show', self.RegenPlugin )
        self.client.notify_add( '/apps/mintMenu/plugins/recent/recent_font_size', self.RegenPlugin )

        self.FileList=[]
        self.RecManagerInstance = gtk.recent_manager_get_default()
        self.RecManagerInstance.connect("changed",self.DoRecent)


        self.RegenPlugin()
        self.wTree.get_widget( "RecentTabs" ).set_current_page(1)

        #Connect event handlers
        dic = { "on_ClrBtn_clicked" : self.clrmenu}
        self.wTree.signal_autoconnect( dic )

    def wake (self) :
        pass

    def RegenPlugin( self, *args, **kargs ):
        self.GetGconfEntries()

    def GetGconfEntries( self ):
        self.gconf = EasyGConf( "/apps/mintMenu/plugins/recent/" )
        self.recenth = self.gconf.get( 'int', 'height', 385 )
        self.recentw = self.gconf.get( 'int', 'width', 250 )
        self.numentries = self.gconf.get( 'int', 'num_recent_docs_to_show', 10 )
        self.recentfontsize = self.gconf.get( 'int', 'recent_font_size', 9 )

        # Hide vertical dotted separator
        self.hideseparator = self.gconf.get( "bool", "hide_separator", False )
        # Plugin icon
        self.icon = self.gconf.get( "string", 'icon', "mate-fs-directory" )
        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.gconf.get( "bool", "sticky", False )
        self.minimized = self.gconf.get( "bool", "minimized", False )
        self.RebuildPlugin()

    def SetHidden( self, state ):
        if state == True:
            self.gconf.set( "bool", "minimized", True )
        else:
            self.gconf.set( "bool", "minimized", False )


    def RebuildPlugin(self):
        self.content_holder.set_size_request(self.recentw, self.recenth )
        self.DoRecent()


    def DoRecent( self, *args, **kargs ):
        for i in self.wTree.get_widget( "RecentBox" ).get_children():
            i.destroy()

        self.wTree.get_widget( "vbox1" ).set_size_request( self.recentw, self.recenth )
        if len( self.wTree.get_widget( "RecentBox" ).get_children() ) < self.numentries:
            n=len( self.wTree.get_widget( "RecentBox" ).get_children() )-1
        else:
            n=self.numentries-1
        while n >= 0:
            self.wTree.get_widget( "RecentBox" ).remove( self.wTree.get_widget( "RecentBox" ).get_children()[n] )
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

        AButton = gtk.Button( "", "ok", True )
        AButton.remove( AButton.get_children()[0] )
        AButton.set_size_request( 200, -1 )
        AButton.set_relief( gtk.RELIEF_NONE )
        AButton.connect( "clicked", self.callback, Name )

        Align1 = gtk.Alignment( 0, 0.5, 0, 0 )
        Align1.set_padding( 0, 0, 0, 0 )
        HBox1 = gtk.HBox( False, 5 )
        VBox1 = gtk.VBox( False, 2 )

        VBox1.show()


        Label1 = gtk.Label( DispName )
        Label1.set_size_request( AButton.size_request()[0]-20, -1 )
        Label1.set_ellipsize( pango.ELLIPSIZE_END )
        Label1.show()
        VBox1.add( Label1 )

        ButtonIcon = gtk.Image()
        ButtonIcon.set_from_pixbuf(RecentImage)
        HBox1.add( ButtonIcon )

        ButtonIcon.show()
        HBox1.add( VBox1 )
        HBox1.show()
        Align1.add( HBox1 )
        Align1.show()
        AButton.add( Align1 )
        AButton.show()

        self.wTree.get_widget( "RecentBox" ).pack_start( AButton, False, True, 0 )

    def callback(self, widget, filename=None):
        self.Win.hide()

        x = os.system("mate-open \""+filename+"\"")
        if x == 256:
            dia = gtk.Dialog('File not found!',
                             None,  #the toplevel wgt of your app
                             gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,  #binary flags or'ed together
                             ("Ok", 77))
            dia.vbox.pack_start(gtk.Label('The location or file could not be found!'))
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
            IconString.append(items.get_icon(gtk.ICON_SIZE_MENU))
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
