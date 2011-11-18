#!/usr/bin/env python

import mateconf

class EasyGConf:

	def __init__( self, gconfDir = None, client = None ):

		if not client:
			client = mateconf.client_get_default()
		
		self.client = client
		self.gconfDir = gconfDir

		self.client.add_dir( self.gconfDir[:-1], mateconf.CLIENT_PRELOAD_NONE )

		self.handlerIds = [ ]

	def get( self, type, key, default = None ):

		if key[0] != "/":
			key = self.gconfDir + key


		#check if key exists, if not set and return default value
		tempkey = self.client.get( key )
		if tempkey == None and default != None:
			self.set( type, key, default )
			return default
			

		if type == "bool":
			return self.client.get_bool( key )
		if type == "string":
			return self.client.get_string( key )
		if type == "int":
			return self.client.get_int( key )
		if type == "color":
			color = self.client.get_string( key )
			if not self.evalColor( color ):
				self.set( type, key, default )
				return default

			return color

		t = type.split("-")
		if len(t) == 2 and t[0] == "list":
			return self.client.get_list( key, t[1] )

		return self.client.get( key )


	def set( self, type, key, value ):

		if key[0] != "/":
			key = self.gconfDir + key

		if type == "bool":
			return self.client.set_bool( key, value )

		if type == "string":
			return self.client.set_string( key, value )

		if type == "int":
			return self.client.set_int( key, value )

		if type == "color":
			if self.evalColor( value ):
				return self.client.set_string( key, value )
			else:
				return self.client.set_string( key, "#ffffff" )

		t = type.split("-")
		if len(t) == 2 and t[0] == "list":
			return self.client.set_list( key, t[1], value )

		return self.client.set( key, value )


	def notifyAdd( self, key, callback, args = None ):
		if key[0] != "/":
			key = self.gconfDir + key

		handlerId = self.client.notify_add( key, callback, args)
		self.handlerIds.append( handlerId )
		return handlerId
		
	def notifyRemove( self, handlerId ):
		return self.client.notify_remove( handlerId )

	def notifyRemoveAll( self ):
		for handlerId in self.handlerIds:
			self.notifyRemove( handlerId )

	def evalColor(self, colorToTest ):
		if colorToTest[0] != '#' or len( colorToTest ) != 7:
			return False
		for i in colorToTest[1:]:
			if i not in ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
				return False
		return True
		
	def bindGconfEntryToVar( self, type, key, obj, varName ):
		return self.notifyAdd( key, self.setVar, ( type, obj, varName ) )
		
	def setVar( self, client, connection_id, entry, args ):
		type, obj, varName = args

		if type == "string":
			setattr( obj, varName, entry.get_value().get_string() )
		elif type == "int":
			setattr( obj, varName, entry.get_value().get_int() )
		elif type == "float":
			setattr( obj, varName, entry.get_value().get_float() )
		elif type == "bool":
			setattr( obj, varName, entry.get_value().get_bool() )
		else:
			setattr( obj, varName, entry.get_value() )


