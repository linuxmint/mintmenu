#!/usr/bin/env python

import os
import os.path
import urllib
"""
def TestForDir(dirname):
	if not os.path.exists( os.path.join(os.path.expanduser("~"), dirname ) ):
		os.makedirs( os.path.join( os.path.expanduser("~"), dirname) )

def TestForFiles(filename):
	if not os.path.exists( os.path.join( os.path.expanduser("~"), filename ) ):
		file = open( os.path.join( os.path.expanduser("~"), filename ),"w")
		file.close()

def FileExists(f):
	return os.path.exists(f)
"""

def GetFilePath(uri):
		path = urllib.url2pathname(uri) # escape special chars
		path = path.strip('\r\n\x00') # remove \r\n and NULL

		# get the path to file
		if path.startswith('file://'): # nautilus, rox
			path = path[7:] # 7 is len('file://')
		return path

"""
def ParseDesktopFile(DFile):
	# Get the locale
	lang = os.getenv("LANG")
	if lang:
		langArray = lang.split("_")
	else:
		langArray = [ None ]
	locale = langArray[0] or ""
	localeName = "Name[" + locale + "]="
	localeComment = "Comment[" + locale + "]="
	localeGenericName = "GenericName[" + locale + "]="
	PlaceName=PlaceComment=PlaceExec=PlaceIconName=GenericName=TerminalName=""
	FileData = []
	if FileExists(GetFilePath(DFile))==True:
		parseData = False
		openfile = open(GetFilePath(DFile), 'r')
		datalist = openfile.readlines()
		openfile.close()
		for i in datalist:
			i = i.strip('\r\n\x00')
			if len(i) != 0:
				if i[0] == "[" and i[-1] == "]":
					parseData = "[Desktop Entry]" == i
				elif parseData:
					if i[0:5] == "Name=":
						PlaceName = i[5:]
					elif i[0:9] == localeName:
						PlaceName = i[9:]
					elif i[0:8] == "Comment=":
						PlaceComment = i[8:]
					elif i[0:12] == localeComment:
						PlaceComment = i[12:]
					elif i[0:5] == "Exec=":
						PlaceExec = i[5:]
					elif i[0:5] == "Icon=":
						PlaceIconName = i[5:]
					elif i[0:12] == "GenericName=":
						GenericName = i[12:]
					elif i[0:16] == localeGenericName:
						GenericName = i[16:]
					elif i[0:9] == "Terminal=":
						TerminalName = i[9:]

		FileData.append(PlaceName)
		FileData.append(PlaceComment)
		FileData.append(PlaceExec)
		FileData.append(PlaceIconName)
		FileData.append(GenericName)
		FileData.append(TerminalName)
		return FileData

	return None

def WriteListFile(ListToAdd,ItemToAdd,mode):

	RecentapplicationsFile = open (os.path.join(os.path.expanduser("~"), ListToAdd),"r")
	RecentapplicationsList = RecentapplicationsFile.readlines()
	RecentapplicationsList.reverse()
	RecentapplicationsFile.close()

	if RecentapplicationsList != []:
		outfile = open (os.path.join(os.path.expanduser("~"), ListToAdd),mode)
		outfile.write(ItemToAdd+"\n")
		outfile.close()
	else:
		outfile = open (os.path.join(os.path.expanduser("~"), ListToAdd),mode)
		outfile.write(ItemToAdd+"\n")
		outfile.close()


def EditDesktopFile(DroppedFile,FileData,ListToAdd):
	fileHandle = open ( DroppedFile , 'w' )
	fileHandle.write ( '[Desktop Entry]\nEncoding=UTF-8\n' )
	fileHandle.write ( 'Name='+FileData[0]+'\n')
	fileHandle.write ( 'Comment='+FileData[1]+'\n')
	fileHandle.write ( 'Exec='+FileData[2]+'\n')
	fileHandle.write ( 'Icon='+FileData[3]+'\n')
	fileHandle.write ( 'GenericName='+FileData[4]+'\n')
	fileHandle.write ( 'Terminal='+FileData[5]+'\n')
	fileHandle.close()

def WriteDesktopFile(DroppedFile,FileData,ListToAdd):
	fileHandle = open ( DroppedFile , 'w' )
	fileHandle.write ( '[Desktop Entry]\nEncoding=UTF-8\n' )
	fileHandle.write ( 'Name='+FileData[0]+'\n')
	fileHandle.write ( 'Comment='+FileData[1]+'\n')
	fileHandle.write ( 'Exec='+FileData[2]+'\n')
	fileHandle.write ( 'Icon='+FileData[3]+'\n')
	fileHandle.write ( 'GenericName='+FileData[4]+'\n')
	fileHandle.write ( 'Terminal='+FileData[5]+'\n')
	fileHandle.close()

	WriteListFile(ListToAdd,DroppedFile,"a")
	print "Added to places.list"
"""