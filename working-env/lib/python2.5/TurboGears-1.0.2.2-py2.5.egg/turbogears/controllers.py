"""Classes and methods for TurboGears controllers."""
import logging
import re
import urllib
import types
from itertools import izip
import cherrypy
from dispatch import generic, strategy, functions
import turbogears.util as tg_util
import turbogears 
from inspect import isclass
from turbogears import view, database, errorhandling, config
from turbogears.decorator import weak_signature_decorator
from turbogears.validators import Invalid
from turbogears.errorhandling import error_handler, exception_handler

log = logging.getLogger("turbogears.controllers")

unicodechars = re.compile(r"([^\x00-\x7F])")

if config.get("session_filter.on",None) == True:
    if config.get("session_filter.storage_type",None) == "PostgreSQL":
        import psycopg2 
        config.update({'session_filter.get_db':psycopg2.connect(psycopg2.get('sessions.postgres.dsn'))})
    # support for mysql/sqlite/etc here

def _process_output(output, template, format, content_type, mapping, fragment=False):
    """Produces final output form from the data returned from a
    controller method.

    @param tg_format: format of desired output (html or json)
    @param output: the output returned by the controller
    @param template: HTML template to use
    """
    if isinstance(output, dict):
        from turbogears.widgets import js_location

        css = tg_util.setlike()
        js = dict(izip(js_location, iter(tg_util.setlike, None)))
        include_widgets = {}
        include_widgets_lst = config.get("tg.include_widgets", [])

        if config.get("tg.mochikit_all", False):
            include_widgets_lst.insert(0, 'turbogears.mochikit')
            
        for i in include_widgets_lst:
            widget = tg_util.load_class(i)  
            if isclass(widget):
                widget = widget()
            include_widgets["tg_%s" % i.split(".")[-1]] = widget
            for script in widget.retrieve_javascript():
                if hasattr(script, "location"):
                    js[script.location].add(script)
                else:
                    js[js_location.head].add(script)
            css.add_all(widget.retrieve_css())

        for value in output.itervalues():
            if hasattr(value, "retrieve_css"):
                retrieve = getattr(value, "retrieve_css")
                if callable(retrieve):
                    css.add_all(value.retrieve_css())
            if hasattr(value, "retrieve_javascript"):
                retrieve = getattr(value, "retrieve_javascript")
                if callable(retrieve):
                    for script in value.retrieve_javascript():
                        if hasattr(script, "location"):
                            js[script.location].add(script)
                        else:
                            js[js_location.head].add(script)
        output.update(include_widgets)
        output["tg_css"] = css
        #output.update([("tg_js_%s" % str(l), js[l]) for l in js_location])
        for l in iter(js_location):
            output["tg_js_%s" % str(l)] = js[l]

        tg_flash = _get_flash() 
        if not tg_flash == None:
            output["tg_flash"] = tg_flash 
        output = view.render(output, template=template, format=format,
                    mapping=mapping, content_type=content_type,
                    fragment=fragment)
    else:
        if content_type:
            cherrypy.response.headers["Content-Type"] = content_type

    # fix the Safari XMLHttpRequest encoding problem
    try:
        contentType = cherrypy.response.headers["Content-Type"]
        ua = cherrypy.request.headers["User-Agent"]
    except KeyError:
        return output
    if not contentType.startswith("text/"):
        return output
    ua = view.UserAgent(ua)
    enc = tg_util.get_template_encoding_default()
    if ua.browser == "safari":
        if isinstance(output, str):
            output = output.decode(enc)
        output = unicodechars.sub(
            lambda m: "&#x%x;" % ord(m.group(1)), output).encode("ascii")
    if isinstance(output, unicode):
        output = output.encode(enc)
    return output

class BadFormatError(Exception):
    """Output-format exception."""

