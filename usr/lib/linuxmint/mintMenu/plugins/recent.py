#!/usr/bin/python2

import os
import subprocess

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import plugins.recentHelper as RecentHelper
from plugins.easygsettings import EasyGSettings
from plugins.execute import Execute


class pluginclass:
    """ This is the main class for the plugin.
        It MUST be named pluginclass
    """

    def __init__(self, mintMenuWin, toggleButton, de):

        self.Win = mintMenuWin
        self.toggleButton = toggleButton
        self.de = de

        self.builder = Gtk.Builder()
        #The Glade file for the plugin
        self.builder.add_from_file(os.path.join(os.path.dirname(__file__), "recent.glade"))

        #Set 'window' property for the plugin (Must be the root widget)
        self.window = self.builder.get_object("window1")

        #Set 'heading' property for plugin
        self.heading = _("Recently used")

        #This should be the first item added to the window in glade
        self.content_holder = self.builder.get_object("eventbox1")

        self.recentBox = self.builder.get_object("RecentBox")
        self.recentAppBox = self.builder.get_object("RecentApps")
        RecentHelper.recentAppBox = self.recentAppBox

        #self.recentApps = []

        self.recentVBox = self.builder.get_object("vbox1")

        #Specify plugin width
        self.width = 250

        #Plugin icon
        self.icon = 'mate-folder.png'

        self.settings = EasyGSettings("com.linuxmint.mintmenu.plugins.recent")

        self.settings.notifyAdd('height', self.RegenPlugin)
        self.settings.notifyAdd('width', self.RegenPlugin)
        self.settings.notifyAdd('num-recent-docs', self.RegenPlugin)
        self.settings.notifyAdd('recent-font-size', self.RegenPlugin)

        self.appSettings = EasyGSettings("com.linuxmint.mintmenu.plugins.applications")
        self.appSettings.notifyAdd("icon-size", self.RegenPlugin)

        self.FileList=[]
        self.RecManagerInstance = Gtk.RecentManager.get_default()
        self.recentManagerId = self.RecManagerInstance.connect("changed", self.DoRecent)

        self.RegenPlugin()
        self.builder.get_object("RecentTabs").set_current_page(0)

        #Connect event handlers
        self.builder.get_object("ClrBtn").connect("clicked", self.clrmenu)

    @staticmethod
    def wake():
        return

    def destroy(self):
        self.recentBox.destroy()
        self.recentVBox.destroy()
        self.builder.get_object("RecentTabs").destroy()
        self.builder.get_object("ClrBtn").destroy()
        self.content_holder.destroy()
        self.settings.notifyRemoveAll()
        if self.recentManagerId:
            self.RecManagerInstance.disconnect(self.recentManagerId)

    def RegenPlugin(self, *args, **kargs):
        self.GetGSettingsEntries()

    def GetGSettingsEntries(self):
        self.recenth = self.settings.get('int', 'height')
        self.recentw = self.settings.get('int', 'width')
        self.numentries = self.settings.get('int', 'num-recent-docs')
        RecentHelper.numentries = self.numentries

        self.recentfontsize = self.settings.get('int', 'recent-font-size')

        # Hide vertical dotted separator
        self.hideseparator = self.settings.get("bool", "hide-separator")
        # Plugin icon
        self.icon = self.settings.get("string", 'icon')
        # Allow plugin to be minimized to the left plugin pane
        self.sticky = self.settings.get("bool", "sticky")
        self.minimized = self.settings.get("bool", "minimized")
        RecentHelper.iconSize = self.appSettings.get("int", "icon-size")
        self.RebuildPlugin()

    def SetHidden(self, minimized):
        if minimized:
            self.settings.set("bool", "minimized", True)
        else:
            self.settings.set("bool", "minimized", False)

    def RebuildPlugin(self):
        self.content_holder.set_size_request(self.recentw, self.recenth)
        self.DoRecent()

    def DoRecent(self, *args, **kargs):
        for i in self.recentBox.get_children():
            i.destroy()

        self.recentVBox.set_size_request(self.recentw, self.recenth)
        if len(self.recentBox.get_children()) < self.numentries:
            n=len(self.recentBox.get_children())-1
        else:
            n=self.numentries-1
        while n >= 0:
            self.recentBox.remove(self.recentBox.get_children()[n])
            n-=1

        self.FileList, self.IconList = self.GetRecent()
        loc = 0
        for Name in self.FileList:
            if Name != None:
                self.AddRecentBtn(Name, self.IconList[loc])
            loc = loc + 1

        RecentHelper.doRecentApps()

        return True

    def clrmenu(self, *args, **kargs):
        self.RecManagerInstance.purge_items()
        self.DoRecent()

    def AddRecentBtn(self, Name, RecentImage):
        DispName=os.path.basename(Name)

        AButton = Gtk.Button("", "ok", True)
        AButton.remove(AButton.get_children()[0])
        AButton.set_size_request(200, -1)
        AButton.set_relief(Gtk.ReliefStyle.NONE)
        AButton.connect("clicked", self.callback, Name)
        AButton.show()

        Box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)

        ButtonIcon = Gtk.Image()
        ButtonIcon.set_size_request(20, -1)
        ButtonIcon.set_from_pixbuf(RecentImage)
        Box1.add(ButtonIcon)

        Label1 = Gtk.Label(DispName)
        Label1.set_ellipsize(3)
        Box1.add(Label1)

        AButton.add(Box1)
        AButton.show_all()

        self.recentBox.pack_start(AButton, False, True, 0)

    def callback(self, widget, filename):
        self.Win.hide()

        try:
            subprocess.check_call(["xdg-open", filename])
        except subprocess.CalledProcessError:
            dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, _("The file or location could not be opened."))
            dialog.set_title("mintMenu")
            dialog.run()
            dialog.destroy()

    def GetRecent(self, *args, **kargs):
        FileString=[]
        IconString=[]
        RecentInfo=self.RecManagerInstance.get_items()
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
        return FileString, IconString

    def ButtonClicked(self, widget, event, Exec):
        self.press_x = event.x
        self.press_y = event.y
        self.Exec = Exec

    def ButtonReleased(self, w, ev, ev2):
        if ev.button == 1:
            if not hasattr(self, "press_x") or \
                    not w.drag_check_threshold(int(self.press_x),
                                                int(self.press_y),
                                                int(ev.x),
                                                int(ev.y)):
                if self.Win.pinmenu == False:
                    self.Win.wTree.get_widget("window1").hide()
                if "applications" in self.Win.plugins:
                    self.Win.plugins["applications"].wTree.get_widget("entry1").grab_focus()
                Execute(w, self.Exec)

    @staticmethod
    def do_plugin():
        return
