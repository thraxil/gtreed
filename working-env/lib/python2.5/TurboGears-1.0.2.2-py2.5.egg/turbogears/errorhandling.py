import sys
from itertools import izip, repeat, islice
from inspect import getargspec

import cherrypy
from dispatch import generic, NoApplicableMethods, strategy

from turbogears.util import inject_args, adapt_call, call_on_stack, has_arg, \
                            remove_keys, Enum, combine_contexts
from turbogears.decorator import func_eq
from turbogears.genericfunctions import MultiorderGenericFunction


default = strategy.default

def dispatch_error(controller, tg_source, tg_errors, tg_exceptions,
                   *args, **kw):
    """Dispatch error.

    Error handler is a function registered via register_handler or if no
    such decorator was applied, the method triggering the error.
    """
dispatch_error = generic(MultiorderGenericFunction)(dispatch_error)

def _register_implicit_errh(controller, tg_source, tg_errors,
                                     tg_exceptions, *args, **kw):
    """Register implicitly declared error handler and re-dispatch.

    Any method declaring tg_errors parameter is considered an implicitly
    declared error handler.
    """
    error_handler(tg_source)(tg_source)
    return dispatch_error(controller, tg_source, tg_errors, tg_exceptions,
                          *args, **kw)
_register_implicit_errh = dispatch_error.when(
    "(tg_errors and has_arg(tg_source, 'tg_errors'))", order=3)(
    _register_implicit_errh)

def _register_implicit_exch(controller, tg_source, tg_errors,
                                         tg_exceptions, *args, **kw):
    """Register implicitly declared exception handler and re-dispatch.

    Any method declaring tg_exceptions parameter is considered an
    implicitly declared exception handler.
    """
    exception_handler(tg_source)(tg_source)
    return dispatch_error(controller, tg_source, tg_errors, tg_exceptions,
                          *args, **kw)
_register_implicit_exch = dispatch_error.when(
    "(tg_exceptions and has_arg(tg_source, 'tg_exceptions'))", order=3)(
    _register_implicit_exch)

def dispatch_error_adaptor(func):
    """Construct a signature isomorphic to dispatch_error.

    The actual handler will receive only arguments explicitly
    declared.
    """
    def adaptor(controller, tg_source, tg_errors, tg_exceptions, *args, **kw):
        args, kw = inject_args(func, {"tg_source":tg_source,
                                      "tg_errors":tg_errors,
                                      "tg_exceptions":tg_exceptions},
                               args, kw, 1)
        args, kw = adapt_call(func, args, kw, 1)
        return func(controller, *args, **kw)
    return adaptor

def try_call(func, self, *args, **kw):
    """Call function, catch and dispatch any resulting exception."""
    # turbogears.database import here to avoid circular imports
    from turbogears.database import _use_sa
    try:
        return func(self, *args, **kw)
    except Exception, e:
        if isinstance(e, cherrypy.HTTPRedirect) or \
           call_on_stack("dispatch_error",
                         {"tg_source":func, "tg_exception":e}, 4):
            raise
        elif _use_sa() and getattr(cherrypy.request, "in_transaction", None):
            # We're in a transaction and using SA, let 
            # database.run_with_transaction handle and dispatch 
            # the exception
            raise
        else:
            exc_type, exc_value, exc_trace = sys.exc_info()
            remove_keys(kw, ("tg_source", "tg_errors", "tg_exceptions"))
            try:
                output = dispatch_error(self, func, None, e, *args, **kw)
            except NoApplicableMethods:
                raise exc_type, exc_value, exc_trace
            else:
                del exc_trace
                return output

def run_with_errors(errors, func, self, *args, **kw):
    """Branch execution depending on presence of errors."""
    if errors:
        if hasattr(self, "validation_error"):
            import warnings
            warnings.warn(
                "Use decorator error_handler() on per-method base "
                "rather than defining a validation_error() method.",
                DeprecationWarning, 2)
            return self.validation_error(func.__name__, kw, errors)
        else:
            remove_keys(kw, ("tg_source", "tg_errors", "tg_exceptions"))
            try:
                return dispatch_error(self, func, errors, None, *args, **kw)
            except NoApplicableMethods:
                raise NotImplementedError("Method %s.%s() has no applicable "
                  "error handler." % (self.__class__.__name__, func.__name__))
    else:
        return func(self, *args, **kw)

def register_handler(handler=None, rules=None):
    """Register handler as an error handler for decorated method.

    If handler is not given, method is considered it's own error handler.

    rules can be a string containing an arbitrary logical Python expression
    to be used as dispatch rule allowing multiple error handlers for a
    single method.

    register_handler decorator is an invariant.
    """
    def register(func):
        when = "func_eq(tg_source, func)"
        if rules:
            when += " and (%s)" % rules
        dispatch_error.when(dispatch_error.parse(when, *combine_contexts(
            depth=[0, 1])), order=1)(dispatch_error_adaptor(handler or func))
        return func
    return register

def bind_rules(pre_rules):
    """Prepend rules to error handler specialisation."""
    def registrant(handler=None, rules=None):
        when = pre_rules
        if rules:
            when += " and (%s)" % rules
        return register_handler(handler, when)
    return registrant

error_handler = bind_rules("tg_errors")
exception_handler = bind_rules("tg_exceptions")

FailsafeSchema = Enum("none", "values", "map_errors", "defaults")

def dispatch_failsafe(schema, values, errors, source, kw):
    """Dispatch fail-safe mechanism for failed inputs."""
dispatch_failsafe = generic()(dispatch_failsafe)

def _failsafe_none(schema, values, errors, source, kw):
    """No fail-safe values."""
    return kw
_failsafe_none = dispatch_failsafe.when(strategy.default)(_failsafe_none)

def _failsafe_values_dict(schema, values, errors, source, kw):
    """Map errorneus inputs to values."""
    kw.update([(key, values[key]) for key in errors.iterkeys()
                                      if key in values])
    return kw
_failsafe_values_dict = dispatch_failsafe.when(
    "schema is FailsafeSchema.values and isinstance(values, dict) and "
    "isinstance(errors, dict)")(_failsafe_values_dict)

def _failsafe_values_atom(schema, values, errors, source, kw):
    """Map all errorneus inputs to a single value."""
    kw.update(izip(errors.iterkeys(), repeat(values)))
    return kw
_failsafe_values_atom = dispatch_failsafe.when(
    "schema is FailsafeSchema.values and isinstance(errors, dict)")(
    _failsafe_values_atom)

def _failsafe_map_errors(schema, values, errors, source, kw):
    """Map errorneus inputs to coresponding exceptions."""
    kw.update(errors)
    return kw
_failsafe_map_errors = dispatch_failsafe.when(
    "schema is FailsafeSchema.map_errors and isinstance(errors, dict)")(
    _failsafe_map_errors)

def _failsafe_defaults(schema, values, errors, source, kw):
    """Map errorneus inputs to method defaults."""
    argnames, defaultvals = getargspec(source)[::3]
    defaults = dict(izip(islice(argnames, len(argnames) - len(defaultvals),
                         None), defaultvals))
    kw.update([(key, defaults[key]) for key in errors.iterkeys()
                                        if key in defaults])
    return kw
_failsafe_defaults = dispatch_failsafe.when(
    "schema is FailsafeSchema.defaults and isinstance(errors, dict)")(
    _failsafe_defaults)

__all__ = ["dispatch_error", "dispatch_error_adaptor", "try_call",
           "run_with_errors", "default", "register_handler", "FailsafeSchema",
           "dispatch_failsafe", "error_handler", "exception_handler",
           ]
