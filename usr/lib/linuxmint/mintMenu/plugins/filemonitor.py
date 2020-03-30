#!/usr/bin/python3

import os
import os.path
import threading
import time
from gi.repository import GLib

try:
    import pyinotify
    hasInotify = True
except ImportError:
    hasInotify = False


if hasInotify:

    class FileMonitor(object):
        def __init__(self):
            self.monitorId = 0
            self.wm = pyinotify.WatchManager()
            self.wdds = {}
            self.callbacks = {}
            self.notifier = pyinotify.ThreadedNotifier(self.wm, self.fileChanged)
            self.notifier.setDaemon(True)
            self.notifier.start()


        def addMonitor(self, filename, callback, args = None):
            try:
                mask = pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY
                mId = self.wm.add_watch(filename, mask, rec = True)[filename]
                if mId >= 0:
                    self.callbacks[mId] = (callback, args)
            except:
                mId = 0
            return mId

        def removeMonitor(self, monitorId):
            if monitorId in self.callbacks:
                self.wm.rm_watch(monitorId)
                del self.callbacks[monitorId]

        def fileChanged(self, event):
            if event.wd in self.callbacks:
                #print event.path
                callback = self.callbacks[event.wd]
                if callback[1]:
                    GLib.idle_add(callback[0], callback[1])
                else:
                    GLib.idle_add(callback[0])

else:

    class _MonitoredFile(object):
        def __init__(self, filename, callback, monitorId, args):
            self.filename = filename
            self.callback = callback
            self.monitorId = monitorId
            self.args = args
            self.exists = os.path.exists(self.filename)
            if self.exists:
                self.mtime = os.stat(filename).st_mtime
            else:
                self.mtime = 0

        def hasChanged(self):
            if os.path.exists(self.filename):
                if not self.exists:
                    self.exists = True
                    self.mtime = os.stat(self.filename).st_mtime
                    return True
                else:
                    mtime = os.stat(self.filename).st_mtime
                    if mtime != self.mtime:
                        self.mtime = mtime
                        return True
            else:
                if self.exists:
                    self.exists = False
                    return True

            return False

    class MonitorThread(threading.Thread):
        def __init__(self, monitor):
            threading.Thread.__init__(self)
            self.monitor = monitor

        def run(self):
            while(1):
                self.monitor.checkFiles()
                time.sleep(1)

    class FileMonitor(object):
        def __init__(self):
            self.monitorId = 0
            self.monitoredFiles = []
            self.monitorThread = MonitorThread(self)
            self.monitorThread.setDaemon(True)
            self.monitorThread.start()

        def addMonitor(self, filename, callback, args = None):
            self.monitorId += 1
            self.monitoredFiles.append(_MonitoredFile(filename, callback, self.monitorId, args))
            return self.monitorId

        def removeMonitor(self, monitorId):
            for monitored in self.monitoredFiles:
                if monitorId == monitored.monitorId:
                    self.monitoredFiles.remove(monitored)
                    break

        def checkFiles(self):
            for monitored in self.monitoredFiles:
                if monitored.hasChanged():
                    if monitored.args:
                        GLib.idle_add(monitored.callback, monitored.args)
                    else:
                        GLib.idle_add(monitored.callback)

monitor = FileMonitor()
