#!/usr/bin/env python
import pkg_resources

pkg_resources.require("TurboGears")
import turbogears
import sys,os,os.path
path = os.path.normpath(os.path.dirname(__file__))
path = path.replace("scripts/","")
sys.path.append(path)
import cherrypy
from os.path import *
turbogears.update_config(configfile=join(dirname(__file__),"../prod.cfg"), modulename="treed.config")
sys.path.append(".")

from treed.model import *

for u in User.select():
    u.tickle()

hub.commit()
