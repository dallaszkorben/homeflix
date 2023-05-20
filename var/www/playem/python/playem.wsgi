#! /var/www/playem/python/env/bin/python

import sys,os

print("\n\n===================================")
print("The playem app started: %s" % (__file__))
print("Python version: {0}".format(sys.version))
print("Python path: {0}".format(sys.path))

sys.path.insert(0, os.path.realpath(os.path.dirname(__file__)))

from playem.restserver.ws_playem import app as application