def validate(form=None, validators=None,
             failsafe_schema=errorhandling.FailsafeSchema.none,
             failsafe_values=None, state_factory=None):
    """Validate input.

    @param form form to validate input from
    @param validators individual validators to use for parameters
    @param failsafe_schema fail-safe schema
    @param failsafe_values replacements for erroneous inputs
    @param state_factory callable which returns the initial state instance for
           validation
    """
    def entangle(func):
        recursion_guard = dict(func=func)
        if callable(form) and not hasattr(form, "validate"):
            init_form = lambda self: form(self)
        else:
            init_form = lambda self: form

        def validate(func, *args, **kw):
            if tg_util.call_on_stack("validate", recursion_guard, 4):
                return func(*args, **kw)
            form = init_form(args and args[0] or kw["self"])
            args, kw = tg_util.to_kw(func, args, kw)

            errors = {}
            if state_factory is not None:
                state = state_factory()
            else:
                state = None

            if form:
                value = kw.copy()
                try:
                    kw.update(form.validate(value, state))
                except Invalid, e:
                    errors = e.unpack_errors()
                    cherrypy.request.validation_exception = e
                cherrypy.request.validated_form = form

            if validators:
                if isinstance(validators, dict):
                    for field, validator in validators.iteritems():
                        try:
                            kw[field] = validator.to_python(
                                kw.get(field, None), state
                                )
                        except Invalid, error:
                            errors[field] = error
                else:
                    try:
                        value = kw.copy()
                        kw.update(validators.to_python(value, state))
                    except Invalid, e:
                        errors = e.unpack_errors()
                        cherrypy.request.validation_exception = e
            cherrypy.request.validation_errors = errors
            cherrypy.request.input_values = kw.copy()
            cherrypy.request.validation_state = state

            if errors:
                kw = errorhandling.dispatch_failsafe(failsafe_schema,
                                            failsafe_values, errors, func, kw)
            args, kw = tg_util.from_kw(func, args, kw)
            return errorhandling.run_with_errors(errors, func, *args, **kw)

        return validate
    return weak_signature_decorator(entangle)

class CustomDispatch(functions.GenericFunction):

    def combine(self,cases):
        strict = [strategy.ordered_signatures,strategy.safe_methods]
        cases = strategy.separate_qualifiers(
            cases,
            primary = strict,
        )
        primary = strategy.method_chain(cases.get('primary',[]))
        if type(primary) != types.FunctionType:
            for i in primary:
                for y in i:
                    return y[1]
        return primary

def _add_rule(_expose, found_default, as_format, accept_format, template,
              rulefunc):
    if as_format == "default":
        if found_default:
            colon = template.find(":")
            if colon == -1:
                as_format = template
            else:
                as_format = template[:colon]
        else:
            found_default = True
    ruleparts = []
    ruleparts.append('kw.get("tg_format", "default") == "%s"'
                % as_format)
    if accept_format:
        ruleparts.append('(accept == "%s" and kw.get("tg_format", '
                '"default") == "default")' % accept_format)
    rule = " or ".join(ruleparts)
    log.debug("Generated rule %s", rule)
    _expose.when(rule)(rulefunc)

    return found_default

def _build_rules(func):
    def _expose(func, accept, allow_json, *args, **kw):
        pass
    _expose = generic(CustomDispatch)(_expose)

    if func._allow_json:
        log.debug("Adding allow_json rule: "
            'allow_json and '
            '(kw.get("tg_format", None) == "json" or accept '
            '=="text/javascript")')
        _expose.when('allow_json '
            'and (kw.get("tg_format", None) == "json" or accept'
            ' =="text/javascript")')(
            lambda _func, accept, allow_json,
                *args, **kw: _execute_func(
                    _func, "json", None, None, None, False, args, kw))

    found_default = False
    for ruleinfo in func._ruleinfo:
        found_default = _add_rule(_expose, found_default, **ruleinfo)

    func._expose = _expose

