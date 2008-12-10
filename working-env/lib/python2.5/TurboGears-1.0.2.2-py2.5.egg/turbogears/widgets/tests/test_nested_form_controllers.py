import turbogears
import cherrypy
from turbogears import widgets
from turbogears import controllers
from turbogears import validators
from turbogears import testutil

myform = widgets.TableForm(fields = [ 
    widgets.FieldSet(
        name = "p_data",
        fields = [
            widgets.TextField(name="name"),
            widgets.TextField(name="age", 
                validator=validators.Int()),
        ]),
])

class MyRoot(controllers.RootController):
    def testform(self, p_data, tg_errors=None):
        if tg_errors:
            self.has_errors = True
        self.name = p_data['name']
        self.age = p_data['age']
    testform = turbogears.validate(form=myform)(testform)
    testform = turbogears.expose(html="turbogears.tests.othertemplate")(
                                 testform)

    def set_errors(self):
        self.has_errors = True

    def testform_new_style(self, p_data):
        self.name = p_data['name']
        self.age = p_data['age']
    testform_new_style = turbogears.validate(form=myform)(testform_new_style)
    testform_new_style = turbogears.error_handler(set_errors)(testform_new_style)
    testform_new_style = turbogears.expose()(testform_new_style)


def test_form_translation_new_style():
    "Form input is translated into properly converted parameters"
    root = MyRoot()
    cherrypy.root = root
    testutil.createRequest("/testform_new_style?p_data.name=ed&p_data.age=5")
    assert root.name == "ed"
    print root.age
    assert root.age == 5

def test_invalid_form_with_error_handling():
    "Invalid forms can be handled by the method"
    root = cherrypy.root
    testutil.createRequest("/testform_new_style?p_data.name=ed&p_data.age=edalso")
    assert root.has_errors
