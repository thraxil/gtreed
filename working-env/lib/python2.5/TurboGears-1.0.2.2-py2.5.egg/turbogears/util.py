import os
import sys
import re
import htmlentitydefs
from inspect import getargspec, getargvalues
from itertools import izip, islice, chain, imap
from operator import isSequenceType

import pkg_resources
import setuptools

from cherrypy import request
from turbogears.decorator import decorator
from turbogears import config


# This Enum implementation is from the Python Cookbook and is
# written by Zoran Isailovski:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/413486

def Enum(*names):
    ##assert names, "Empty enums are not supported" # <- Don't like empty enums? Uncomment!

    class EnumClass(object):
        __slots__ = names
        def __iter__(self):          return iter(constants)
        def __len__(self):            return len(constants)
        def __getitem__(self, i):  return constants[i]
        def __repr__(self):          return 'Enum' + str(names)
        def __str__(self):            return 'enum ' + str(constants)

    enumType = EnumClass()

    class EnumValue(object):
        __slots__ = ('__value')
        def __init__(self, value): self.__value = value
        Value = property(lambda self: self.__value)
        EnumType = property(lambda self: enumType)
        def __hash__(self):          return hash(self.__value)
        def __cmp__(self, other):
            # C fans might want to remove the following assertion
            # to make all enums comparable by ordinal value {;))
            assert self.EnumType is other.EnumType, "Only values from the same enum are comparable"
            return cmp(self.__value, other.__value)
        def __invert__(self):        return constants[maximum - self.__value]
        def __nonzero__(self):      return bool(self.__value)
        def __repr__(self):          return str(names[self.__value])

    maximum = len(names) - 1
    constants = [None] * len(names)
    for i, each in enumerate(names):
        val = EnumValue(i)
        setattr(EnumClass, each, val)
        constants[i] = val
    constants = tuple(constants)
    return enumType

class setlike(list):
    """Set preserving item order."""

    def add(self, item):
        if item not in self:
            self.append(item)

    def add_all(self, iterable):
        for item in iterable:
            self.add(item)

def get_project_meta(name):
    for dirname in os.listdir("./"):
        if dirname.lower().endswith("egg-info"):
            fname = os.path.join(dirname, name)
            return fname

def get_project_config():
    """Tries to select appropriate project configuration file."""

    config = None
    if os.path.exists("setup.py"):
        config = "dev.cfg"
    else:
        config = "prod.cfg"
    return config

def load_project_config(configfile=None):
    """Tries to update the config, loading project settings from the config
    file specified.  If config is C{None} uses L{get_project_config} to locate
    one.
    """
    if configfile is None:
        configfile = get_project_config()
    if not os.path.isfile(configfile):
        print 'config file %s not found or is not a file.' % os.path.abspath(configfile)
        sys.exit()
    package = get_package_name()
    config.update_config(configfile=configfile,
        modulename = package + ".config")

def get_package_name():
    """Try to find out the package name of the current directory."""
    if "--egg" in sys.argv:
        projectname = sys.argv[sys.argv.index("--egg")+1]
        egg = pkg_resources.get_distribution(projectname)
        package = list(egg._get_metadata("top_level.txt"))[0]
        return package
    fname = get_project_meta('top_level.txt')
    if fname:
        return open(fname).readline()[:-1]

def get_project_name():
    pkg_info = get_project_meta('PKG-INFO')
    if pkg_info:
        name = list(open(pkg_info))[1][6:-1]
        return name

def get_model():
    package_name = get_package_name()
    if not package_name:
        return None
    package = __import__(package_name, {}, {}, ["model"])
    if hasattr(package, "model"):
        return package.model


def ensure_sequence(obj):
    """Construct a sequence from object."""
    if obj is None:
        return []
    elif isSequenceType(obj):
        return obj
    else:
        return [obj]

def to_kw(func, args, kw, start=0):
    """Convert all applicable arguments to keyword arguments."""
    argnames, defaults = getargspec(func)[::3]
    defaults = ensure_sequence(defaults)
    kv_pairs = izip(islice(argnames, start, len(argnames) - len(defaults)), args)
    for k, v in kv_pairs:
        kw[k] = v
    return args[len(argnames)-len(defaults)-start:], kw

