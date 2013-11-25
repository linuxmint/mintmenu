import os
import subprocess

def RemoveArgs(Execline):
	NewExecline = []
	Specials=["\"%c\"", "%f","%F","%u","%U","%d","%D","%n","%N","%i","%c","%k","%v","%m","%M", "-caption", "/bin/sh", "sh", "-c", "STARTED_FROM_MENU=yes"]
	for elem in Execline:
		elem = elem.replace("'","")
		elem = elem.replace("\"", "")
		if elem not in Specials:
			print elem
			NewExecline.append(elem)
	return NewExecline

# Actually execute the command
def Execute( cmd , commandCwd=None):
	if not commandCwd:
		cwd = os.path.expanduser( "~" );
	else:
		tmpCwd = os.path.expanduser( commandCwd );
		if (os.path.exists(tmpCwd)):
			cwd = tmpCwd
	
	if isinstance( cmd, str ) or isinstance( cmd, unicode):
		if (cmd.find("/home/") >= 0) or (cmd.find("su-to-root") >= 0) or (cmd.find("\"") >= 0):
			print "running manually..."
			os.chdir(cwd)
			os.system(cmd + " &")
			return True		
		cmd = cmd.split()
	cmd = RemoveArgs(cmd)
	
	try:
		os.chdir( cwd )
		subprocess.Popen( cmd )
		return True
	except Exception, detail:
		print detail
		return False
		
