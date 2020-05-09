#!/usr/bin/python3

import os
from gi.repository import Gio, GLib, Gdk


def RemoveArgs(Execline):
    if isinstance(Execline, list):
        Execline = ' '.join(Execline)

    Specials = ["%f", "%F", "%u", "%U", "%d", "%D", "%n", "%N", "%i", "%c", "%k", "%v", "%m", "%M",
                "STARTED_FROM_MENU=yes"]
    for spec in Specials:
        if spec in Execline:
            Execline = Execline.replace(spec, "")

    return Execline

def dummy_child_watch (pid, status, data):
  # Do nothing, this is just to ensure we don't double fork
  # and break pkexec: https://bugzilla.gnome.org/show_bug.cgi?id=675789
  pass

def gather_pid_callback(appinfo, pid, data):
    GLib.child_watch_add(pid, dummy_child_watch, None)

# Actually execute the command
def Execute(cmd , commandCwd=None, desktopFile=None, offload=False):
    if desktopFile:
        launcher = Gio.DesktopAppInfo.new_from_filename(desktopFile)
        context = Gdk.Display.get_default().get_app_launch_context()
        if offload:
            print("Offloading '%s' to discrete gpu." % launcher.get_name());

            context.setenv("__NV_PRIME_RENDER_OFFLOAD", "1")
            context.setenv("__GLX_VENDOR_LIBRARY_NAME", "nvidia");

        try:
            retval = launcher.launch_uris_as_manager(uris=[],
                                                     launch_context=context,
                                                     spawn_flags=GLib.SpawnFlags.SEARCH_PATH|GLib.SpawnFlags.DO_NOT_REAP_CHILD,
                                                     user_setup=None, user_setup_data=None,
                                                     pid_callback=gather_pid_callback, pid_callback_data=None)
            return retval
        except GLib.Error as e:
            print("Error launching %s: %s" % (launcher.get_name(), e.message))
            return False

    cwd = os.path.expanduser("~")

    if commandCwd:
        tmpCwd = os.path.expanduser(commandCwd)
        if (os.path.exists(tmpCwd)):
            cwd = tmpCwd

    cmd = RemoveArgs(cmd)

    try:
        os.chdir(cwd)
        os.system(cmd + " &")
        return True
    except Exception as e:
        print(e)
        return False