def from_kw(func, args, kw, start=0):
    """Extract named positional arguments from keyword arguments."""
    argnames, defaults = getargspec(func)[::3]
    defaults = ensure_sequence(defaults)
    newargs = [kw.pop(name) for name in islice(argnames, start,
               len(argnames) - len(defaults)) if name in kw]
    newargs.extend(args)
    return newargs, kw

def adapt_call(func, args, kw, start=0):
    """Remove excess arguments."""
    argnames, varargs, kwargs, defaults = getargspec(func)
    defaults = ensure_sequence(defaults)
    del argnames[:start]
    if kwargs in (None, "_decorator__kwargs"):
        remove_keys(kw, [key for key in kw.iterkeys() if key not in argnames])
    if varargs in (None, "_decorator__varargs"):
        args = args[:len(argnames) - len(defaults)]
    else:
        pivot = len(argnames) - len(defaults)
        args = tuple(chain(islice(args, pivot), imap(kw.pop, islice(
                        argnames, pivot, None)), islice(args, pivot, None)))
    return args, kw

def call_on_stack(func_name, kw, start=0):
    """Check if a call to function matching pattern is on stack. """
    try:
        frame = sys._getframe(start+1)
    except ValueError:
        return False
    while frame.f_back:
        frame = frame.f_back
        if frame.f_code.co_name == func_name:
            args = getargvalues(frame)[3]
            for key in kw.iterkeys():
                try:
                    if kw[key] != args[key]:
                        continue
                except KeyError, TypeError:
                    continue
            if key or not args:
                return True
    return False

def arg_index(func, argname):
    """Find index of argument as declared for given function."""
    argnames = getargspec(func)[0]
    if has_arg(func, argname):
        return argnames.index(argname)
    else:
        return None

def has_arg(func, argname):
    """Check whether function has argument."""
    return argname in getargspec(func)[0]

def inject_arg(func, argname, argval, args, kw, start=0):
    """Insert argument into call."""
    argnames, defaults = getargspec(func)[::3]
    defaults = ensure_sequence(defaults)
    pos = arg_index(func, argname)
    if pos is None or pos > len(argnames) - len(defaults) - 1:
        kw[argname] = argval
    else:
        pos -= start
        args = tuple(chain(islice(args, pos), (argval,),
                           islice(args, pos, None)))
    return args, kw

def inject_args(func, injections, args, kw, start=0):
    """Insert arguments into call."""
    for argname, argval in injections.iteritems():
        args, kw = inject_arg(func, argname, argval, args, kw, start)
    return args, kw

def inject_call(func, injections, *args, **kw):
    """Insert arguments and call."""
    args, kw = inject_args(func, injections, args, kw)
    return func(*args, **kw)

def bind_args(**add):
    """Call with arguments set to a predefined value."""
    def entagle(func):
        return lambda func, *args, **kw: inject_call(func, add, *args, **kw)

    def make_decorator(func):
        argnames, varargs, kwargs, defaults = getargspec(func)
        defaults = list(ensure_sequence(defaults))
        defaults = [d for d in defaults if
                    argnames[-len(defaults) + defaults.index(d)] not in add]
        argnames = [arg for arg in argnames if arg not in add]
        return decorator(entagle, (argnames, varargs, kwargs, defaults))(func)

    return make_decorator

def remove_keys(dict_, seq):
    """Gracefully remove keys from dict."""
    for key in seq:
        dict_.pop(key, None)
    return dict_

def recursive_update(to_dict, from_dict):
    """Recursively update all dicts in to_dict with values from from_dict."""
    # probably slow as hell :( should be optimized somehow...
    for k, v in from_dict.iteritems():
        if isinstance(v, dict) and isinstance(to_dict[k], dict):
            recursive_update(to_dict[k], v)
        else:
            to_dict[k] = v
    return to_dict

def combine_contexts(frames=None, depth=None):
    """Combine contexts (globals, locals) of frames."""
    locals_ = {}
    globals_ = {}
    if frames is None:
        frames = []
    if depth is not None:
        frames.extend([sys._getframe(d+1) for d in depth])
    for frame in frames:
        locals_.update(frame.f_locals)
        globals_.update(frame.f_globals)
    return locals_, globals_

def request_available():
    """Check if cherrypy.request is available."""
    try:
        setattr(request, "tg_dumb_attribute", True)
        return True
    except AttributeError:
        return False


def flatten_sequence(seq):
    """Flatten sequence."""
    for item in seq:
        if isSequenceType(item) and not isinstance(item, basestring):
            for item in flatten_sequence(item):
                yield item
        else:
            yield item


