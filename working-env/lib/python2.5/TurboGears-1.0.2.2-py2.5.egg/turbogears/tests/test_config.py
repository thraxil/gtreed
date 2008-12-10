import turbogears
import pkg_resources
import sys
from cStringIO import StringIO
import logging
import re

testfile = pkg_resources.resource_filename(__name__, "configfile.cfg")

rfn = pkg_resources.resource_filename

logout = StringIO()
logging.logout = logout

def test_update_from_package():
    turbogears.update_config(modulename="turbogears.tests.config")
    assert turbogears.config.get("foo.bar") == "BAZ!"
    print turbogears.config.get("my.static")
    assert turbogears.config.get("my.static").endswith(
                                            "turbogears/tests/static")
    assert turbogears.config.get("static_filter.on", path="/static") == True

def test_update_from_both():
    turbogears.update_config(configfile = testfile, 
        modulename="turbogears.tests.config")
    print turbogears.config.get("foo.bar")
    assert turbogears.config.get("foo.bar") == "blurb"
    assert turbogears.config.get("tg.something") == 10
    print turbogears.config.get("test.dir")
    assert turbogears.config.get("test.dir").endswith("turbogears/tests")

callnum = 0

def windows_filename(*args, **kw):
    global callnum
    callnum += 1
    if callnum > 1:
        return "c:\\foo\\bar\\"
    else:
        return rfn(*args, **kw)

def test_windows_filenames():
    pkg_resources.resource_filename = windows_filename
    turbogears.update_config(configfile = testfile, 
        modulename="turbogears.tests.config")
    testdir = turbogears.config.get("test.dir")
    print testdir
    assert testdir == "c:/foo/bar"

def test_logging_config():
    logout.truncate(0)
    log = logging.getLogger("turbogears.tests.test_config.logconfig")
    log.info("Testing")
    logged = logout.getvalue()
    print "Logged: %s" % logged
    assert re.match(r'F1 \d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d INFO '
                    'Testing', logged)
    assert turbogears.config.get("tg.new_style_logging", False)
        
def teardown_module():
    pkg_resources.resource_filename = rfn
