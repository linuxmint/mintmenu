#!/usr/bin/python

import threading

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GObject, GLib

from Xlib import X
from Xlib.display import Display


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
        self.windows.append(window)

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
                        if (Gtk.MAJOR_VERSION, Gtk.MINOR_VERSION) >= (3, 20):
                            pdevice = Gdk.Display.get_default().get_default_seat().get_pointer()
                        else:
                            pdevice = Gdk.Display.get_default().get_device_manager().get_client_pointer()
                        p = self.get_window().get_device_position(pdevice)
                        g = self.get_size()

                        if p.x >= 0 and p.y >= 0 and p.x <= g.width and p.y <= g.height:
                            break
                    else:
                        # Is outside, so activate
                        GLib.idle_add(self.idle)
                    self.display.allow_events(X.ReplayPointer, event.time)
                else:
                    self.display.allow_events(X.ReplayPointer, X.CurrentTime)
            except Exception as e:
                print("Unexpected error:", e)

    def stop(self):
        self.running = False
        self.root.ungrab_button(X.AnyButton, X.AnyModifier)
        self.display.close()
