#!/usr/bin/python2

import urllib

def GetFilePath(uri):
    path = urllib.url2pathname(uri) # escape special chars
    path = path.strip('\r\n\x00') # remove \r\n and NULL

    # get the path to file
    if path.startswith('file://'): # nautilus, rox
        path = path[7:] # 7 is len('file://')
    return path