def expose(template=None, validators=None, allow_json=None, html=None,
           format=None, content_type=None, inputform=None, fragment=False,
           as_format="default", mapping=None, accept_format=None):
    """Exposes a method to the web.

    By putting the expose decorator on a method, you tell TurboGears that
    the method should be accessible via URL traversal. Additionally, expose
    handles the output processing (turning a dictionary into finished
    output) and is also responsible for ensuring that the request is
    wrapped in a database transaction.

    You can apply multiple expose decorators to a method, if
    you'd like to support multiple output formats. The decorator that's
    listed first in your code without as_format or accept_format is
    the default that is chosen when no format is specifically asked for.
    Any other expose calls that are missing as_format and accept_format
    will have as_format implicitly set to the whatever comes before
    the ":" in the template name (or the whole template name if there
    is no ":". For example, <code>expose("json")</code>, if it's not
    the default expose, will have as_format set to "json".
    
    When as_format is set, passing the same value in the tg_format
    parameter in a request will choose the options for that expose
    decorator. Similarly, accept_format will watch for matching
    Accept headers. You can also use both. expose("json", as_format="json",
    accept_format="text/javascript") will choose JSON output for either
    case: tg_format=json as a parameter or Accept: text/javascript as a
    request header.

    Passing allow_json=True to an expose decorator
    is equivalent to adding the decorator just mentioned.

    Each expose decorator has its own set of options, and each one
    can choose a different template or even template engine (you can
    use Kid for HTML output and Cheetah for plain text, for example).
    See the other expose parameters below to learn about the options
    you can pass to the template engine.

    Take a look at the
    <a href="tests/test_expose-source.html">test_expose.py</a> suite
    for more examples.

    @param template "templateengine:dotted.reference" reference along the
            Python path for the template and the template engine. For
            example, "kid:foo.bar" will have Kid render the bar template in
            the foo package.
    @keyparam format format for the template engine to output (if the
            template engine can render different formats. Kid, for example,
            can render "html", "xml" or "xhtml")
    @keyparam content_type sets the content-type http header
    @keyparam allow_json allow the function to be exposed as json
    @keyparam fragment for template engines (like Kid) that generate
            DOCTYPE declarations and the like, this is a signal to
            just generate the immediate template fragment. Use this
            if you're building up a page from multiple templates or
            going to put something onto a page with .innerHTML.
    @keyparam mapping mapping with options that are sent to the template
            engine
    @keyparam as_format designates which value of tg_format will choose
            this expose.
    @keyparam accept_format which value of an Accept: header will 
            choose this expose.
    @keyparam html deprecated in favor of template
    @keyparam validators deprecated. Maps argument names to validator
            applied to that arg
    @keyparam inputform deprecated. A form object that generates the 
            input to this method
    """
    if html:
        template = html
    if not template:
        template = format
    if format == "json" or (format == None and template == None):
        template = "json"
        allow_json = True
    if content_type is None:
        content_type = config.get("tg.content_type", None)

    if config.get("tg.session.automatic_lock",None) == True:
        cherrypy.session.acquire_lock()

    def entangle(func):
        log.debug("Exposing %s", func)
        log.debug("template: %s, format: %s, allow_json: %s, "
            "content-type: %s", template, format, allow_json, content_type)
        if not getattr(func, "exposed", False):
            def expose(func, *args, **kw):
                accept = cherrypy.request.headers.get('Accept', "").lower()
                if not hasattr(func, "_expose"):
                    _build_rules(func)
                if hasattr(cherrypy.request, "in_transaction"):
                    output = func._expose(func, accept, func._allow_json,
                                *args, **kw)
                else:
                    cherrypy.request.in_transaction = True
                    output = database.run_with_transaction(
                            func._expose, func, accept, func._allow_json,
                            *args, **kw)
                return output
            func.exposed = True
            func._ruleinfo = []
            allow_json_from_config = config.get(
                                        "tg.allow_json", False)
            func._allow_json = allow_json_from_config
        else:
            expose = lambda func, *args, **kw: func(*args, **kw)

        func._ruleinfo.insert(0, dict(as_format = as_format,
            accept_format = accept_format, template = template,
            rulefunc = lambda _func, accept, allow_json,
                    *args, **kw:
                    _execute_func(_func, template, format, content_type,
                                mapping, fragment, args, kw)))

        if allow_json:
            func._allow_json = True

        if inputform or validators:
            import warnings
            warnings.warn(
                "Use a separate decorator validate() rather than passing "
                "arguments validators and/or inputform to decorator "
                "expose().",
                DeprecationWarning, 2)
            func = validate(form=inputform, validators=validators)(func)

        return expose
    return weak_signature_decorator(entangle)

def _execute_func(func, template, format, content_type, mapping, fragment, args, kw):
    """Call controller method and process it's output."""
    if config.get("tg.strict_parameters", False):
	    tg_util.remove_keys(kw, ["tg_random", "tg_format"])
    else:
        args, kw = tg_util.adapt_call(func, args, kw)
    if config.get('server.environment', 'development') == 'development':
        # Only output this in development mode: If it's a field storage object,
        # this means big memory usage, and we don't want that in production
        log.debug("Calling %s with *(%s), **(%s)", func, args, kw)
    output = errorhandling.try_call(func, *args, **kw)
    if isinstance(output, list):
        return output
    assert isinstance(output, basestring) or isinstance(output, dict) \
        or isinstance(output, types.GeneratorType), \
           "Method %s.%s() returned unexpected output. Output should " \
           "be of type basestring, dict or generator." % (
            args[0].__class__.__name__, func.__name__)
    if isinstance(output, dict):
        template = output.pop("tg_template", template)
        format= output.pop("tg_format", format)
    if template and template.startswith("."):
        template = func.__module__[:func.__module__.rfind('.')]+template
    return _process_output(output, template, format, content_type, mapping, fragment)

def flash(message):
    """Set a message to be displayed in the browser on next page display."""
    cherrypy.response.simple_cookie['tg_flash'] = tg_util.to_utf8(message)
    cherrypy.response.simple_cookie['tg_flash']['path'] = '/'

