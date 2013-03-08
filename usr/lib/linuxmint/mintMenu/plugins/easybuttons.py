#!/usr/bin/env python

from gi.repository import Gtk, GdkPixbuf, Gdk
from gi.repository import Pango
#import matedesktop
from gi.repository import GObject
import os.path
import shutil
import re
from execute import *
import xdg.DesktopEntry
import xdg.Menu
from filemonitor import monitor as filemonitor
import glib
import ctypes
from ctypes import *

gtk = CDLL("libgtk-x11-2.0.so.0")

class IconManager(GObject.GObject):

    __gsignals__ = {
            "changed" : (GObject.SignalFlags.RUN_LAST, None, () )
    }

    def __init__( self ):
        GObject.GObject.__init__( self )
        self.icons = { }
        self.count = 0

        # Some apps don't put a default icon in the default theme folder, so we will search all themes
        def createTheme( d ):
            theme = Gtk.IconTheme()
            theme.set_custom_theme( d )
            return theme

        # This takes to much time and there are only a very few applications that use icons from different themes
        #self.themes = map(  createTheme, [ d for d in os.listdir( "/usr/share/icons" ) if os.path.isdir( os.path.join( "/usr/share/icons", d ) ) ] )

        defaultTheme = Gtk.IconTheme()
        defaultKdeTheme = createTheme( "kde.default" )

        # Themes with the same content as the default them aren't needed
        #self.themes = [ theme for theme in self.themes if  theme.list_icons() != defaultTheme.list_icons() ]

        self.themes = [ defaultTheme, defaultKdeTheme ]

        self.cache = {}

        # Listen for changes in the themes
        for theme in self.themes:
            theme.connect("changed", self.themeChanged )


    def getIcon( self, iconName, iconSize ):
        if not iconName:
            return None

        try:
            #[ iconWidth, iconHeight ] = self.getIconSize( iconSize )
            if iconSize <= 0:
                return None

            if iconName in self.cache and iconSize in self.cache[iconName]:
                iconFileName = self.cache[iconName][iconSize]
            elif os.path.isabs( iconName ):
                iconFileName = iconName
            else:
                if iconName[-4:] in [".png", ".xpm", ".svg", ".gif"]:
                    realIconName = iconName[:-4]
                else:
                    realIconName = iconName
                tmp = None
                for theme in self.themes:
                    if theme.has_icon( realIconName ):
                        tmp = theme.lookup_icon( realIconName, iconSize, 0 )
                        if tmp:
                            break

                if tmp:
                    iconFileName = tmp.get_filename()
                else:
                    iconFileName = ""

            if iconFileName and os.path.exists( iconFileName ):
                icon = GdkPixbuf.Pixbuf.new_from_file_at_size( iconFileName, iconSize, iconSize )
            else:
                icon = None


            # if the actual icon size is to far from the desired size resize it
            if icon and (( icon.get_width() - iconSize ) > 5 or ( icon.get_height() - iconSize ) > 5):
                if icon.get_width() > icon.get_height():
                    newIcon = icon.scale_simple( iconSize, icon.get_height() * iconSize / icon.get_width(), GdkPixbuf.InterpType.BILINEAR )
                else:
                    newIcon = icon.scale_simple( icon.get_width() * iconSize / icon.get_height(), iconSize, GdkPixbuf.InterpType.BILINEAR )
                del icon
                icon = newIcon

            if iconName in self.cache:
                self.cache[iconName][iconSize] = iconFileName
            else:
                self.cache[iconName] = { iconSize : iconFileName }

            return icon
        except Exception, e:
            print "Exception " + e.__class__.__name__ + ": " + e.message
            return None

    def themeChanged( self, theme ):
        self.cache = { }
        self.emit( "changed" )

GObject.type_register(IconManager)

