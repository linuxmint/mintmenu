#!/usr/bin/python2


from gi.repository import Gio

class EasyGSettings:

    def __init__( self, schema = None ):
        self.schema = schema
        self.settings = Gio.Settings.new(self.schema)
        self.handlerIds = [ ]

    def get( self, type, key ):

        if type == "bool":
            return self.settings.get_boolean( key )
        if type == "string":
            return self.settings.get_string( key )
        if type == "int":
            return self.settings.get_int( key )
        if type == "color":
            color = self.settings.get_string( key )
            if not self.evalColor( color ):
                self.settings.set_string(key, "#ffffff")
                return "#ffffff"
            return color

        t = type.split("-")
        if len(t) == 2 and t[0] == "list":
            return self.settings.get_strv( key )

        return self.settings.get( key )

    def set( self, type, key, value ):

        if type == "bool":
            return self.settings.set_boolean( key, value )

        if type == "string":
            return self.settings.set_string( key, value )

        if type == "int":
            return self.settings.set_int( key, value )

        if type == "color":
            if self.evalColor( value ):
                return self.settings.set_string( key, value )
            else:
                return self.settings.set_string( key, "#ffffff" )

        t = type.split("-")
        if len(t) == 2 and t[0] == "list":
            return self.settings.set_strv( key, value )

        return self.settings.set( key, value )

    def notifyAdd( self, key, callback, args = None ):
        handlerId = self.settings.connect("changed::"+key, callback, args)
        self.handlerIds.append( handlerId )
        return handlerId

    def notifyRemove( self, handlerId ):
        return self.settings.disconnect(handlerId)

    def notifyRemoveAll( self ):
        for handlerId in self.handlerIds:
            self.settings.disconnect( handlerId )

    def evalColor(self, colorToTest ):
        if colorToTest[0] != '#' or len( colorToTest ) != 7:
            return False
        for i in colorToTest[1:]:
            if i not in ['a', 'A', 'b', 'B', 'c', 'C', 'd', 'D', 'e', 'E', 'f', 'F', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                return False
        return True
        
    def bindGSettingsEntryToVar( self, type, key, obj, varName ):
        return self.notifyAdd( key, self.setVar, ( type, obj, varName ) )
        
    def setVar( self, settings, key, args ):
        type, obj, varName = args

        if type == "string":
            setattr( obj, varName, settings.get_string(key) )
        elif type == "int":
            setattr( obj, varName, settings.get_int(key) )
        elif type == "float":
            setattr( obj, varName, settings.get_float(key) )
        elif type == "bool":
            setattr( obj, varName, settings.get_boolean(key) )
        else:
            setattr( obj, varName, settings.get_value(key) )