def _get_flash():
    """Retrieve the flash message (if one is set), clearing the message."""
    request_cookie = cherrypy.request.simple_cookie
    response_cookie = cherrypy.response.simple_cookie

    def clearcookie():
        response_cookie["tg_flash"] = ""
        response_cookie["tg_flash"]['expires'] = 0
        response_cookie['tg_flash']['path'] = '/'

    if response_cookie.has_key("tg_flash"):
        message = response_cookie["tg_flash"].value
        response_cookie.pop("tg_flash")
        if request_cookie.has_key("tg_flash"):
            # New flash overrided old one sitting in cookie. Clear that old cookie.
            clearcookie()
    elif request_cookie.has_key("tg_flash"):
        message = request_cookie["tg_flash"].value
        if not response_cookie.has_key("tg_flash"):
            clearcookie()
    else:
        message = None
    if message:
        message = unicode(message, 'utf-8')
    return message

class Controller(object):
    """Base class for a web application's controller.

    Currently, this provides positional parameters functionality
    via a standard default method.
    """

class RootController(Controller):
    """Base class for the root of a web application.

    Your web application should have one of these. The root of
    your application is used to compute URLs used by your app.
    """
    is_app_root = True

    msglog = logging.getLogger('cherrypy.msg')
    msglogfunc = {0: msglog.info, 1: msglog.warning, 2: msglog.error}
    def _cp_log_message(self, msg, context = 'nocontext', severity = 0):
        log = self.msglogfunc[severity]
        text = ''.join((context, ': ', msg))
        log(text)

    accesslog = logging.getLogger("turbogears.access")
    def _cp_log_access(self):
        tmpl = '%(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
        try:
            username = cherrypy.request.user_name
            if not username:
                username = "-"
        except AttributeError:
            username = "-"
        s = tmpl % {'h': cherrypy.request.remote_host,
                   'l': '-',
                   'u': username,
                   'r': cherrypy.request.requestLine,
                   's': cherrypy.response.status.split(" ", 1)[0],
                   'b': cherrypy.response.headers.get('Content-Length',
                            '') or "-",
                   'f': cherrypy.request.headers.get('referer', ''),
                   'a': cherrypy.request.headers.get('user-agent', ''),
        }
        self.accesslog.info(s)

Root = RootController

def url(tgpath, tgparams=None, **kw):
    """Computes URLs.

    tgpath can be a list or a string. If the path is absolute (starts
    with a "/"), the server.webpath and the approot of the application
    are prepended to the path. In order for the approot to be
    detected properly, the root object should extend
    controllers.RootController.

    Query parameters for the URL can be passed in as a dictionary in
    the second argument *or* as keyword parameters.
    """
    if not isinstance(tgpath, basestring):
        tgpath = "/".join(list(tgpath))
    if tgpath.startswith("/"):
        if tg_util.request_available():
            check_app_root()
            tgpath = cherrypy.request.app_root + tgpath
        result = config.get("server.webpath", "") + tgpath
    else:
        result = tgpath
    if tgparams is not None:
        tgparams.update(kw)
    else:
        tgparams = kw
    args = []
    for key, value in tgparams.iteritems():
        if value is None:
            continue
        if isinstance(value, unicode):
            value = value.encode("utf8")
        args.append("%s=%s" % (key, urllib.quote(str(value))))
    if args:
        result += "?" + "&".join(args)
    return result

def check_app_root():
    """Sets cherrypy.request.app_root if needed."""
    if hasattr(cherrypy.request, "app_root"):
        return
    found_root = False
    trail = cherrypy.request.object_trail
    top = len(trail) - 1
    # compute the app_root by stepping back through the object
    # trail and collecting up the path elements after the first
    # root we find
    # we can eliminate this if we find a way to use
    # CherryPy's mounting mechanism whenever a new root
    # is hit.
    rootlist = []
    for i in xrange(len(trail) - 1, -1, -1):
        path, obj = trail[i]
        if not found_root and isinstance(obj, RootController):
            if i == top:
                break
            found_root = True
        if found_root and i > 0:
            rootlist.insert(0, path)
    app_root = "/".join(rootlist)
    if not app_root.startswith("/"):
        app_root = "/" + app_root
    if app_root.endswith("/"):
        app_root = app_root[:-1]
    cherrypy.request.app_root = app_root

def redirect(redirect_path, redirect_params=None, **kw):
    """
    Redirect (via cherrypy.HTTPRedirect).
    Raises the exception instead of returning it, this to allow
    users to both call it as a function or to raise it as an exeption.
    """
    raise cherrypy.HTTPRedirect(
                    url(tgpath=redirect_path, tgparams=redirect_params, **kw))

__all__ = ["expose", "validate", "redirect", "flash",
           "Root", "RootController", "Controller",
           "error_handler", "exception_handler",
          ]