class easyButton( Gtk.Button ):

    def __init__( self, iconName, iconSize, labels = None, buttonWidth = -1, buttonHeight = -1 ):
        GObject.GObject.__init__( self )
        self.connections = [ ]
        self.iconName = iconName
        self.iconSize = iconSize
        self.showIcon = True

        self.set_relief( Gtk.ReliefStyle.NONE )
        self.set_size_request( buttonWidth, buttonHeight )

        Align1 = Gtk.Alignment.new( 0, 0.5, 1.0, 0 )
        HBox1 = Gtk.HBox()
        self.labelBox = Gtk.VBox( False, 2 )


        self.buttonImage = Gtk.Image()
        icon = self.getIcon( self.iconSize )
        if icon:
            self.buttonImage.set_from_pixbuf( icon )
            del icon
        else:
            #[ iW, iH ] = iconManager.getIconSize( self.iconSize )
            self.buttonImage.set_size_request( self.iconSize, self.iconSize  )
        self.buttonImage.show()
        HBox1.pack_start( self.buttonImage, False, False, 5 )        

        if labels:
            for label in labels:
                if isinstance( label, basestring ):
                    self.addLabel( label )                   
                elif isinstance( label, list ):
                    self.addLabel( label[0], label[1] )

        self.labelBox.show()
        HBox1.pack_start( self.labelBox , True, True, 0)
        HBox1.show()
        Align1.add( HBox1 )
        Align1.show()
        self.add( Align1 )

        self.connectSelf( "destroy", self.onDestroy )
        self.connect( "released", self.onRelease )
        # Reload icons when the theme changed
        self.themeChangedHandlerId = iconManager.connect("changed", self.themeChanged )

    def connectSelf( self, event, callback ):
        self.connections.append( self.connect( event, callback ) )

    def onRelease( self, widget ):
        widget.set_state(Gtk.StateType.NORMAL)

    def onDestroy( self, widget ):
        self.buttonImage.clear()
        iconManager.disconnect( self.themeChangedHandlerId )
        for connection in self.connections:
            self.disconnect( connection )
        del self.connections


    def addLabel( self, text, styles = None ):
        label = Gtk.Label()
        if "<b>" in text or "<span" in text:
            label.set_markup(text) # don't remove our pango
        else:
            label.set_markup(glib.markup_escape_text(text))

        if styles:
            labelStyle = Pango.AttrList()
            for attr in styles:
                labelStyle.insert( attr )
            label.set_attributes( labelStyle )

        label.set_ellipsize( Pango.EllipsizeMode.END )
        label.set_alignment( 0.0, 1.0 )
        label.show()
        self.labelBox.pack_start( label , True, True, 0)


    def getIcon ( self, iconSize ):
        if not self.iconName:
            return None

        icon = iconManager.getIcon( self.iconName, iconSize )
        if not icon:
            icon = iconManager.getIcon( "application-default-icon", iconSize )

        return icon

    def setIcon ( self, iconName ):
        self.iconName = iconName
        self.iconChanged()

    # IconTheme changed, setup new button icons
    def themeChanged( self, theme ):
        self.iconChanged()

    def iconChanged( self ):
        icon = self.getIcon( self.iconSize )
        self.buttonImage.clear()
        if icon:
            self.buttonImage.set_from_pixbuf( icon )
            self.buttonImage.set_size_request( -1, -1 )
            del icon
        else:
            #[iW, iH ] = iconManager.getIconSize( self.iconSize )
            self.buttonImage.set_size_request( self.iconSize, self.iconSize  )

    def setIconSize( self, size ):
        self.iconSize = size
        icon = self.getIcon( self.iconSize )
        self.buttonImage.clear()
        if icon:
            self.buttonImage.set_from_pixbuf( icon )
            self.buttonImage.set_size_request( -1, -1 )
            del icon
        elif self.iconSize:
            #[ iW, iH ] = iconManager.getIconSize( self.iconSize )
            self.buttonImage.set_size_request( self.iconSize, self.iconSize  )

