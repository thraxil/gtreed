"""Template processing for TurboGears view templates."""

import os
import imp
import sys
import re
import logging
from itertools import chain
from itertools import cycle as icycle
from urllib import quote_plus

import cherrypy
import pkg_resources

import turbogears
from turbogears import identity, config
from turbogears.i18n import i18n_filter, get_locale
from turbogears.util import DictObj, DictWrapper, get_template_encoding_default, adapt_call

log = logging.getLogger("turbogears.view")

baseTemplates = []
variable_providers = []
root_variable_providers = []
engines = dict()

# Deprecation of variableProviders
def print_warning(func):
    def _print_warning(*args, **kw):
        import warnings
        warnings.warn(
            "Use of variableProviders is deprecated, use variable_providers"
            "instead.",
            DeprecationWarning, 2)
        return func(*args, **kw)
    return _print_warning

class MetaDeprecatedVariableProviders(type):
    def __new__(cls, name, bases, dict):
        for (key, value) in dict.items():
            if key == "__metaclass__":
                continue
            if callable(value):
                dict[key] = print_warning(value)
        return type.__new__(cls,name, bases, dict)

class DeprecatedVariableProviders(list):
    __metaclass__ = MetaDeprecatedVariableProviders

    def append(self, *args, **kw):
        super(DeprecatedVariableProviders, self).append(*args, **kw)

    def count(self, *args, **kw):
        return super(DeprecatedVariableProviders, self).count(*args, **kw)

    def extend(self, *args, **kw):
        super(DeprecatedVariableProviders, self).extend(*args, **kw)

    def index(self, *args, **kw):
        return super(DeprecatedVariableProviders, self).index(*args, **kw)

    def insert(self, *args, **kw):
        super(DeprecatedVariableProviders, self).insert(*args, **kw)

    def pop(self, *args, **kw):
        return super(DeprecatedVariableProviders, self).pop(*args, **kw)

    def remove(self, *args, **kw):
        super(DeprecatedVariableProviders, self).remove(*args, **kw)

    def reverse(self, *args, **kw):
        super(DeprecatedVariableProviders, self).reverse(*args, **kw)

    def sort(self, *args, **kw):
        super(DeprecatedVariableProviders, self).sort(*args, **kw)

variableProviders = DeprecatedVariableProviders()

def _choose_engine(template):
    if isinstance(template, basestring):
        colon = template.find(":")
        if colon > -1:
            enginename = template[:colon]
            template = template[colon+1:]
        else:
            engine = engines.get(template, None)
            if engine:
                return engine, None, template
            enginename = config.get("tg.defaultview", "kid")
    else:
        enginename = config.get("tg.defaultview", "kid")
    engine = engines.get(enginename, None)
    if not engine:
        raise KeyError, \
            "Template engine %s is not installed" % enginename
    return engine, template, enginename


def render(info, template=None, format=None ,content_type=None, mapping=None, fragment=False):
    """Renders data in the desired format.

    @param info: the data itself
    @type info: dict
    @param format: "html", "xml" or "json"
    @type format: string
    @param fragment: passed through to tell the template if only a
                     fragment of a page is desired
    @type fragment: bool
    @param template: name of the template to use
    @type template: string
    """
    template = info.pop("tg_template", template)
    if not info.has_key("tg_flash"):
        if config.get("tg.empty_flash", True):
            info["tg_flash"] = None
    engine, template, enginename = _choose_engine(template)
    if  not content_type and getattr(engine, 'get_content_type', None):
        ua = getattr(cherrypy.request.headers, "User-Agent", None)
        ua = UserAgent(ua)
        content_type = engine.get_content_type(ua)
    elif not content_type:
        content_type = "text/html"
    if content_type == 'text/html' and enginename in ('genshi', 'kid'):
        charset = get_template_encoding_default(enginename)
        content_type = content_type + '; charset=' + charset
    cherrypy.response.headers["Content-Type"] = content_type
    if not format:
        format = config.get("%s.outputformat" % enginename, "html") 
    args, kw = adapt_call(engine.render, args= [],
                kw = dict(info=info, format=format, fragment=fragment, template=template, mapping=mapping), start=1)
    return engine.render(**kw)

def transform(info, template):
    "Create ElementTree representation of the output"
    engine, template, enginename = _choose_engine(template)
    return engine.transform(info, template)

def loadBaseTemplates():
    """Loads base templates for use by other templates.
    By listing templates in turbogears.view.baseTemplates, these templates will
    automatically be loaded so that the "import" statement in a template
    will work.
    """
    log.debug("Loading base templates")
    for template in baseTemplates:
        engine, template, enginename = _choose_engine(template)
        if sys.modules.has_key(template):
            del sys.modules[template]
        engine.load_template(template)

NOTGIVEN = []

class cycle:
    """
    Loops forever over an iterator. Wraps the itertools.cycle method
    but provides a way to get the current value via the 'value' attribute

    >>> from turbogears.view.base import cycle
    >>> oe = cycle(('odd','even'))
    >>> oe
    None
    >>> oe.next()
    'odd'
    >>> oe
    'odd'
    >>> oe.next()
    'even'
    >>> oe.next()
    'odd'
    >>> oe.value
    'odd'
    """
    value = None
    def __init__(self,iterable):
        self._cycle = icycle(iterable)
    def __str__(self):
        return self.value.__str__()
    def __repr__(self):
        return self.value.__repr__()
    def next(self):
        self.value = self._cycle.next()
        return self.value


