import unittest

import cherrypy

from turbogears.controllers import error_handler, exception_handler, \
                                   expose, validate, RootController, Controller
from turbogears.errorhandling import FailsafeSchema
from turbogears.util import bind_args
from turbogears import validators
from turbogears import testutil


def _errors_to_str(errors):
    if isinstance(errors, dict):
        return dict(map(lambda (k,v): (k, str(v)), errors.iteritems()))
    else:
        return str(errors)

class MyRoot(RootController):

    def defaulterrorhandler(self, tg_source, tg_errors, tg_exceptions,
                            *args, **kw):
        return dict(title="Default error handler",
                    errors=_errors_to_str(tg_errors), args=args, kw=kw)

    def specialisederrorhandler(self, tg_source, tg_errors, *args, **kw):
        return dict(title="Specialised error handler",
                    errors=_errors_to_str(tg_errors), args=args, kw=kw)

    def defaulterror(self, bar=""):
        return dict(title="Default error provider")
    defaulterror = error_handler(defaulterrorhandler)(defaulterror)
    defaulterror = validate(validators={"bar":validators.StringBoolean()})(
                            defaulterror)
    defaulterror = expose()(defaulterror)

    def specialisederror(self, bar="", baz=""):
        return dict(title="Specialised error provider")
    specialisederror = error_handler(defaulterrorhandler)(
                                             specialisederror)
    specialisederror = error_handler(specialisederrorhandler,
                                     "'baz' in tg_errors")(specialisederror)
    specialisederror = validate(validators={"bar":validators.Int(not_empty=True),
                                            "baz":validators.Email()})(
                                specialisederror)
    specialisederror = expose()(specialisederror)

    def exceptionerror(self):
        raise Exception("Exception 1")
    exceptionerror = exception_handler(defaulterrorhandler)(exceptionerror)
    exceptionerror = expose()(exceptionerror)

    def exceptionerror2(self):
        raise Exception("Exception 2")
    exceptionerror2 = exception_handler(exceptionerror2)(exceptionerror2)
    exceptionerror2 = expose()(exceptionerror2)

    def recursiveerror(self, tg_errors=None, bar=""):
        if tg_errors:
            return dict(title="Recursive error handler")
        else:
            return dict(title="Recursive error provider")
    recursiveerror = error_handler()(recursiveerror)
    recursiveerror = validate(validators={"bar":validators.Int(not_empty=True)})(
                              recursiveerror)
    recursiveerror = expose()(recursiveerror)

    def impliciterror(self, tg_errors=None, bar=""):
        if tg_errors:
            return dict(title="Implicit error handler",
                        tg_errors=str(tg_errors))
        else:
            return dict(title="Implicit error provider")
    impliciterror = validate(validators={"bar":validators.Int(not_empty=True)})(
                             impliciterror)
    impliciterror = expose()(impliciterror)

    def normalmethod(self):
        return dict(title="Normal method")
    normalmethod = expose()(normalmethod)

    def normalmethodcaller(self, bar=""):
        return dict(title="Normal method caller")
    normalmethodcaller = error_handler(normalmethod)(normalmethodcaller)
    normalmethodcaller = validate(validators={
                                  "bar":validators.StringBoolean()})(
                         normalmethodcaller)
    normalmethodcaller = expose()(normalmethodcaller)

    def infiniteloop(self):
        try:
            self.exceptionerror2()
        except Exception, e:
            return dict(title=str(e))
        else:
            return dict(title="Infinite loop provider")
    infiniteloop = expose()(infiniteloop)

    def positionalargs(self, first, second, *args, **kw):
        self.first = first
        self.second = second
        self.third = args[0]
        return dict(title="Positional arguments", first=first, second=second,
                    args=args, bar=kw["bar"])
    positionalargs = error_handler(defaulterrorhandler)(
                                   positionalargs)
    positionalargs = validate(validators={"bar":validators.StringBoolean(),
                                          "second":validators.Int(not_empty=True)})(
                              positionalargs)
    positionalargs = expose()(positionalargs)

    def missingargs(self, bar=""):
        return dict(title="Missing args provider")
    missingargs = error_handler(defaulterrorhandler)(missingargs)
    missingargs = validate(validators={"bar":validators.Int(not_empty=True)})(missingargs)
    missingargs = expose()(missingargs)

    def nohandler2(self, bar=""):
        return dict(title="No handler inner")
    nohandler2 = validate(validators={"bar":validators.Int(not_empty=True)})(nohandler2)
    nohandler2 = expose()(nohandler2)

    def nohandler(self):
        try:
            self.nohandler2("abc")
        except Exception, NotImplementedError:
            return dict(title="Exception raised")
        else:
            return dict(title="No handler")
    nohandler = expose()(nohandler)

    def simpleerrorhandler(self, baz=None):
         return dict(title="Default error handler", baz=baz)

    def bindargs(self, bar=""):
        return dict(title="Bind arguments to error handler")
    bindargs = error_handler(bind_args(baz=123)(simpleerrorhandler))(bindargs)
    bindargs = validate(validators={"bar":validators.Int(not_empty=True)})(bindargs)
    bindargs = expose()(bindargs)

    def notexposed(self, bar, tg_errors = None):
        if tg_errors:
            return dict(title="Not exposed error", bar=bar)
        else:
            return dict(title="Not exposed", bar=bar)
    notexposed = validate(validators={"bar":validators.Int(not_empty=True)})(notexposed)

    def notexposedcaller(self, foo="", bar="", baz=""):
        return self.notexposed(bar)
    notexposedcaller = expose()(notexposedcaller)

    def continuation(self, tg_source):
        self.continuation = True
        return tg_source(self)

    def continuationcaller(self, bar=""):
        return dict(title="Continuation caller")
    continuationcaller = error_handler(continuation)(continuationcaller)
    continuationcaller = validate(validators={"bar":validators.Int(not_empty=True)})(
                                  continuationcaller)
    continuationcaller = expose()(continuationcaller)

    def nest(self, bar=""):
        return dict(title="Nested")
    nest = error_handler(defaulterrorhandler)(nest)
    nest = validate(validators={"bar":validators.Int(not_empty=True)})(nest)
    nest = expose()(nest)

    def failsafenone(self, tg_errors=None, bar="", baz=""):
        return dict(title="No failsafe", bar=bar, baz=baz)
    failsafenone = validate(validators={"bar":validators.Int(not_empty=True),
        "baz":validators.Int(not_empty=True)})(failsafenone)
    failsafenone = expose()(failsafenone)

    def failsafevaluesdict(self, tg_errors=None, bar="", baz=""):
        return dict(title="Failsafe values-dict", bar=bar, baz=baz)
    failsafevaluesdict = validate(validators={"bar":validators.Int(not_empty=True),
        "baz":validators.Int(not_empty=True)}, failsafe_schema=FailsafeSchema.values,
        failsafe_values={"bar":1, "baz":2})(failsafevaluesdict)
    failsafevaluesdict = expose()(failsafevaluesdict)

    def failsafevaluesatom(self, tg_errors=None, bar="", baz=""):
        return dict(title="Failsafe values-atom", bar=bar, baz=baz)
    failsafevaluesatom = validate(validators={"bar":validators.Int(not_empty=True),
        "baz":validators.Int(not_empty=True)}, failsafe_schema=FailsafeSchema.values,
        failsafe_values=13)(failsafevaluesatom)
    failsafevaluesatom = expose()(failsafevaluesatom)

    def failsafemaperrors(self, tg_errors=None, bar="", baz=""):
        return dict(title="Failsafe map errors", bar=str(bar), baz=str(baz))
    failsafemaperrors = validate(validators={"bar":validators.Int(not_empty=True),
        "baz":validators.Int(not_empty=True)}, failsafe_schema=FailsafeSchema.map_errors)(
        failsafemaperrors)
    failsafemaperrors = expose()(failsafemaperrors)

    def failsafeformencode(self, tg_errors=None, bar="", baz=""):
        return dict(title="Formencode if_invalid", bar=bar, baz=baz)
    failsafeformencode = validate(validators={"bar":validators.Int(
        if_invalid=1), "baz":validators.Int(if_invalid=2)})(failsafeformencode)
    failsafeformencode = expose()(failsafeformencode)

    def failsafedefaults(self, tg_errors=None, bar=1, baz=2):
        return dict(title="Failsafe map defaults", bar=bar, baz=baz)
    failsafedefaults = validate(validators={"bar":validators.Int(not_empty=True),
        "baz":validators.Int(not_empty=True)}, failsafe_schema=FailsafeSchema.defaults)(
        failsafedefaults)
    failsafedefaults = expose()(failsafedefaults)

