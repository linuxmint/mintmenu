#!/usr/bin/python

import apt
import sys

try:
	cache = apt.Cache()	
	pkg = cache["mintmenu"]
	print pkg.installedVersion
except:
	pass