def load_class(dottedpath):
    '''
    Loads a class from a module in dotted-path notation.
    Eg: load_class("package.module.class").

    Based on recipe 16.3 from "Python Cookbook, 2ed., by Alex Martelli,
    Anna Martelli Ravenscroft, and David Ascher (O'Reilly Media, 2005)
    0-596-00797-3"
    '''
    splitted_path = dottedpath.split('.')
    modulename = '.'.join(splitted_path[:-1])
    classname = splitted_path[-1]
    try:
        module = __import__(modulename, globals(), locals(), [classname])
    except ImportError:
        return None
    return getattr(module, classname)

class Bunch(dict):
    __setattr__ = dict.__setitem__

    def __delattr__(self, name):
        try:
            del self[name]
        except KeyError:
            raise AttributeError(name)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

#XXX: Should issue Deprecation warning?
DictObj = Bunch
DictWrapper = Bunch

def parse_http_accept_header(accept):
    items = []
    if accept is None:
        return items
    for item in accept.split(","):
        pos = item.find(";q=")
        order = 1
        if pos > -1:
            order = float(item[pos+3:].strip())
            item = item[:pos].strip()
        items.append((item, order))
    items.sort(lambda i1, i2: cmp(i2[1], i1[1]))
    return [i[0] for i in items]

def to_unicode(value):
    """
    Converts encoded string to unicode string.

    Uses get_template_encoding_default() to guess source string encoding.
    Handles turbogears.i18n.lazystring correctly.
    """
    if isinstance(value, str):
        # try to make sure we won't get UnicodeDecodeError from the template
        # by converting all encoded strings to Unicode strings
        try:
            value = unicode(value)
        except UnicodeDecodeError:
            try:
                value = unicode(value, get_template_encoding_default())
            except UnicodeDecodeError:
                # fail early
                raise ValueError("Non-unicode string: %r" % value)
    return value

def to_utf8(value):
    """Converts a unicode string to utf-8 encoded plain string.

    Handles turbogears.i18n.lazystring correctly. Does nothing to already encoded string.
    """
    if isinstance(value, str):
        pass
    elif hasattr(value, '__unicode__'):
        value = unicode(value)
    if isinstance(value, unicode):
        value = value.encode('utf-8')
    return value

def get_template_encoding_default(engine_name=None):
    """Returns default encoding for template files (Kid, Genshi, etc.)."""
    if engine_name is None:
        engine_name = config.get('tg.defaultview', 'kid')
    return config.get('%s.encoding' % engine_name, 'utf-8')

def find_precision(value):
    """
    Find precision of some arbitrary value.  The main intention for this function
    is to use it together with turbogears.i18n.format.format_decimal() where one
    has to inform the precision wanted.  So, use it like this:

    format_decimal(some_number, find_precision(some_number))
    """
    decimals = ''
    try:
        stub, decimals = str(value).split('.')
    except ValueError:
        pass
    return len(decimals)

def copy_if_mutable(value, feedback=False):
    if isinstance(value, dict):
        mutable = True
        value = value.copy()
    elif isinstance(value, list):
        mutable = True
        value = value[:]
    else:
        mutable = False
    if feedback:
        return (value, mutable)
    else:
        return value

def fixentities(htmltext):
    # replace HTML character entities with numerical references
    # note: this won't handle CDATA sections properly
    def repl(m):
        entity = htmlentitydefs.entitydefs.get(m.group(1).lower())
        if not entity:
            return m.group(0)
        elif len(entity) == 1:
            if entity in "&<>'\"":
                return m.group(0)
            return "&#%d;" % ord(entity)
        else:
            return entity
    return re.sub("&(\w+);?", repl, htmltext)


__all__ = ["Enum", "setlike",
           "get_package_name", "get_model", "load_project_config",
           "url", "ensure_sequence", "has_arg",
           "DictWrapper", "DictObj", "to_kw", "from_kw", "adapt_call",
           "call_on_stack", "remove_keys",
           "arg_index", "inject_arg", "inject_args", "bind_args",
           "recursive_update", "combine_contexts", "request_available",
           "flatten_sequence", "load_class", "Bunch",
           "parse_http_accept_header", 
           "to_unicode", "to_utf8", "get_template_encoding_default",
           "find_precision", "copy_if_mutable"]
