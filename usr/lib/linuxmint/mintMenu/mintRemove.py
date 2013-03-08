#!/usr/bin/env python

import gi
gi.require_version("Gtk", "2.0")

from gi.repository import Gtk, Gdk

try:
    import sys
    import string
    import os
    import commands
    import threading
    import tempfile
    import gettext

except Exception, detail:
    print detail
    sys.exit(1)

from subprocess import Popen, PIPE

Gdk.threads_init()

# i18n
gettext.install("mintmenu", "/usr/share/linuxmint/locale")

class RemoveExecuter(threading.Thread):

    def __init__(self, window_id, package):
        threading.Thread.__init__(self)
        self.window_id = window_id
        self.package = package
    
    def execute(self, command):
        #print "Executing: " + command
        os.system(command)
        ret = commands.getoutput("echo $?")
        return ret

    def run(self):  
        removePackages = string.split(self.package)
        cmd = ["sudo", "/usr/sbin/synaptic", "--hide-main-window",  \
                "--non-interactive", "--parent-window-id", self.window_id]
        cmd.append("--progress-str")
        cmd.append("\"" + _("Please wait, this can take some time") + "\"")
        cmd.append("--finish-str")
        cmd.append("\"" + _("Application removed successfully") + "\"")
        f = tempfile.NamedTemporaryFile()
        for pkg in removePackages:
            f.write("%s\tdeinstall\n" % pkg)
            cmd.append("--set-selections-file")
            cmd.append("%s" % f.name)
            f.flush()
            comnd = Popen(' '.join(cmd), shell=True)
        returnCode = comnd.wait()
        f.close()
        Gtk.main_quit()
        sys.exit(0)
        
class mintRemoveWindow:

    def __init__(self, desktopFile):
        self.desktopFile = desktopFile  

            #Set the Glade file


        self.builder = Gtk.Builder()
        self.builder.add_from_file ("/usr/lib/linuxmint/mintMenu/mintRemove.glade")
        self.builder.get_object("main_window").set_icon_from_file("/usr/lib/linuxmint/mintMenu/icon.svg")
        self.builder.get_object("main_window").set_title("")
        self.builder.get_object("main_window").connect("destroy", self.giveUp)

        # Get the window socket (needed for synaptic later on)
        vbox = self.builder.get_object("vbox1")
        socket = Gtk.Socket()
        vbox.pack_start(socket, False, False, 0)
        socket.show()
        window_id = repr(socket.get_id())

        package = commands.getoutput("dpkg -S " + self.desktopFile)
        package = package[:package.find(":")]
        if package == "dpkg":
            warnDlg = Gtk.Dialog("MintMenu", None, 0,
                                  Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                  Gtk.STOCK_REMOVE, Gtk.ResponseType.OK)
            warnDlg.vbox.set_spacing(10)
            warnDlg.set_icon_from_file("/usr/share/linuxmint/logo.png")
            labelSpc = Gtk.Label(" ")
            warnDlg.vbox.pack_start(labelSpc, False, False, 0)
            labelSpc.show()
            warnText = "<b>" + _("No matching package found") + "</b>"
            infoText = _("Do you want to remove this menu entry?") + " (" + self.desktopFile + ")"
            label = Gtk.Label(warnText)
            lblInfo = Gtk.Label(infoText)
            label.set_use_markup(True)
            lblInfo.set_use_markup(True)
            warnDlg.vbox.pack_start(label)
            warnDlg.vbox.pack_start(lblInfo)
            label.show()
            lblInfo.show()
            response = warnDlg.run()
            if response == Gtk.ResponseType.OK :
                print "removing " + self.desktopFile + "*.desktop"
                os.system("rm -f " + self.desktopFile)
                os.system("rm -f " + self.desktopFile + "*.desktop")
            warnDlg.destroy()
            Gtk.main_quit()
            sys.exit(0)     

        self.builder.get_object("txt_name").set_text("<big><b>" + _("Remove %s?") % package + "</b></big>")
        self.builder.get_object("txt_name").set_use_markup(True)
            
        self.builder.get_object("txt_guidance").set_text(_("The following packages will be removed:"))
        
        treeview = self.builder.get_object("tree")
        column1 = Gtk.TreeViewColumn(_("Packages to be removed"))
        renderer = Gtk.CellRendererText()
        column1.pack_start(renderer, False)
        column1.add_attribute(renderer, "text", 0)
        treeview.append_column(column1)

        model = Gtk.ListStore(str)
        dependenciesString = commands.getoutput("apt-get -s -q remove " + package + " | grep Remv")
        dependencies = string.split(dependenciesString, "\n")
        for dependency in dependencies:
            dependency = dependency.replace("Remv ", "")
            model.append([dependency])
        treeview.set_model(model)
        treeview.show()


        self.builder.get_object("remove_button").connect ("clicked", self.MainButtonClicked, window_id, package)
        self.builder.get_object("cancel_button").connect ("clicked", self.giveUp)

        self.builder.get_object("main_window").show()


    def MainButtonClicked(self, widget, window_id, package):
        self.builder.get_object("main_window").window.set_cursor(Gdk.Cursor(Gdk.CursorType.WATCH))
        self.builder.get_object("main_window").set_sensitive(False)
        executer = RemoveExecuter(window_id, package)
        executer.start()
        return True

    def giveUp(self, widget):
        Gtk.main_quit()
        sys.exit(0)

if __name__ == "__main__":
    mainwin = mintRemoveWindow(sys.argv[1])
    Gtk.main()
    
