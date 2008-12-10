"""Tools which both CherryPy and application developers may invoke."""

import inspect
import mimetools
import mimetypes
mimetypes.init()
mimetypes.types_map['.dwg']='image/x-dwg'
mimetypes.types_map['.ico']='image/x-icon'

import os
import sys
import time

import cherrypy
import httptools

from cherrypy.filters.wsgiappfilter import WSGIAppFilter


def decorate(func, decorator):
    """
    Return the decorated func. This will automatically copy all
    non-standard attributes (like exposed) to the newly decorated function.
    """
    newfunc = decorator(func)
    for (k,v) in inspect.getmembers(func):
        if not hasattr(newfunc, k):
            setattr(newfunc, k, v)
    return newfunc

def decorateAll(obj, decorator):
    """
    Recursively decorate all exposed functions of obj and all of its children,
    grandchildren, etc. If you used to use aspects, you might want to look
    into these. This function modifies obj; there is no return value.
    """
    obj_type = type(obj)
    for (k,v) in inspect.getmembers(obj):
        if hasattr(obj_type, k): # only deal with user-defined attributes
            continue
        if callable(v) and getattr(v, "exposed", False):
            setattr(obj, k, decorate(v, decorator))
        decorateAll(v, decorator)


class ExposeItems:
    """
    Utility class that exposes a getitem-aware object. It does not provide
    index() or default() methods, and it does not expose the individual item
    objects - just the list or dict that contains them. User-specific index()
    and default() methods can be implemented by inheriting from this class.
    
    Use case:
    
    from cherrypy.lib.cptools import ExposeItems
    ...
    cherrypy.root.foo = ExposeItems(mylist)
    cherrypy.root.bar = ExposeItems(mydict)
    """
    exposed = True
    def __init__(self, items):
        self.items = items
    def __getattr__(self, key):
        return self.items[key]

def modified_since(path, stat=None):
    """Check whether a file has been modified since the date
    provided in 'If-Modified-Since'
    It doesn't check if the file exists or not
    Return True if has been modified, False otherwise
    """
    # serveFile already creates a stat object so let's not
    # waste our energy to do it again
    if not stat:
        try:
            stat = os.stat(path)
        except OSError:
            if cherrypy.config.get('server.log_file_not_found', False):
                cherrypy.log("    NOT FOUND file: %s" % path, "DEBUG")
            raise cherrypy.NotFound()
    
    response = cherrypy.response
    strModifTime = httptools.HTTPDate(time.gmtime(stat.st_mtime))
    if cherrypy.request.headers.has_key('If-Modified-Since'):
        if cherrypy.request.headers['If-Modified-Since'] == strModifTime:
            response.status = "304 Not Modified"
            response.body = None
            if getattr(cherrypy, "debug", None):
                cherrypy.log("    Found file (304 Not Modified): %s" % path, "DEBUG")
            return False
    response.headers['Last-Modified'] = strModifTime
    return True
    
def serveFile(path, contentType=None, disposition=None, name=None):
    """Set status, headers, and body in order to serve the given file.
    
    The Content-Type header will be set to the contentType arg, if provided.
    If not provided, the Content-Type will be guessed by its extension.
    
    If disposition is not None, the Content-Disposition header will be set
    to "<disposition>; filename=<name>". If name is None, it will be set
    to the basename of path. If disposition is None, no Content-Disposition
    header will be written.
    """
    
    response = cherrypy.response
    
    # If path is relative, users should fix it by making path absolute.
    # That is, CherryPy should not guess where the application root is.
    # It certainly should *not* use cwd (since CP may be invoked from a
    # variety of paths). If using static_filter, you can make your relative
    # paths become absolute by supplying a value for "static_filter.root".
    if not os.path.isabs(path):
        raise ValueError("'%s' is not an absolute path." % path)
    
    try:
        stat = os.stat(path)
    except OSError:
        if cherrypy.config.get('server.log_file_not_found', False):
            cherrypy.log("    NOT FOUND file: %s" % path, "DEBUG")
        raise cherrypy.NotFound()
    
    if os.path.isdir(path):
        # Let the caller deal with it as they like.
        raise cherrypy.NotFound()
    
    if contentType is None:
        # Set content-type based on filename extension
        ext = ""
        i = path.rfind('.')
        if i != -1:
            ext = path[i:].lower()
        contentType = mimetypes.types_map.get(ext, "text/plain")
    response.headers['Content-Type'] = contentType
    
    if not modified_since(path, stat):
        return []
    
    if disposition is not None:
        if name is None:
            name = os.path.basename(path)
        cd = "%s; filename=%s" % (disposition, name)
        response.headers["Content-Disposition"] = cd
    
    # Set Content-Length and use an iterable (file object)
    #   this way CP won't load the whole file in memory
    c_len = stat.st_size
    bodyfile = open(path, 'rb')
    if getattr(cherrypy, "debug", None):
        cherrypy.log("    Found file: %s" % path, "DEBUG")
    
    # HTTP/1.0 didn't have Range/Accept-Ranges headers, or the 206 code
    if cherrypy.response.version >= "1.1":
        response.headers["Accept-Ranges"] = "bytes"
        r = httptools.getRanges(cherrypy.request.headers.get('Range'), c_len)
        if r == []:
            response.headers['Content-Range'] = "bytes */%s" % c_len
            message = "Invalid Range (first-byte-pos greater than Content-Length)"
            raise cherrypy.HTTPError(416, message)
        if r:
            if len(r) == 1:
                # Return a single-part response.
                start, stop = r[0]
                r_len = stop - start
                response.status = "206 Partial Content"
                response.headers['Content-Range'] = ("bytes %s-%s/%s" %
                                                       (start, stop - 1, c_len))
                response.headers['Content-Length'] = r_len
                bodyfile.seek(start)
                response.body = bodyfile.read(r_len)
            else:
                # Return a multipart/byteranges response.
                response.status = "206 Partial Content"
                boundary = mimetools.choose_boundary()
                ct = "multipart/byteranges; boundary=%s" % boundary
                response.headers['Content-Type'] = ct