class TargetEntry(Structure):
     _fields_ = [("target", c_char_p),
                 ("flags", c_int),
                 ("info", c_int)]

class ApplicationLauncher( easyButton ):

    def __init__( self, desktopFile, iconSize):

        if isinstance( desktopFile, xdg.Menu.MenuEntry ):
            desktopItem = desktopFile.DesktopEntry
            desktopFile = desktopItem.filename
            self.appDirs = desktop.desktopFile.AppDirs
        elif isinstance( desktopFile, xdg.Menu.DesktopEntry ):
            desktopItem = desktopFile
            desktopFile = desktopItem.filename
            self.appDirs = [ os.path.dirname( desktopItem.filename ) ]
        else:
            desktopItem = xdg.DesktopEntry.DesktopEntry( desktopFile )
            self.appDirs = [ os.path.dirname( desktopFile ) ]

        self.desktopFile = desktopFile
        self.startupMonitorId = 0

        self.loadDesktopEntry( desktopItem )

        self.desktopEntryMonitors = []

        base = os.path.basename( self.desktopFile )
        for dir in self.appDirs:
            self.desktopEntryMonitors.append( filemonitor.addMonitor( os.path.join(dir, base) , self.onDesktopEntryFileChanged ) )

        easyButton.__init__( self, self.appIconName, iconSize )
        self.setupLabels()

        # Drag and Drop
        self.connectSelf( "drag-data-get", self.dragDataGet )

        array = TargetEntry * 2
        targets = array(( "text/plain", 0, 100 ), ( "text/uri-list", 0, 101 ))
        gtk.gtk_drag_source_set(hash(self), Gdk.ModifierType.BUTTON1_MASK, targets, 2, Gdk.DragAction.COPY)

        icon = self.getIcon( Gtk.IconSize.DND )
        if icon:
            gtk.gtk_drag_source_set_icon_pixbuf( hash(self), hash(icon) )
            del icon

        self.connectSelf( "focus-in-event", self.onFocusIn )
        self.connectSelf( "focus-out-event", self.onFocusOut )
        self.connectSelf( "enter-notify-event", self.onEnterNotify )
        self.connectSelf( "clicked", self.execute )



    def loadDesktopEntry( self, desktopItem ):
        try:
            self.appName = desktopItem.getName()
            self.appGenericName = desktopItem.getGenericName()
            self.appComment = desktopItem.getComment()
            self.appExec = desktopItem.getExec()
            self.appIconName = desktopItem.getIcon()
            self.appCategories = desktopItem.getCategories()
            self.appGnomeDocPath = desktopItem.get( "X-MATE-DocPath" ) or ""
            self.useTerminal = desktopItem.getTerminal()

            if not self.appGnomeDocPath:
                self.appKdeDocPath      = desktopItem.getDocPath() or ""

            self.appName            = self.appName.strip()
            self.appGenericName     = self.appGenericName.strip()
            self.appComment         = self.appComment.strip()

            basename = os.path.basename( self.desktopFile )
            self.startupFilePath = os.path.join( os.path.expanduser("~"), ".config", "autostart", basename )
            if self.startupMonitorId:
                filemonitor.removeMonitor( self.startupMonitorId  )
            self.startupMonitorId = filemonitor.addMonitor( self.startupFilePath, self.startupFileChanged )
            #self.inStartup = os.path.exists( self.startupFilePath )

        except Exception, e:
            print e
            self.appName            = ""
            self.appGenericName     = ""
            self.appComment         = ""
            self.appExec            = ""
            self.appIconName                = ""
            self.appCategories      = ""
            self.appDocPath         = ""
            self.startupMonitorId   = 0


    def onFocusIn( self, widget, event ):
        self.set_relief( Gtk.ReliefStyle.HALF )

    def onFocusOut( self, widget, event ):
        self.set_relief( Gtk.ReliefStyle.NONE )

    def onEnterNotify( self, widget, event ):
        self.grab_focus()

    def setupLabels( self ):
        self.addLabel( self.appName )
            
    def filterText( self, text ):
        keywords = text.lower().split()
        appName = self.strip_accents(self.appName.lower())
        appGenericName = self.strip_accents(self.appGenericName.lower())
        appComment = self.strip_accents(self.appComment.lower())
        appExec = self.strip_accents(self.appExec.lower())
        for keyword in keywords:
            keyw = self.strip_accents(keyword)
            if keyw != "" and appName.find( keyw ) == -1 and appGenericName.find( keyw ) == -1 and appComment.find( keyw ) == -1 and appExec.find( keyw ) == -1:
                self.hide()
                return False

        self.show()
        return True

    def strip_accents(self, string):
        import unicodedata
        return unicodedata.normalize('NFKD', unicode(string)).encode('UTF8', 'ignore')


    def getTooltip( self ):
        tooltip = self.appName
        if self.appComment != "" and self.appComment != self.appName:
            tooltip = tooltip + "\n" + self.appComment

        return tooltip



    def dragDataGet( self, widget, context, selection, targetType, eventTime ):
        print "drag data get"
        if targetType == 100: # text/plain
            selection.set_text( "'" + self.desktopFile + "'", -1 )
        elif targetType == 101: # text/uri-list
            if self.desktopFile[0:7] == "file://":
                selection.set_uris( [ self.desktopFile ] )
            else:
                selection.set_uris( [ "file://" + self.desktopFile ] )

    def execute( self, *args ):
        if self.appExec:
            if self.useTerminal:
                cmd = "x-terminal-emulator -e \"" + self.appExec + "\""
                Execute(cmd)
            else:
                Execute(self.appExec)

    def uninstall (self, *args ):
        Execute("gksu /usr/lib/linuxmint/mintMenu/mintRemove.py " + self.desktopFile)

    # IconTheme changed, setup new icons for button and drag 'n drop
    def iconChanged( self ):
        easyButton.iconChanged( self )

        icon = self.getIcon( Gtk.IconSize.DND )
        if icon:
            self.drag_source_set_icon_pixbuf( icon )
            del icon

    def startupFileChanged( self, *args ):
        self.inStartup = os.path.exists( self.startupFilePath )

    def addToStartup( self ):
        startupDir = os.path.join( os.path.expanduser("~"), ".config", "autostart" );
        if not os.path.exists( startupDir ):
            os.makedirs( startupDir )

        shutil.copyfile( self.desktopFile, self.startupFilePath )

        # Remove %u, etc. from Exec entry, because gnome will not replace them when it starts the app
        item = matedesktop.item_new_from_uri( self.startupFilePath, matedesktop.LOAD_ONLY_IF_EXISTS )
        if item:
            r = re.compile("%[A-Za-z]");
            tmp = r.sub("", item.get_string( matedesktop.KEY_EXEC ) ).strip()
            item.set_string( matedesktop.KEY_EXEC, tmp )
            item.save( self.startupFilePath, 0 )

    def removeFromStartup( self ):
        if os.path.exists( self.startupFilePath ):
            os.remove( self.startupFilePath )

    def addToFavourites( self ):
        favouritesDir = os.path.join( os.path.expanduser("~"), ".linuxmint", "mintMenu", "applications" );
        if not os.path.exists( favouritesDir ):
            os.makedirs( favouritesDir )

        shutil.copyfile( self.desktopFile, self.favouritesFilePath )

    def removeFromFavourites( self ):
        if os.path.exists( self.favouritesFilePath ):
            os.remove( self.favouritesFilePath )

    def isInStartup( self ):
        #return self.inStartup
        return os.path.exists( self.startupFilePath )

    def onDestroy( self, widget ):
        easyButton.onDestroy( self, widget )
        if self.startupMonitorId:
            filemonitor.removeMonitor( self.startupMonitorId )
        for id in self.desktopEntryMonitors:
            filemonitor.removeMonitor( id )

    def onDesktopEntryFileChanged( self ):
        exists = False
        base = os.path.basename( self.desktopFile )
        for dir in self.appDirs:
            if os.path.exists( os.path.join( dir, base ) ):
                print os.path.join( dir, base ), self.desktopFile
                self.loadDesktopEntry( xdg.DesktopEntry.DesktopEntry( os.path.join( dir, base ) ) )
                for child in self.labelBox:
                    child.destroy()

                self.iconName = self.appIconName

                self.setupLabels()
                self.iconChanged()
                exists = True
                break

        if not exists:
            # FIXME: What to do in this case?
            self.destroy()

