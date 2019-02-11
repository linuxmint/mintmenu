#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

import gi
gi.require_version("Gtk", "3.0")
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gdk, GLib, Vte

class IntegratedTerminal(Gtk.Window):

    def __init__(self, command, title=None, shell=None, cwd=None, width=600, height=500):
        try:
            self.terminal=Vte.Terminal()
            self.terminal.set_scrollback_lines(-1)
            # Setting the font doesn't work for some reason, let's leave it
            # self.terminal.set_font(Pango.FontDescription(string='Monospace'))
            self.command = command
            self.ready = False
            self.output_handler = self.terminal.connect("cursor-moved",
                self.on_cursor_moved)
            # apparently Vte.Terminal.spawn_sync() is deprecated in favour of the
            # non-existent Vte.Terminal.spawn_async()...
            self.terminal.spawn_sync(
                    Vte.PtyFlags.DEFAULT, # pty_flags
                    cwd or os.environ.get("HOME"), # working_directory
                    shell or [os.environ.get("SHELL")], # argv
                    [], # envv
                    GLib.SpawnFlags.DO_NOT_REAP_CHILD, # spawn_flags
                    None, # child_setup
                    None, # child_setup_data
                    None # cancellable
                    )
        except Exception as e:
            self.close()
            raise Exception(e)

        Gtk.Window.__init__(self, title=title or "mintMenu Integrated Terminal")
        self.set_icon_name("utilities-terminal")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_size_request(width, height)
        self.scrolled_window.add(self.terminal)
        box.pack_start(self.scrolled_window, False, True, 0)
        self.add(box)
        self.connect("key-press-event", self.on_key_press_event)
        self.terminal.connect("child-exited", self.exit)
        self.terminal.connect("eof", self.exit)
        self.terminal.set_rewrap_on_resize(True)

    def on_cursor_moved(self, terminal):
        if not self.ready:
            # we have to run the command on a callback because the
            # spawn_sync() method doesn't wait for the shell to load,
            # so instead we have to wait for the shell to create a prompt
            self.ready = True
            # if we don't show the terminal once after this it won't
            # always receive output, so we show it and hide it again right
            # away. Whatever works...
            self.show_all()
            self.hide()
            # Now we can go:
            command = "%s\n" % self.command
            self.terminal.feed_child(command, len(command))
            return
        # Unfortunately we cannot guarantee that the command is on the first
        # line (the shell may display somethinge else first), so we have to
        # search for it:
        x, y = terminal.get_cursor_position()
        contents, dummy = terminal.get_text_range(0, 0, x, y, None, None)
        lines = contents.split("\n")
        prefix = ""
        command_found = False
        for line in lines:
            if not line:
                continue
            if command_found:
                if not line.lstrip(prefix):
                    # we got a command prompt, exit
                    self.exit()
                    break
                # the command generated output, show the terminal
                terminal.disconnect(self.output_handler)
                self.show_all()
                break
            if self.command in line:
                # this is our command line
                prefix = line.split(self.command, 1)[0]
                command_found = True

    def on_key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.exit()

    def exit(self, *args):
        # Gtk.main_quit()
        self.close()