##                del response.headers['Content-Length']
                
                def fileRanges():
                    for start, stop in r:
                        yield "--" + boundary
                        yield "\nContent-type: %s" % contentType
                        yield ("\nContent-range: bytes %s-%s/%s\n\n"
                               % (start, stop - 1, c_len))
                        bodyfile.seek(start)
                        yield bodyfile.read((stop + 1) - start)
                        yield "\n"
                    # Final boundary
                    yield "--" + boundary
                response.body = fileRanges()
        else:
            response.headers['Content-Length'] = c_len
            response.body = bodyfile
    else:
        response.headers['Content-Length'] = c_len
        response.body = bodyfile
    return response.body

def fileGenerator(input, chunkSize=65536):
    """Yield the given input (a file object) in chunks (default 64k)."""
    chunk = input.read(chunkSize)
    while chunk:
        yield chunk
        chunk = input.read(chunkSize)
    input.close()

def modules(modulePath):
    """Load a module and retrieve a reference to that module."""
    try:
        mod = sys.modules[modulePath]
        if mod is None:
            raise KeyError()
    except KeyError:
        # The last [''] is important.
        mod = __import__(modulePath, globals(), locals(), [''])
    return mod

def attributes(fullAttributeName):
    """Load a module and retrieve an attribute of that module."""
    
    # Parse out the path, module, and attribute
    lastDot = fullAttributeName.rfind(u".")
    attrName = fullAttributeName[lastDot + 1:]
    modPath = fullAttributeName[:lastDot]
    
    aMod = modules(modPath)
    # Let an AttributeError propagate outward.
    try:
        attr = getattr(aMod, attrName)
    except AttributeError:
        raise AttributeError("'%s' object has no attribute '%s'"
                             % (modPath, attrName))
    
    # Return a reference to the attribute.
    return attr


class WSGIApp(object):
    """a convenience class that uses the WSGIAppFilter
    
    to easily add a WSGI application to the CP object tree.

    example:
    cherrypy.tree.mount(SomeRoot(), '/')
    cherrypy.tree.mount(WSGIApp(other_wsgi_app), '/ext_app')
    """
    def __init__(self, app, env_update=None):
        self._cpFilterList = [WSGIAppFilter(app, env_update)]


# public domain "unrepr" implementation, found on the web and then improved.
import compiler

def getObj(s):
    s = "a=" + s
    p = compiler.parse(s)
    return p.getChildren()[1].getChildren()[0].getChildren()[1]


class UnknownType(Exception):
    pass


class Builder:
    
    def build(self, o):
        m = getattr(self, 'build_' + o.__class__.__name__, None)
        if m is None:
            raise UnknownType(o.__class__.__name__)
        return m(o)
    
    def build_List(self, o):
        return map(self.build, o.getChildren())
    
    def build_Const(self, o):
        return o.value
    
    def build_Dict(self, o):
        d = {}
        i = iter(map(self.build, o.getChildren()))
        for el in i:
            d[el] = i.next()
        return d
    
    def build_Tuple(self, o):
        return tuple(self.build_List(o))
    
    def build_Name(self, o):
        if o.name == 'None':
            return None
        if o.name == 'True':
            return True
        if o.name == 'False':
            return False
        
        # See if the Name is a package or module
        try:
            return modules(o.name)
        except ImportError:
            pass
        
        raise UnknownType(o.name)
    
    def build_Add(self, o):
        real, imag = map(self.build_Const, o.getChildren())
        try:
            real = float(real)
        except TypeError:
            raise UnknownType('Add')
        if not isinstance(imag, complex) or imag.real != 0.0:
            raise UnknownType('Add')
        return real+imag
    
    def build_Getattr(self, o):
        parent = self.build(o.expr)
        return getattr(parent, o.attrname)


def unrepr(s):
    if not s:
        return s
    return Builder().build(getObj(s))