class MenuApplicationLauncher( ApplicationLauncher ):

    def __init__( self, desktopFile, iconSize, category, showComment, highlight=False ):

        self.showComment = showComment
        self.appCategory = category
        self.highlight = highlight

        ApplicationLauncher.__init__( self, desktopFile, iconSize )


    def filterCategory( self, category ):
        if self.appCategory == category or category == "":
            self.show()
        else:
            self.hide()

    def setupLabels( self ):        
        appName = self.appName
        appComment = self.appComment
        if self.highlight: 
            try:
                #color = self.labelBox.rc_get_style().fg[ Gtk.StateType.SELECTED ].to_string()                
                #if len(color) > 0 and color[0] == "#":
                    #appName = "<span foreground=\"%s\"><b>%s</b></span>" % (color, appName);
                    #appComment = "<span foreground=\"%s\"><b>%s</b></span>" % (color, appComment);
                    #appName = "<b>%s</b>" % (appName);
                    #appComment = "<b>%s</b>" % (appComment);
                #else:
                    #appName = "<b>%s</b>" % (appName);
                    #appComment = "<b>%s</b>" % (appComment);
                appName = "<b>%s</b>" % (appName);
                appComment = "<b>%s</b>" % (appComment);
            except Exception, detail:
                print detail
                pass
        
        if self.showComment and self.appComment != "":
            if self.iconSize <= 2:
                self.addLabel( '<span size="small">%s</span>' % appName)
                self.addLabel( '<span size="x-small">%s</span>' % appComment)
            else:
                self.addLabel( appName )
                self.addLabel( '<span size="small">%s</span>' % appComment)
        else:
            self.addLabel( appName )
    
    def execute( self, *args ):        
        self.highlight = False
        for child in self.labelBox:
            child.destroy()
        self.setupLabels()
        return super(MenuApplicationLauncher, self).execute(*args)

    def setShowComment( self, showComment ):
        self.showComment = showComment
        for child in self.labelBox:
            child.destroy()
        self.setupLabels()

class FavApplicationLauncher( ApplicationLauncher ):

    def __init__( self, desktopFile, iconSize, swapGeneric = False ):

        self.swapGeneric = swapGeneric

        ApplicationLauncher.__init__( self, desktopFile, iconSize )

    def setupLabels( self ):
        if self.appGenericName:
            if self.swapGeneric:
                self.addLabel( '<span weight="bold">%s</span>' % self.appName )
                self.addLabel( self.appGenericName )
            else:
                self.addLabel( '<span weight="bold">%s</span>' % self.appGenericName )
                self.addLabel( self.appName )
        else:
            self.addLabel( '<span weight="bold">%s</span>' % self.appName )
            if self.appComment != "":
                self.addLabel( self.appComment )
            else:
                self.addLabel ( "" )
                
    def setSwapGeneric( self, swapGeneric ):
        self.swapGeneric = swapGeneric
        for child in self.labelBox:
            child.destroy()

        self.setupLabels()


class CategoryButton( easyButton ):

    def __init__( self, iconName, iconSize, labels , f ):
        easyButton.__init__( self, iconName, iconSize, labels )
        self.filter = f


iconManager = IconManager()
