#!/usr/bin/python

import apt, sys

try:
    cache = apt.Cache()    
    for pkg in cache:
        if not pkg.is_installed:
            name = pkg.name
            summary = pkg.candidate.summary.capitalize()
            description = pkg.candidate.description.replace("\n", "~~~")
            print "CACHE" + "###" + str(name) + "###" + str(summary) + "###" + str(description)
except Exception, detail:
    print "ERROR###ERROR###ERROR###ERROR"
    print detail
    sys.exit(1)