class NestedController(Controller):

    def nest(self, bar=""):
        return dict(title="Nested")
    nest = error_handler()(nest)
    nest = validate(validators={"bar":validators.Int(not_empty=True)})(nest)
    nest = expose()(nest)


class TestErrorHandler(unittest.TestCase):

    def setUp(self):
        cherrypy.root = MyRoot()
        cherrypy.root.nestedcontroller = NestedController()

    def test_defaultErrorHandler(self):
        """ Default error handler. """
        testutil.createRequest("/defaulterror?bar=abc")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/defaulterror?bar=true")
        self.failUnless("Default error provider" in cherrypy.response.body[0])

    def test_specialisedErrorHandler(self):
        """ Error handler specialisation. """
        testutil.createRequest("/specialisederror?bar=abc&baz=a@b.com")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/specialisederror?baz=abc&bar=1")
        self.failUnless("Specialised error handler" in
                        cherrypy.response.body[0])
        testutil.createRequest("/specialisederror?bar=1&baz=a@b.com")
        self.failUnless("Specialised error provider" in
                        cherrypy.response.body[0])

    def test_exceptionErrorHandler(self):
        """ Error handler for exceptions. """
        testutil.createRequest("/exceptionerror")
        self.failUnless("Default error handler" in cherrypy.response.body[0])

    def test_recursiveErrorHandler(self):
        """ Recursive error handler. """
        testutil.createRequest("/recursiveerror?bar=abc")
        self.failUnless("Recursive error handler" in cherrypy.response.body[0])
        testutil.createRequest("/recursiveerror?bar=1")
        self.failUnless("Recursive error provider" in
                        cherrypy.response.body[0])

    def test_implicitErrorHandler(self):
        """ Implicit error handling. """
        testutil.createRequest("/impliciterror?bar=abc")
        self.failUnless("Implicit error handler" in
                        cherrypy.response.body[0])
        testutil.createRequest("/impliciterror?bar=1")
        self.failUnless("Implicit error provider" in
                        cherrypy.response.body[0])

    def test_normalMethodErrorHandler(self):
        """ Normal method as an error handler. """
        testutil.createRequest("/normalmethodcaller?bar=abc")
        self.failUnless("Normal method" in cherrypy.response.body[0])
        testutil.createRequest("/normalmethodcaller?bar=true")
        self.failUnless("Normal method caller" in cherrypy.response.body[0])

    def test_infiniteRecursionPrevention(self):
        """ Infinite recursion prevention. """
        testutil.createRequest("/infiniteloop")
        self.failUnless("Exception 2" in cherrypy.response.body[0])

    def test_positionalArgs(self):
        """ Positional argument validation.  """
        testutil.createRequest("/positionalargs/first/23/third?bar=abc")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/positionalargs/first/abc/third?bar=false")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/positionalargs/first/abc/third?bar=abc")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/positionalargs/first/23/third?bar=true")
        self.failUnless("Positional arguments" in cherrypy.response.body[0])
        self.failUnless(cherrypy.root.first == "first")
        self.failUnless(cherrypy.root.second == 23)
        self.failUnless(cherrypy.root.third == "third")

    def test_missingArgs(self):
        """ Arguments required in validation missing. """
        testutil.createRequest("/missingargs")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/missingargs?bar=12")
        self.failUnless("Missing args provider" in cherrypy.response.body[0])

    def test_nohandler(self):
        """ No error hanlder declared. """
        testutil.createRequest("/nohandler")
        self.failUnless("Exception raised" in cherrypy.response.body[0])

    def test_bindArgs(self):
        """ Arguments can be bond to an error handler. """
        testutil.createRequest("/bindargs")
        self.failUnless("123" in cherrypy.response.body[0])

    def test_notExposed(self):
        """ Validation error handling is decoupled from expose. """
        testutil.createRequest("/notexposedcaller?foo=a&bar=rab&baz=c")
        self.failUnless("Not exposed error" in cherrypy.response.body[0])
        self.failUnless("rab" in cherrypy.response.body[0])

    def test_continuations(self):
        """ Continuations via error handling mechanism. """
        testutil.createRequest("/continuationcaller?bar=a")
        self.failUnless("Continuation caller" in cherrypy.response.body[0])
        self.failUnless(cherrypy.root.continuation == True)

    def test_nested(self):
        """ Potentially ambiguous cases. """
        testutil.createRequest("/nest?bar=a")
        self.failUnless("Default error handler" in cherrypy.response.body[0])
        testutil.createRequest("/nestedcontroller/nest?bar=a")
        self.failUnless("Nested" in cherrypy.response.body[0])

    def test_failsafe(self):
        """ Failsafe values for erroneous input. """
        testutil.createRequest("/failsafenone?bar=a&baz=b")
        self.failUnless('"bar": "a"' in cherrypy.response.body[0])
        self.failUnless('"baz": "b"' in cherrypy.response.body[0])
        testutil.createRequest("/failsafevaluesdict?bar=a&baz=b")
        self.failUnless('"bar": 1' in cherrypy.response.body[0])
        self.failUnless('"baz": 2' in cherrypy.response.body[0])
        testutil.createRequest("/failsafevaluesatom?bar=a&baz=b")
        self.failUnless('"bar": 13' in cherrypy.response.body[0])
        self.failUnless('"baz": 13' in cherrypy.response.body[0])
        testutil.createRequest("/failsafemaperrors?bar=a&baz=b")
        self.failUnless('"bar": "Please enter an integer value"' in
                        cherrypy.response.body[0])
        self.failUnless('"baz": "Please enter an integer value"' in
                        cherrypy.response.body[0])
        testutil.createRequest("/failsafeformencode?bar=a&baz=b")
        self.failUnless('"bar": 1' in cherrypy.response.body[0])
        self.failUnless('"baz": 2' in cherrypy.response.body[0])
        testutil.createRequest("/failsafedefaults?bar=a&baz=b")
        self.failUnless('"bar": 1' in cherrypy.response.body[0],cherrypy.response.body[0])
        self.failUnless('"baz": 2' in cherrypy.response.body[0])
