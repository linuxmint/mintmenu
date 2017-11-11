#!/usr/bin/python2

import gi
gi.require_version("Gtk", "3.0")

import os
import string
from user import home
from easyfiles import *
from easybuttons import *

recentApps = []
mintMenuWin = None
recentAppBox = None
numentries = 10
iconSize = 16

def recentAppsAdd( recentAppsButton ):
    if recentAppsButton:

        recentApps.insert(0, recentAppsButton )

        counter = 0
        for recentApp in recentApps:
            if counter != 0 and ( recentApp.desktopFile == recentAppsButton.desktopFile or counter >= numentries ):
                del recentApps[counter]
            counter = counter + 1

def recentAppsSave():
    try:
        if (not os.path.exists(home + "/.linuxmint/mintMenu/recentApplications.list")):
            os.system("touch " + home + "/.linuxmint/mintMenu/recentApplications.list")
        recentAppListFile = open( os.path.join( os.path.expanduser( "~"), ".linuxmint", "mintMenu", "recentApplications.list" ) , "w" )

        for recentApp in recentApps:
            if not hasattr(recentApp, "type") or recentApp.type == "location":
                recentAppListFile.write( "location:" + recentApp.desktopFile + "\n" )
            else:
                recentAppListFile.write( recentApp.type + "\n" )

        recentAppListFile.close( )
    except Exception, e:
        print e
        msgDlg = Gtk.MessageDialog( None, gtk.DialogFlags.MODAL, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, _("Couldn't save recent apps. Check if you have write access to ~/.linuxmint/mintMenu")+"\n(" + e.__str__() + ")" )
        msgDlg.run();
        msgDlg.destroy();

def recentAppBuildLauncher( location ):
    try:
        ButtonIcon = None
        # For Folders and Network Shares
        location = string.join( location.split( "%20" ) )

        if location.startswith( "file" ):
            ButtonIcon = "mate-fs-directory"

        if location.startswith( "smb" ) or location.startswith( "ssh" ) or location.startswith( "network" ):
            ButtonIcon = "mate-fs-network"

        #For Special locations
        if location == "x-nautilus-desktop:///computer":
            location = "/usr/share/applications/nautilus-computer.desktop"
        elif location == "x-nautilus-desktop:///home":
            location =  "/usr/share/applications/nautilus-home.desktop"
        elif location == "x-nautilus-desktop:///network":
            location = "/usr/share/applications/network-scheme.desktop"
        elif location.startswith( "x-nautilus-desktop:///" ):
            location = "/usr/share/applications/nautilus-computer.desktop"

        if location.startswith( "file://" ):
            location = location[7:]
        appButton = ApplicationLauncher( location, iconSize)

        if appButton.appExec:
            appButton.show()
            appButton.connect( "clicked", applicationButtonClicked )
            appButton.type = "location"
            return appButton
    except Exception, e:
        print u"File in recentapp not found: '" + location + "'", e

    return None


def buildRecentApps():
    del recentApps[:]
    try:
        if (not os.path.exists(home + "/.linuxmint/mintMenu/recentApplications.list")):
            os.system("touch " + home + "/.linuxmint/mintMenu/recentApplications.list")
        recentAppListFile = open( os.path.join( os.path.expanduser( "~"), ".linuxmint", "mintMenu", "recentApplications.list" ) , "r" )

        recentApplicationsList = recentAppListFile.readlines()

        for app in recentApplicationsList :
            app = app.strip()

            if app[0:9] == "location:":
                appButton = recentAppBuildLauncher( app[9:] )
            else:
                if ( app.endswith( ".desktop" ) ):
                    appButton = recentAppBuildLauncher( app )
                else:
                    appButton = None

            if appButton:
                recentApps.append( appButton )
    except Exception, e:
        print e
    return recentApps

def doRecentApps():
    for i in recentAppBox.get_children():
        i.destroy()

    # recent apps
    buildRecentApps()
    for AButton in recentApps:
        
        AButton.set_size_request( 200, -1 )
        AButton.set_relief( Gtk.ReliefStyle.NONE )

        recentAppBox.pack_start( AButton, False, True, 0 )

    return True

def applicationButtonClicked( widget ):
    mintMenuWin.hide()
    recentAppsAdd(widget)
    recentAppsSave()
    doRecentApps()
