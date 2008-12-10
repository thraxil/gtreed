"Things to do when TurboGears is imported."

import os
import errno
import logging
import sys
import time
import atexit
import signal

import pkg_resources
import cherrypy
from cherrypy import _cputil
from formencode.variabledecode import NestedVariables
from cherrypy._cpwsgi import wsgiApp, CPHTTPRequest
from cherrypy._cpwsgiserver import CherryPyWSGIServer

from turbogears import config, scheduler, database
from turbogears import view
from turbogears.database import hub_registry, EndTransactionsFilter

log = logging.getLogger("turbogears.startup")

pkg_resources.require("TurboGears")


def reloader_thread(freq):
    """Monkeypatch for the reloader provided by CherryPy.

    This reloader is designed to reload a single package. This is
    more efficient and, more important, compatible with zipped
    libraries that may not provide access to the individual files."""

    def archive_selector(module):
        if hasattr(module, '__loader__'):
            if hasattr(module.__loader__, 'archive'):
                return module.__loader__.archive
        return module

    mtimes = {}
    package = config.get("autoreload.package", None)
    if package is None:
        print \
"""TurboGears requires autoreload.package to be set. It can be an empty
value, which will use CherryPy's default behavior which is to check
every module. Setting an actual package makes the check much faster."""
        return
    while cherrypy.lib.autoreload.RUN_RELOADER:
        if package:
            modnames = filter(lambda modname: modname.startswith(package),
                                sys.modules.keys())
            modlist = [sys.modules[modname] for modname in modnames]
        else:
            modlist = map(archive_selector, sys.modules.values())
        for filename in filter(lambda v: v,
                map(lambda m: getattr(m, "__file__", None), modlist)):
            if filename.endswith(".kid") or filename == "<string>":
                continue
            orig_filename = filename
            if filename.endswith(".pyc"):
                filename = filename[:-1]
            try:
                mtime = os.stat(filename).st_mtime
            except OSError, e:
                if orig_filename.endswith('.pyc') and e[0] == errno.ENOENT:
                    # This prevents us from endlessly restarting
                    # if there is an old .pyc lying around
                    # after a .py file has been deleted
                    try: os.unlink(orig_filename)
                    except: pass
                sys.exit(3) # force reload
            if filename not in mtimes:
                mtimes[filename] = mtime
                continue
            if mtime > mtimes[filename]:
                sys.exit(3) # force reload
        time.sleep(freq)

cherrypy.lib.autoreload.reloader_thread = reloader_thread

webpath = ""

DNS_SD_PID = None


def start_bonjour(package=None):
    global DNS_SD_PID
    if DNS_SD_PID:
        return
    if (not hasattr(cherrypy, "root")) or (not cherrypy.root):
        return
    if not package:
        package = cherrypy.root.__module__
        package = package[:package.find(".")]

    host = config.get('server.socket_host', '')
    port = str(config.get('server.socket_port'))
    env = config.get('server.environment')
    name = package + ": " + env
    type = "_http._tcp"

    cmds = [['/usr/bin/avahi-publish-service', ["-H", host, name, type, port]],
            ['/usr/bin/dns-sd', ['-R', name, type, "."+host, port, "path=/"]]]

    for cmd, args in cmds:
        # TODO:. This check is flawed.  If one has both services installed and
        # avahi isn't the one running, then this won't work.  We should either
        # try registering with both or checking what service is running and use
        # that.  Program availability on the filesystem was never enough...
        if os.path.exists(cmd):
            DNS_SD_PID = os.spawnv(os.P_NOWAIT, cmd, [cmd]+args)
            atexit.register(stop_bonjour)
            break


def stop_bonjour():
    if not DNS_SD_PID:
        return
    try:
        os.kill(DNS_SD_PID, signal.SIGTERM)
    except OSError:
        pass


class VirtualPathFilter(object):
    """Filter that makes CherryPy ignorant of a URL root path.

    That is, you can mount your app so the URI "/users/~rdel/myapp/"
    maps to the root object "/".
    """

    def on_start_resource(self):
        prefix = config.get('server.webpath', False)
        if prefix:
            path = cherrypy.request.object_path
            if path == prefix:
                cherrypy.request.object_path = '/'
            elif path.startswith(prefix):
                cherrypy.request.object_path = path[len(prefix):]
            else:
                raise cherrypy.NotFound(path)

class NestedVariablesFilter(object):

    def before_main(self):
        if hasattr(cherrypy.request, "params"):
            cherrypy.request.params = \
                NestedVariables.to_python(cherrypy.request.params or {})


