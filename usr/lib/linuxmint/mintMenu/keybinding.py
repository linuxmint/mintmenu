# -*- coding: utf-8; -*-
# Copyright (C) 2013  Özcan Esen <ozcanesen@gmail.com>
# Copyright (C) 2008  Luca Bruno <lethalman88@gmail.com>
#
# This a slightly modified version of the globalkeybinding.py file which is part of FreeSpeak.
#   
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell   
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#   
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#   
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER    
# DEALINGS IN THE SOFTWARE.

import gi
gi.require_version("Gtk", "2.0")

from Xlib.display import Display
from Xlib import X, error
from gi.repository import Gtk, Gdk, GObject, GLib
import threading
import ctypes
from ctypes import *
import capi

gdk = CDLL("libgdk-x11-2.0.so.0")

class GlobalKeyBinding(GObject.GObject, threading.Thread):
    __gsignals__ = {
        'activate':(GObject.SIGNAL_RUN_LAST, None,()),
        }

    def __init__(self):
        GObject.GObject.__init__(self)
        threading.Thread.__init__(self)
        self.setDaemon(True)

        self.keymap = capi.get_widget (gdk.gdk_keymap_get_default())
        self.display = Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        self.ignored_masks = self.get_mask_combinations(X.LockMask | X.Mod2Mask | X.Mod5Mask)
        self.map_modifiers()

    def map_modifiers(self):
        gdk_modifiers =(Gdk.ModifierType.CONTROL_MASK, Gdk.ModifierType.SHIFT_MASK, Gdk.ModifierType.MOD1_MASK,
                         Gdk.ModifierType.MOD2_MASK, Gdk.ModifierType.MOD3_MASK, Gdk.ModifierType.MOD4_MASK, Gdk.ModifierType.MOD5_MASK,
                         Gdk.ModifierType.SUPER_MASK, Gdk.ModifierType.HYPER_MASK)
        self.known_modifiers_mask = 0
        for modifier in gdk_modifiers:
            if "Mod" not in Gtk.accelerator_name(0, modifier):
                self.known_modifiers_mask |= modifier

    def grab(self, key):
        Gdk.threads_enter()
        accelerator = key
        Gdk.threads_leave()
        keyval, modifiers = Gtk.accelerator_parse(accelerator)
        print keyval, modifiers
        # if not accelerator or (not keyval and not modifiers):
        #     self.keycode = None
        #     self.modifiers = None
        #     print "what"
        #     return
        count = c_int()
        keys = KeymapKey * 10
        self.keycode = gdk.gdk_keymap_get_entries_for_keyval(hash(self.keymap), keyval, byref(keys), byref(count))
        #self.keycode= self.keymap.get_entries_for_keyval(keyval)[0].keycode
        print keys
        self.modifiers = int(modifiers)

        catch = error.CatchError(error.BadAccess)
        for ignored_mask in self.ignored_masks:
            mod = modifiers | ignored_mask
            result = self.root.grab_key(self.keycode, mod, True, X.GrabModeAsync, X.GrabModeSync, onerror=catch)
        self.display.sync()
        if catch.get_error():
            return False
        return True

    def ungrab(self, key):
        if self.keycode:
            self.root.ungrab_key(self.keycode, X.AnyModifier, self.root)

    def get_mask_combinations(self, mask):
        return [x for x in xrange(mask+1) if not (x & ~mask)]

    def idle(self):
        print "caught"
        Gdk.threads_enter()
        self.emit("activate")
        Gdk.threads_leave()
        return False

    def run(self):
        self.running = True
        wait_for_release = False
        while self.running:
            event = self.display.next_event()
            self.current_event_time = event.time
            if event.detail == self.keycode and event.type == X.KeyPress and not wait_for_release:
                modifiers = event.state & self.known_modifiers_mask
                if modifiers == self.modifiers:
                    wait_for_release = True
                    self.display.allow_events(X.AsyncKeyboard, event.time)
                else:
                    self.display.allow_events(X.ReplayKeyboard, event.time)
            elif event.detail == self.keycode and wait_for_release:
                if event.type == X.KeyRelease:
                    wait_for_release = False
                    GLib.idle_add(self.idle)
                self.display.allow_events(X.AsyncKeyboard, event.time)
            else:
                self.display.allow_events(X.ReplayKeyboard, event.time)

    def stop(self):
        self.running = False
        self.ungrab()
        self.display.close()

class KeymapKey(Structure):
     _fields_ = [("keycode", c_uint),
                 ("group", c_int),
                 ("level", c_int)]

class KeymapKeyMany(Structure):
    _fields_ = [("keymap", KeymapKey*10)]