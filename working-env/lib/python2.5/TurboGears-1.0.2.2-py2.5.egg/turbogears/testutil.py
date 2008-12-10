import types
import inspect
import logging
import unittest
import cStringIO as StringIO
import Cookie

import cherrypy
try:
    import sqlobject
    from sqlobject.inheritance import InheritableSQLObject
except ImportError:
    sqlobject = None

try:
    import sqlalchemy
except ImportError:
    sqlalchemy = None

from cherrypy import _cphttptools

from turbogears import database, controllers, startup, validators, config, \
                       update_config
from turbogears.util import get_model

import os
from os.path import *

cwd = os.getcwd()

# For clean tests, remove all compiled Kid templates
for w in os.walk(cwd):
    if w[0] != '.svn':
        for f in w[2]:
            if f.endswith('.kid'):
                f = join(w[0], f[:-3] + 'pyc')
                if exists(f):
                    os.remove(f)

# Override config of all applications with test.cfg
if exists(join(cwd, "test.cfg")):
    modulename = None
    for w in os.walk(cwd):
        if w[0].endswith("config"):
            config_dir = w[0].replace(cwd, "")[1:]
            modulename = "%s.app" % config_dir.replace(os.sep, ".")
            break
    update_config(configfile=join(cwd, "test.cfg"), modulename=modulename)
else:
    database.set_db_uri("sqlite:///:memory:")

config.update({"global" : {"tg.new_style_logging" : True}})
config.update({"global" : {"autoreload.on" : False}})

def start_cp():
    if not config.get("cherrypy_started", False):
        cherrypy.server.start(serverClass=None, initOnly=True)
        config.update({"cherrypy_started" : True})

test_user = None

def set_identity_user(user):
    "Setup a user which will be used to configure request's identity."
    global test_user
    test_user = user

def attach_identity(req):
    from turbogears.identity import current_provider
    if config.get("identity.on", False):
        if test_user:
            id = current_provider.authenticated_identity(test_user)
        else:
            id = current_provider.anonymous_identity()
        req.identity = id

def create_request(request, method="GET", protocol="HTTP/1.1",
    headers={}, rfile=None, clientAddress="127.0.0.1",
    remoteHost="localhost", scheme="http"):
    start_cp()
    if not rfile:
        rfile = StringIO.StringIO("")
    if type(headers) != dict:
        headerList = headers
    else:
        headerList = [(key, value) for key, value in headers.items()]
    headerList.append(("Host", "localhost"))
    if not hasattr(cherrypy.root, "started"):
        startup.startTurboGears()
        cherrypy.root.started = True
    req = _cphttptools.Request(clientAddress, 80, remoteHost, scheme)
    cherrypy.serving.request = req
    attach_identity(req)
    cherrypy.serving.response = _cphttptools.Response()
    req.run(" ".join((method, request, protocol)), headerList, rfile)

createRequest = create_request


class BrowsingSession(object):
    def __init__(self):
        self.visit = None
        self.response, self.status = None, None
        self.cookie = Cookie.SimpleCookie()

    def goto(self, *args, **kwargs):
        if self.cookie:
            headers = kwargs.setdefault('headers', {})
            headers['Cookie'] = self.cookie.output()
        create_request(*args, **kwargs)
        self.response = cherrypy.response.body[0]
        self.status = cherrypy.response.status
        if cherrypy.response.simple_cookie:
            self.cookie.update(cherrypy.response.simple_cookie)


def _return_directly(output, *args):
    return output

class DummySession:
    session_storage = dict
    to_be_loaded = None

class DummyRequest:
    "A very simple dummy request."
    remote_host = "127.0.0.1"

    def __init__(self, method='GET', path='/', headers=None):
        self.headers = headers or {}
        self.method = method
        self.path = path
        self.base = ''
        self._session = DummySession()
    def purge__(self):
        pass

def call(method, *args, **kw):
    start_cp()
    output, response = call_with_request(method, DummyRequest(), *args, **kw)
    return output

def call_with_request(method, request, *args, **kw):
    "More fine-grained version of call method, allowing to use request/response."
    orig_proc_output = controllers._process_output
    controllers._process_output = _return_directly
    cherrypy.serving.response = _cphttptools.Response()
    cherrypy.serving.request = request
    if not hasattr(request, "identity"):
        attach_identity(request)
    output = None
    try:
        output = method(*args, **kw)
    finally:
        del cherrypy.serving.request
        controllers._process_output = orig_proc_output
    response = cherrypy.serving.response
    return output, response


class DBTest(unittest.TestCase):
    model = None

    def setUp(self):
        if not self.model:
            self.model = get_model()
            if not self.model:
                raise "Unable to run database tests without a model"

        for item in self.model.__dict__.values():
            if isinstance(item, types.TypeType) and issubclass(item,
                sqlobject.SQLObject) and item != sqlobject.SQLObject \
                and item != InheritableSQLObject:
                item.createTable(ifNotExists=True)

    def tearDown(self):
        database.rollback_all()
        for item in self.model.__dict__.values():
            if isinstance(item, types.TypeType) and issubclass(item,
                sqlobject.SQLObject) and item != sqlobject.SQLObject \
                and item != InheritableSQLObject:
                item.dropTable(ifExists=True)

def reset_cp():
    cherrypy.root = None

def catch_validation_errors(widget, value):
    """ Catches and unpacks validation errors. For testing purposes. """
    errors = {}
    try:
        value = widget.validate(value)
    except validators.Invalid, e:
        if hasattr(e, 'unpack_errors'):
            errors = e.unpack_errors()
        else:
            errors = e
    return value, errors

class MemoryListHandler(logging.Handler):

    def __init__(self):
        logging.Handler.__init__(self, level=logging.DEBUG)
        self.log = []

    def emit(self, record):
        print "Got record: %s" % record
        print "formatted as: %s" % self.format(record)
        self.log.append(self.format(record))

    def print_log(self):
        print "\n".join(self.log)
        self.log = []

    def get_log(self):
        log = self.log
        self.log = []
        return log

_memhandler = MemoryListHandler()
_currentcat = None

def capture_log(category):
    """Category can either be a single category (a string like 'foo.bar')
    or a list of them. You <em>must</em> call print_log() to reset when
    you're done."""
    global _currentcat
    assert not _currentcat
    if not isinstance(category, list) and not isinstance(category, tuple):
        category = [category]
    _currentcat = category
    for cat in category:
        log = logging.getLogger(cat)
        log.setLevel(logging.DEBUG)
        log.addHandler(_memhandler)

def _reset_logging():
    """Manages the resetting of the loggers"""
    global _currentcat
    if not _currentcat:
        return
    for cat in _currentcat:
        log = logging.getLogger(cat)
        log.removeHandler(_memhandler)
    _currentcat = None

def print_log():
    """Prints the log captured by capture_log to stdout, resets that log
    and resets the temporarily added handlers."""
    _reset_logging()
    _memhandler.print_log()

def get_log():
    """Returns the list of log messages captured by capture_log,
    resets that log and resets the temporarily added handlers."""
    _reset_logging()
    return _memhandler.get_log()

def sqlalchemy_cleanup():
    database._engine = None
    sqlalchemy.clear_mappers()
    database.metadata.clear()
    database.metadata.dispose()

__all__ = ["create_request", "call", "DBTest", "createRequest",
    "attach_identity", "set_identity_user",
    "capture_log", "print_log", "get_log", "sqlalchemy_cleanup"]
