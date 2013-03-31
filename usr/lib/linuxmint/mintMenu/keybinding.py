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
gtk = CDLL("libgtk-x11-2.0.so.0")

class GlobalKeyBinding(GObject.GObject, threading.Thread):
    __gsignals__ = {
        'activate': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self):
        GObject.GObject.__init__ (self)
        threading.Thread.__init__ (self)
        self.setDaemon (True)

        self.keymap = capi.get_widget (gdk.gdk_keymap_get_default())
        self.display = Display()
        self.screen = self.display.screen()
        self.root = self.screen.root
        self.ignored_masks = self.get_mask_combinations(X.LockMask | X.Mod2Mask | X.Mod5Mask)
        self.map_modifiers()
        self.raw_keyval = None

    def is_hotkey(self, key, modifier):
        keymatch = False
        modmatch = False
        modint = int(modifier)
        if self.get_keycode(key) == self.keycode:
            keymatch = True
        for ignored_mask in self.ignored_masks:
            if self.modifiers | ignored_mask == modint | ignored_mask:
                modmatch = True
                break
        return keymatch and modmatch

    def map_modifiers(self):
        gdk_modifiers =(Gdk.ModifierType.CONTROL_MASK, Gdk.ModifierType.SHIFT_MASK, Gdk.ModifierType.MOD1_MASK,
                         Gdk.ModifierType.MOD2_MASK, Gdk.ModifierType.MOD3_MASK, Gdk.ModifierType.MOD4_MASK, Gdk.ModifierType.MOD5_MASK,
                         Gdk.ModifierType.SUPER_MASK, Gdk.ModifierType.HYPER_MASK)
        self.known_modifiers_mask = 0
        for modifier in gdk_modifiers:
            if "Mod" not in Gtk.accelerator_name(0, modifier):
                self.known_modifiers_mask |= modifier

    def get_keycode(self, keyval):
        count = c_int()
        array = (KeymapKey * 10)()
        keys = cast(array, POINTER(KeymapKey))
        gdk.gdk_keymap_get_entries_for_keyval(hash(self.keymap), keyval, byref(keys), byref(count))
        return keys[0].keycode

    def grab(self, key):
        accelerator = key
        keyval, modifiers = Gtk.accelerator_parse(accelerator)
        if not accelerator or (not keyval and not modifiers):
            self.keycode = None
            self.modifiers = None
            return False

        self.keycode = self.get_keycode(keyval)
        self.modifiers = int(modifiers)

        catch = error.CatchError(error.BadAccess)
        for ignored_mask in self.ignored_masks:
            mod = modifiers | ignored_mask
            result = self.root.grab_key(self.keycode, mod, True, X.GrabModeAsync, X.GrabModeSync, onerror=catch)
        self.display.sync()
        if catch.get_error():
            return False
        return True

    def ungrab(self):
        if self.keycode:
            self.root.ungrab_key(self.keycode, X.AnyModifier, self.root)

    def get_mask_combinations(self, mask):
        return [x for x in xrange(mask+1) if not (x & ~mask)]

    def idle(self):
        self.emit("activate")
        return False

    def activate(self):
        GLib.idle_add(self.run)

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


class KeybindingWidget(Gtk.HBox):
    __gsignals__ = {
        'accel-edited': (GObject.SignalFlags.RUN_LAST, None, ()),
    }
    def __init__(self, desc):
        super(KeybindingWidget, self).__init__()
        self.desc = desc
        self.label = Gtk.Label(desc)
        self.model = Gtk.ListStore(str, object)
        self.tree = Gtk.TreeView.new()
        self.tree.set_headers_visible(False)
        self.cell = Gtk.CellRendererAccel()
        self.cell.set_alignment(.5, .5)
        self.change_id = self.cell.connect('accel-edited', self.on_my_value_changed)
        self.cell.set_property('editable', True)
        self.cell.set_property('accel-mode', Gtk.CellRendererAccelMode.OTHER)
        col = Gtk.TreeViewColumn("col", self.cell, text=0)
        col.set_min_width(200)
        col.set_alignment(.5)
        self.tree.append_column(col)
        self.value = ""
        self.tree.set_model(self.model)
        self.model.append((self.value, self))
        if self.desc != "":
            self.pack_start(self.label, False, False, 0)
        shadow = Gtk.Frame()
        shadow.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        shadow.add(self.tree)
        self.pack_start(shadow, False, False, 2)

        self.combomodel = Gtk.ListStore(str, str)

        customs = (["Select a single modifier...", "x"],
                   ["Left Super",    "Super_L"      ],
                   ["Right Super",   "Super_R"      ],
                   ["Left Control",  "Control_L"    ],
                   ["Right Control", "Control_R"    ],
                   ["Left Alt",      "Alt_L"        ],
                   ["Right Alt",     "Alt_R"        ])

        first = None
        for option in customs:
            iter = self.combomodel.insert_before(None, None)
            self.combomodel.set_value(iter, 0, option[0])
            self.combomodel.set_value(iter, 1, option[1])
            if first is None:
                first = iter

        self.combo = Gtk.ComboBox.new_with_model(self.combomodel)   
        renderer_text = Gtk.CellRendererText()
        self.combo.pack_start(renderer_text, True)
        self.combo.add_attribute(renderer_text, "text", 0)

        self.combo.set_active_iter(first)
        self.combo.connect('changed', self.on_combo_changed)

        self.pack_start(self.combo, False, False, 0)

        self.show_all()

    def on_combo_changed(self, widget):
        tree_iter = widget.get_active_iter()
        if tree_iter != None:
            value = self.combomodel[tree_iter][1]
            self.set_val(value)
            self.emit("accel-edited")

    def on_my_value_changed(self, cell, path, keyval, mask, keycode):
        gtk.gtk_accelerator_name.restype = c_char_p
        accel_string = gtk.gtk_accelerator_name(keyval, mask)
        accel_string = accel_string.replace("<Mod2>", "")
        self.value = accel_string
        self.emit("accel-edited")

    def get_val(self):
        return self.value

    def set_val(self, value):
        self.cell.handler_block(self.change_id)
        self.value = value
        self.model.clear()
        self.model.append((self.value, self))
        self.cell.handler_unblock(self.change_id)