def selector(expression):
    """If the expression is true, return the string 'selected'. Useful for
    HTML <option>s."""
    if expression:
        return "selected"
    else:
        return None

def checker(expression):
    """If the expression is true, return the string "checked". This is useful
    for checkbox inputs.
    """
    if expression:
        return "checked"
    else:
        return None

def ipeek(it):
    """Lets you look at the first item in an iterator. This is a good way
    to verify that the iterator actually contains something. This is useful
    for cases where you will choose not to display a list or table if there
    is no data present.
    """
    it = iter(it)
    try:
        item = it.next()
        return chain([item], it)
    except StopIteration:
        return None

safariua = re.compile(r"Safari/(\d+)")

class UserAgent:
    """Representation of the user's browser.

    Provides information about the type of browser, browser version,
    etc. This currently contains only the information needed for work
    thus far. (msie, firefox, safari browser types, plus safari version
    info.)
    """
    def __init__(self, useragent=None):
        self.majorVersion = None
        self.minorVersion = None
        if not useragent:
            useragent = "unknown"
        if useragent.find("MSIE") > -1:
            self.browser = "msie"
        elif useragent.find("Firefox") > -1:
            self.browser = "firefox"
        else:
            isSafari = safariua.search(useragent)
            if isSafari:
                self.browser = "safari"
                build = int(isSafari.group(1))
                # this comes from:
                # http://developer.apple.com/internet/safari/uamatrix.html
                if build >= 412:
                    self.majorVersion = "2"
                    self.minorVersion = "0"
                elif build >= 312:
                    self.majorVersion = "1"
                    self.minorVersion = "3"
                elif build >= 125:
                    self.majorVersion = "1"
                    self.minorVersion = "2"
                elif build >= 85:
                    self.majorVersion = "1"
                    self.minorVersion = "0"
            elif useragent == "unknown" or useragent is None:
                self.browser = "unknown"
            else:
                self.browser = "unknown: %s" % useragent

class DeprecatedDictWrapper(DictWrapper):
    """Wraps access with a deprecation warning."""

    def __getattr__(self,name):
        import warnings
        warnings.warn(
            "The use of 'std' inside your templates is deprecated,"
            " use 'tg' instead.",
            DeprecationWarning, 2)
        return super(DeprecatedDictWrapper, self).__getattr__(name)

def stdvars():
    """Creates an DictObj with variables that should be available in all
    templates. These variables are:

    useragent
        a UserAgent object with information about the browser
    selector
        the selector function
    checker
        the checker function
    tg_js
        the path to the JavaScript libraries
    ipeek
        the ipeek function
    cycle
        cycle through a set of values
    quote_plus
        the urllib quote_plus function
    url
        the turbogears.url function for creating flexible URLs
    identity
        the current visitor's identity information
    locale
        the default locale
    inputs
        input values from a form
    errors
        validation errors
    request
        the cherrypy request
    config
        the cherrypy config get function

    Additionally, you can add a callable to turbogears.view.variable_providers
    that can add more variables to this list. The callable will be
    called with the vars DictObj after these standard variables have
    been set up.
    """
    try:
        useragent = cherrypy.request.headers["User-Agent"]
        useragent = UserAgent(useragent)
    except:
        useragent = UserAgent()
    vars = DictObj(
        useragent=useragent, selector=selector,
        tg_js="/" + turbogears.startup.webpath + "tg_js",
        tg_toolbox="/" + turbogears.startup.webpath + "tg_toolbox",
        widgets="/" + turbogears.startup.webpath + "tg_widgets",
        tg_static="/" + turbogears.startup.webpath + "tg_static",
        ipeek=ipeek, cycle=cycle, quote_plus=quote_plus, checker=checker,
        url = turbogears.url, identity=identity.current, config=config.get,
        locale = get_locale(),
        errors = getattr(cherrypy.request, "validation_errors", {}),
        inputs = getattr(cherrypy.request, "input_values", {}),
        request = cherrypy.request)
    for provider in variable_providers + variableProviders:
        provider(vars)
    deprecated_vars = DeprecatedDictWrapper(vars)
    root_vars = dict()
    for provider in root_variable_providers:
        provider(root_vars)
    root_vars.update(dict(tg=vars, std=deprecated_vars))
    return root_vars

def load_engines():
    config = turbogears.config
    engine_options ={
        "mako.directories" : config.get("mako.directories", []),
        "mako.output_encoding" : config.get("mako.output_encoding", "utf-8"),
        "genshi.encoding" : config.get("genshi.encoding", "utf-8"),
        "genshi.default_doctype" : config.get("genshi.default_doctype", None),
        "genshi.variable_lookup" : config.get("genshi.variable_lookup", "strict"),
        "kid.encoding" : config.get("kid.encoding", "utf-8"),
        "kid.assume_encoding" : config.get("kid.assume_encoding", "utf-8"),
        "kid.precompiled" : config.get("kid.precompiled", False),
        "kid.i18n.run_template_filter" : config.get("i18n.run_template_filter",
                                                  False),
        "kid.i18n_filter" : i18n_filter,
        "kid.sitetemplate" : config.get("tg.sitetemplate",
                            "turbogears.view.templates.sitetemplate"),
        "kid.reloadbases" : config.get("kid.reloadbases", False)
    }
    for entrypoint in pkg_resources.iter_entry_points(
                                            "python.templating.engines"):
        engine = entrypoint.load()
        engines[entrypoint.name] = engine(stdvars, engine_options)
load_engines()
