#!/usr/bin/env python

import gi
gi.require_version("Gtk", "2.0")

from Xlib.display import Display
from Xlib import X, error
from gi.repository import Gtk, Gdk, GObject, GLib
import threading
import ctypes
from ctypes import *

gdk = CDLL("libgdk-x11-2.0.so.0")
gtk = CDLL("libgtk-x11-2.0.so.0")

class PointerMonitor(GObject.GObject, threading.Thread):
    __gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
    }
       
    def __init__(self):
        GObject.GObject.__init__ (self)
        threading.Thread.__init__ (self)
        self.setDaemon (True)
        self.display = Display()
        self.root = self.display.screen().root
        self.windows = []
        
    # Receives GDK windows
    def addWindowToMonitor(self, window):
        xWindow = self.display.create_resource_object("window", gdk.gdk_x11_drawable_get_xid(hash(window)))
        self.windows.append(xWindow)
            
    def grabPointer(self):
        self.root.grab_button(X.AnyButton, X.AnyModifier, True, X.ButtonPressMask, X.GrabModeSync, X.GrabModeAsync, 0, 0)
        self.display.flush()
        
    def ungrabPointer(self):
        self.root.ungrab_button(X.AnyButton, X.AnyModifier)
        self.display.flush()

    def idle(self):
        self.emit("activate")
        return False

    def activate(self):
        GLib.idle_add(self.run)
                    
    def run(self):
        self.running = True
        while self.running:
            event = self.display.next_event()
            try:
                if event.type == X.ButtonPress:
                    # Check if pointer is inside monitored windows
                    for w in self.windows:
                        p = w.query_pointer()
                        g = w.get_geometry()
                        if p.win_x >= 0 and p.win_y >= 0 and p.win_x <= g.width and p.win_y <= g.height:
                            break
                    else:
                        # Is outside, so activate
                        GLib.idle_add(self.idle)
                    self.display.allow_events(X.ReplayPointer, event.time)
                else:        
                    self.display.allow_events(X.ReplayPointer, X.CurrentTime)
            except Exception as e:
                print "Unexpected error: " + str(e)

    def stop(self):
        self.running = False
        self.root.ungrab_button(X.AnyButton, X.AnyModifier)
        self.display.close()
        
