#!/usr/bin/python2

import os
from gi.repository import Gio

def RemoveArgs(Execline):
    if isinstance(Execline, list):
        Execline = ' '.join(Execline)

    Specials = ["%f", "%F", "%u", "%U", "%d", "%D", "%n", "%N", "%i", "%c", "%k", "%v", "%m", "%M",
                "STARTED_FROM_MENU=yes"]
    for spec in Specials:
        if spec in Execline:
            Execline = Execline.replace(spec, "")

    return Execline

# Actually execute the command
def Execute(cmd , commandCwd=None, desktopFile=None):
    if desktopFile:
        launcher = Gio.DesktopAppInfo.new_from_filename(desktopFile)
        retval = launcher.launch_uris()

        return retval

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
    except Exception as err:
        print err
        return False
