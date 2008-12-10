from unittest import TestCase
from turbogears import widgets
import turbogears
from turbogears import controllers
from turbogears import validators
from turbogears import testutil
import cherrypy
from datetime import datetime

class MyFormFields(widgets.WidgetsList):
    #XXX: Since allow_extra_fields should be removed from validators.Schema we
    #      Need a validator for every input-expecting widget
    name = widgets.TextField(validator=validators.String())
    age = widgets.TextField(validator=validators.Int(), default=0)
    date = widgets.CalendarDatePicker(validator=validators.DateConverter(
                                            if_empty=datetime.now()))

myform = widgets.TableForm(fields=MyFormFields())
                           
class MyRoot(controllers.RootController):

    def index(self):
        return dict(form=myform)
    index = turbogears.expose(html="turbogears.tests.form")(index)

    def usemochi(self):
        return dict(mochi=turbogears.mochikit, form=myform)
    usemochi = turbogears.expose(html="turbogears.tests.form")(usemochi)

    def testform(self, name, date, age, tg_errors=None):
        if tg_errors:
            self.has_errors = True
        self.name = name
        self.age = age
        self.date = date
    testform = turbogears.validate(form=myform)(testform)
    testform = turbogears.expose(html="turbogears.tests.othertemplate")(
                                 testform)

    def testform_new_style(self, name, date, age):
        if cherrypy.request.validation_errors:
            self.has_errors = True
        self.name = name
        self.age = age
        self.date = date
    testform_new_style = turbogears.validate(form=myform)(testform_new_style)
    testform_new_style = turbogears.expose()(testform_new_style)


def test_form_translation():
    "Form input is translated into properly converted parameters"
    root = MyRoot()
    cherrypy.root = root
    testutil.createRequest("/testform?name=ed&date=11/05/2005&age=5")
    assert root.name == "ed"
    print root.age
    assert root.age == 5

def test_form_translation_new_style():
    "Form input is translated into properly converted parameters"
    root = MyRoot()
    cherrypy.root = root
    testutil.createRequest("/testform_new_style?name=ed&date=11/05/2005&age=5&")
    assert root.name == "ed"
    print root.age
    assert root.age == 5

def test_invalid_form_with_error_handling():
    "Invalid forms can be handled by the method"
    root = cherrypy.root
    testutil.createRequest("/testform?name=ed&age=edalso&date=11/05/2005")
    assert root.has_errors

def test_css_should_appear():
    "CSS should appear when asked for"
    root = cherrypy.root
    testutil.createRequest("/")
    print cherrypy.response.body[0]
    assert "calendar-system.css" in cherrypy.response.body[0]

def test_javascript_should_appear():
    "JavaScript should appear when asked for"
    root = cherrypy.root
    testutil.createRequest("/")
    print cherrypy.response.body[0]
    assert "calendar.js" in cherrypy.response.body[0]

def test_include_mochikit():
    "JSLinks (and MochiKit especially) can be included easily"
    root = cherrypy.root
    testutil.createRequest("/usemochi")
    print cherrypy.response.body[0]
    assert "MochiKit.js" in cherrypy.response.body[0]

def test_mochikit_everywhere():
    "MochiKit can be included everywhere by setting tg.mochikit_all"
    root = cherrypy.root
    turbogears.config.update({"global":{"tg.mochikit_all" : True}})
    testutil.createRequest("/")
    turbogears.config.update({"global":{"tg.mochikit_all" : False}})
    print cherrypy.response.body[0]
    assert "MochiKit.js" in cherrypy.response.body[0]

def test_include_widgets():   
    "Any widget Can be included everywhere by  setting tg.include_widgets"
    root = cherrypy.root
    turbogears.config.update({"global":{"tg.include_widgets" : ["turbogears.mochikit"]}})
    testutil.createRequest("/")
    turbogears.config.update({"global":{"tg.include_widgets" : None}})
    print cherrypy.response.body[0]
    assert "MochiKit.js" in cherrypy.response.body[0]


class State(object):
    counter = 0
class AddingValidator(validators.FancyValidator):
    def _to_python(self, value, state=None):
        state.counter += 1
        return value
class AddingSchema(validators.Schema):
    a = AddingValidator()
    b = AddingValidator()
class AddingNestedSchema(AddingSchema):
    c = AddingSchema()

class TestValidationState(TestCase):

    class Controller(controllers.RootController):
        def validate(self, a, b, c):
            return 'counter: %d' % cherrypy.request.validation_state.counter
        validate = turbogears.expose()(validate)
        validate = turbogears.validate(validators=AddingNestedSchema(), 
                                       state_factory=State)(validate)

    def __init__(self, *args, **kw):
        super(TestValidationState, self).__init__(*args, **kw)
        cherrypy.root = self.Controller()

    def test_counter_is_incremented(self):
        # parameter values are irrelevant
        url = '/validate?a=1&b=2&c.a=3&c.b=4'
        testutil.create_request(url)
        body = cherrypy.response.body[0]
        print body
        msg = "Validation state is not handled properly"
        # 4 == 1 (a) + 1(b) + 1(c.a) + 1(c.b)
        self.failUnless('counter: 4' in body, msg)

   