def startTurboGears():
    """Handles TurboGears tasks when the CherryPy server starts.

    This adds the "tg_js" configuration to make MochiKit accessible.
    It also turns on stdlib logging when in development mode.
    """
    config.update({"/tg_static":
            {
            "static_filter.on": True,
            "static_filter.dir":
                os.path.abspath(pkg_resources.resource_filename(__name__, "static")),
            'log_debug_info_filter.on' : False,
            }
        })
    config.update({"/tg_js" :
            {
            "static_filter.on" : True,
            "static_filter.dir" :
                os.path.abspath(pkg_resources.resource_filename(__name__, "static/js")),
            'log_debug_info_filter.on' : False,
            }
        })
    cherrypy.config.environments['development']['log_debug_info_filter.on'] = False
    
    if config.get("decoding_filter.on", path="/") is None:
        config.update({"/": {
            "decoding_filter.on" : True,
            "decoding_filter.encoding" : config.get(
                                        "kid.encoding", "utf8")
        }})
        
    view.load_engines()
    view.loadBaseTemplates()
    global webpath
    webpath = config.get("server.webpath", "")

    if hasattr(cherrypy, "root") and cherrypy.root:
        if not hasattr(cherrypy.root, "_cp_filters"):
            cherrypy.root._cp_filters= []
        morefilters = [EndTransactionsFilter(),
                       NestedVariablesFilter()]
        if webpath:
            morefilters.insert(0, VirtualPathFilter())
        cherrypy.root._cp_filters.extend(morefilters)

    if webpath.startswith("/"):
        webpath = webpath[1:]
    if webpath and not webpath.endswith("/"):
        webpath = webpath + "/"
    isdev = config.get('server.environment') == 'development'
    if not config.get("tg.new_style_logging"):
        if config.get('server.log_to_screen'):
            setuplog = logging.getLogger()
            setuplog.setLevel(logging.DEBUG)
            fmt = logging.Formatter("%(asctime)s %(name)s "
                                    "%(levelname)s %(message)s")
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(fmt)
            setuplog.addHandler(handler)
        
        logfile = config.get("server.log_file")
        if logfile:
            setuplog = logging.getLogger("turbogears.access")
            setuplog.propagate = 0
            fmt = logging.Formatter("%(message)s")
            handler = logging.FileHandler(logfile)
            handler.setLevel(logging.INFO)
            handler.setFormatter(fmt)
            setuplog.addHandler(handler)

    bonjoursetting = config.get("tg.bonjour", None)
    if bonjoursetting or isdev:
        start_bonjour(bonjoursetting)
    
    if config.get("sqlalchemy.dburi"):
        database.bind_meta_data()

    # Start all TurboGears extensions
    extensions= pkg_resources.iter_entry_points( "turbogears.extensions" )
    for entrypoint in extensions:
        ext= entrypoint.load()
        if hasattr(ext, "start_extension"):
            ext.start_extension()
    
    for item in call_on_startup:
        item()
        
    if config.get("tg.scheduler", False):
        scheduler._start_scheduler()
        log.info("Scheduler started")


def stopTurboGears():
    # end all transactions and clear out the hubs to
    # help ensure proper reloading in autoreload situations
    for hub in hub_registry:
        hub.end()
    hub_registry.clear()

    stop_bonjour()

    # Shut down all TurboGears extensions
    extensions= pkg_resources.iter_entry_points( "turbogears.extensions" )
    for entrypoint in extensions:
        ext= entrypoint.load()
        if hasattr(ext, "shutdown_extension"):
            ext.shutdown_extension()

    for item in call_on_shutdown:
        item()
        
    if config.get("tg.scheduler", False):
        scheduler._stop_scheduler()
        log.info("Scheduler stopped")
        
old_object_trail = _cputil.get_object_trail

# hang on to object trail to use it to find an app root if need be
def get_object_trail(object_path=None):
    trail = old_object_trail(object_path)
    try:
        cherrypy.request.object_trail = trail
    except AttributeError:
        pass
    return trail

_cputil.get_object_trail = get_object_trail

class SimpleWSGIServer(CherryPyWSGIServer):
    """A WSGI server that accepts a WSGI application as a parameter."""
    RequestHandlerClass = CPHTTPRequest
    
    def __init__(self):
        conf = cherrypy.config.get
        wsgi_app = wsgiApp
        if conf('server.environment') == 'development':
            try:
                from paste.evalexception.middleware import EvalException
            except ImportError:
                pass
            else:
                wsgi_app = EvalException(wsgi_app, global_conf={})
                cherrypy.config.update({'server.throw_errors':True})
        bind_addr = (conf("server.socket_host"), conf("server.socket_port"))
        CherryPyWSGIServer.__init__(self, bind_addr, wsgi_app,
                                    conf("server.thread_pool"),
                                    conf("server.socket_host"),
                                    request_queue_size = conf(
                                        "server.socket_queue_size"),
                                    )

def start_server(root):
    cherrypy.root = root
    if config.get("tg.fancy_exception", False):
        cherrypy.server.start(server=SimpleWSGIServer())
    else:
        cherrypy.server.start()

if startTurboGears not in cherrypy.server.on_start_server_list:
    cherrypy.server.on_start_server_list.append(startTurboGears)

if stopTurboGears not in cherrypy.server.on_stop_server_list:
    cherrypy.server.on_stop_server_list.append(stopTurboGears)

call_on_startup = []
call_on_shutdown = []
