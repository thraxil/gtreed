import itertools

import cherrypy

from turbogears import widgets, validators
from turbogears.testutil import catch_validation_errors

import sets

class Request:
    input_values = {}
    validation_errors = {}

oldrequest = None

def setup_module():
    global oldrequest
    oldrequest = cherrypy.request
    cherrypy.request = Request()

def teardown_module():
    global oldrequest
    cherrypy.request = oldrequest

def test_label():
    """Tests simple labels"""
    label = widgets.Label("foo")
    rendered = label.render("The Foo", format='xhtml')
    assert """<label id="foo" class="label">The Foo</label>""" == rendered

def test_default_value():
    """Widgets can have a default value"""
    textfield = widgets.TextField("name")
    output = textfield.render(format='xhtml')
    assert 'value' not in output
    textfield = widgets.TextField("name", default="ed kowalczyk")
    output = textfield.render(format='xhtml')
    assert 'value="ed kowalczyk"' in output

def test_labeltext():
    "Label text defaults to the capitalized name"
    textfield = widgets.TextField("name")
    assert textfield.label == "Name"

def test_validation():
    "Values can be converted to/from python values"
    textfield = widgets.TextField("age", validator=validators.Int())
    output = textfield.render(2, format="xhtml")
    assert 'value="2"' in output
    value = "2"
    value = textfield.validator.to_python(value)
    print value
    assert value == 2

def test_unicode_input():
    "Unicode values are rendered correctly"
    tf = widgets.TextField("name", validator=validators.UnicodeString())
    output = tf.render(u'Pete \u011C', format='xhtml')
    assert 'value="Pete \xc4\x9c"' in output
    return # XXX: the folowing causes OTHER(!) tests to fail!
    try:
        print tf.render('Pete \xfe\xcd')
    except ValueError, e:
        pass
    else:
        assert 0, "ValueError not raised: non-unicode input not detected"
    #tf2 = widgets.TextField("name", validator=validators.String())

# simon: failed inputs are no longer being removed.
#
#def test_failed_validation():
#    "If validation fails, the bad value should be removed from the input"
#    textfield = widgets.TextField("age", validator=validators.Int())
#    values = dict(age="ed")
#    try:
#        textfield.validate(values)
#    except validators.Invalid:
#        pass
#    assert not values.has_key("age")

def test_widget_css():
    "Widgets can require CSS resources"
    css = widgets.CSSLink(mod=widgets.static, name="foo.css")
    css2 = widgets.CSSLink(mod=widgets.static, name="foo.css")
    assert css == css2
    cssset = sets.Set()
    cssset.add(css)
    cssset.add(css2)
    assert len(cssset) == 1
    css3 = widgets.CSSLink(mod=widgets.static, name="bar.css")
    assert css3 != css2
    css4 = widgets.CSSSource(src="foo.css")
    assert css != css4
    rendered = css.render(format='xhtml')
    assert 'link' in rendered
    assert 'href="/tg_widgets/turbogears.widgets/foo.css"' in rendered
    assert 'type="text/css"' in rendered
    assert 'rel="stylesheet"' in rendered
    assert 'media="all"' in rendered
    rendered = css.render(media="printer", format='xhtml')
    assert 'media="printer"' in rendered
    css = widgets.CSSSource("h1 { color: black }")
    rendered = css.render(format='xhtml')
    assert 'h1 { color: black }' in rendered

def test_widget_js():
    "Widgets can require JavaScript resources"
    js = widgets.JSLink(mod=widgets.static, name="foo.js")
    js2 = widgets.JSLink(mod=widgets.static, name="foo.js")
    assert js == js2
    js3 = widgets.CSSLink(mod=widgets.static, name="bar.js")
    assert js3 != js2
    js4 = widgets.JSSource(src="foo.js")
    assert js != js4
    rendered = js.render(format='xhtml').strip()
    expected = '<script src="/tg_widgets/turbogears.widgets/foo.js"' \
               ' type="text/javascript"></script>'
    assert rendered == expected
    js = widgets.JSSource("alert('hello');")
    rendered = js.render(format='xhtml').strip()
    expected = """<script type="text/javascript">alert('hello');</script>"""
    assert rendered == expected

def test_widget_url():
    "It might be needed to insert an URL somewhere"
    url = widgets.URLLink(link='http://www.turbogears.org')
    rendered = url.render(format='xhtml')
    expected = """<a href="http://www.turbogears.org"></a>"""
    assert rendered == expected
    url = widgets.URLLink(link='http://www.turbogears.org', text='TurboGears Website')
    rendered = url.render(format='xhtml')
    expected = """<a href="http://www.turbogears.org">TurboGears Website</a>"""
    assert rendered == expected
    url = widgets.URLLink(link='http://www.turbogears.org', text='TurboGears Website', target="_blank")
    rendered = url.render(format='xhtml')
    expected = """<a href="http://www.turbogears.org" target="_blank">TurboGears Website</a>"""
    assert rendered == expected

def test_submit():
    sb = widgets.SubmitButton()
    r = sb.render(format='xhtml')
    assert 'name' not in r
    assert 'id' not in r
    r = sb.render('Krakatoa', format='xhtml')
    assert 'id' not in r
    assert 'name' not in r
    sb = widgets.SubmitButton(name='blink')
    r = sb.render(format='xhtml')
    assert 'name="blink"' in r
    assert 'id="blink"' in r
    r = sb.render('Krakatoa', format='xhtml')
    assert 'name="blink"' in r
    assert 'id="blink"' in r
    sb = widgets.SubmitButton(name='submit')
    r = sb.render(format='xhtml')
    assert 'name="submit"' in r
    assert 'id="submit"' in r
    r = sb.render('Krakatoa', format='xhtml')
    assert 'name="submit"' in r
    assert 'id="submit"' in r
    sb = widgets.SubmitButton(default='Save')
    r = sb.render(format='xhtml')
    assert 'value="Save"' in r
    r = sb.render(value='Discard', format='xhtml')
    assert 'value="Discard"' in r

def test_threadsafety():
    "Widget attributes can't be changed after init, for threadsafety"
    w = widgets.TextField("bar")
    w.display()
    try:
        w.name = "foo"
        assert False, "should have gotten an exception"
    except ValueError:
        pass

def test_checkbox():
    "A CheckBox has not a value and is not checked by default"
    w = widgets.CheckBox("foo")
    output = w.render(format='xhtml')
    assert 'name="foo"' in output
    assert 'value' not in output
    assert 'checked' not in output
    output = w.render(value=True, format='xhtml')
    assert 'checked' in output
    w = widgets.CheckBox("foo", default=True)
    output = w.render(format='xhtml')
    assert 'checked' in output
    output = w.render(value=False, format='xhtml')
    assert 'checked' not in output
    #CheckBox should accept alternate validators
    value = w.validator.to_python('checked')
    assert value == True
    w = widgets.CheckBox("foo", validator=validators.NotEmpty())
    value = w.validator.to_python('checked')
    assert value == 'checked'

def test_field_class():
    "The class of a field corresponds to the name of its python class"
    w = widgets.TextField("bar")
    output = w.render(format='xhtml')
    assert 'class="%s"' % w.__class__.__name__

def test_field_id():
    "The id of a field corresponds to the name of the field"
    w = widgets.TextField("bar")
    output = w.render(format='xhtml')
    assert 'id="bar"'

def test_selection_field():
    """A selection field presents a list of options that can be changed
    dynamically. One or more options can be selected/checked by default
    or dynamically."""
    options = [(1, "python"), (2, "java"), (3, "pascal")]
    w = widgets.SingleSelectField(options=options)
    output = w.render(format='xhtml')
    assert 'python' in output
    assert 'java' in output
    assert 'pascal' in output
    output = w.render(value=2, format='xhtml')
    assert '<option value="1">' in output
    assert '<option selected="selected" value="2">' in output
    assert '<option value="3">' in output
    w = widgets.SingleSelectField(options=options, default=3)
    output = w.render(format='xhtml')
    assert '<option value="1">' in output
    assert '<option value="2">' in output
    assert '<option selected="selected" value="3">' in output
    output = w.render(options=options + [(4, "cobol"), (5, "ruby")],
        format='xhtml')
    assert 'python' in output
    assert 'java' in output
    assert 'pascal' in output
    assert 'cobol' in output
    assert 'ruby' in output
    output = w.render(options=options
        + [(4, "cobol"), (5, "ruby")], value=5, format='xhtml')
    assert '<option value="1">' in output
    assert '<option value="2">' in output
    assert '<option value="3">' in output
    assert '<option value="4">' in output
    assert '<option selected="selected" value="5">' in output
    w = widgets.MultipleSelectField(options=options, default=[1, 3])
    output = w.render(format='xhtml')
    assert '<option selected="selected" value="1">' in output
    assert '<option value="2">' in output
    assert '<option selected="selected" value="3">' in output
    output = w.render(options=options
        + [(4, "cobol"), (5, "ruby")], value=[2, 4, 5], format='xhtml')
    assert '<option value="1">' in output
    assert '<option selected="selected" value="2">' in output
    assert '<option value="3">' in output
    assert '<option selected="selected" value="4">' in output
    assert '<option selected="selected" value="5">' in output

def test_callable_options():
    """Widgets support callable options passed to the
    constructor or dynamically"""
    def options_func1():
        return [(1, "coke"), (2, "pepsi"), (3, "redbull")]
    def options_func2():
        return [(1, "python"), (2, "java"), (3, "pascal")]
    w = widgets.SingleSelectField(options=options_func1)
    output = w.render(format='xhtml')
    assert 'coke' in output
    assert 'pepsi' in output
    assert 'redbull' in output
    output = w.render(options=options_func2, format='xhtml')
    assert 'coke' not in output
    assert 'pepsi' not in output
    assert 'redbull' not in output
    assert 'python' in output
    assert 'java' in output
    assert 'pascal' in output

class TestParams:
    class A(widgets.Widget):
        template = """<tag xmlns:py="http://purl.org/kid/ns#" a="${a}" />"""
        params = ["a", "b", "c"]
    class B(widgets.Widget):
        params = ["b", "c", "d"]
    class C(A, B):
        params = ["c", "d", "e"]

    def test_building_params(self):
        """
        Tests that the list of params is built correctly. Must be the
        union of all params from all bases
        """
        # for easy equivalenece testing
        self.C.params.sort()
        assert ''.join(self.C.params) == "abcde"

    def test_default_values(self):
        """
        Test that params which are not initialized at the ctor. nor
        at the subclass declarartion default to None.
        """
        a = self.A()
        assert a.a == None
        output = a.render(format='xhtml')
        print output
        assert 'a=' not in output

    def test_overridal(self):
        """
        Test we can override a template_var in the ctor, and at display.
        Both from the class and it's bases.
        """
        a = self.A(a="test")
        assert a.a == "test"
        c = self.C(a="test")
        assert c.a == "test"
        output = c.render(format='xhtml')
        print output
        assert 'a="test"' in output
        output = c.render(a="another", format='xhtml')
        print output
        assert 'a="another"' in output

def test_template_overridal():
    """ Tests that we can override an instances template at construction time
    and get it automatically compiled """
    new_template = """
    <label xmlns:py="http://purl.org/kid/ns#"
        for="${name}"
        class="${field_class}"
        py:content="value"
        custom_template="True"
    />
    """
    l = widgets.Label(template=new_template)
    output = l.render(format='xhtml')
    assert 'custom_template="True"' in output

def test_simple_widget_attrs():
    """A simple widget supports attributes passed to the constructor or at
    display time."""
    w = widgets.TextField(name="foo", attrs={'onchange':'python', 'size':'10'})
    output = w.render(format='xhtml')
    assert 'onchange="python"' in output
    assert 'size="10"' in output
    output = w.render(attrs={'onclick':'java'}, format='xhtml')
    assert 'onchange="python"' not in output
    assert 'size="10"' not in output
    assert 'onclick="java"' in output
    output = w.render(attrs={'onchange':'java', 'size':'50', 'alt':None},
        format='xhtml')
    assert 'onchange="java"' in output
    assert 'size="50"' in output
    assert 'alt' not in output
    assert 'onclick' not in output

def test_textfield():
    class MyField(widgets.WidgetsList):
        blonk = widgets.TextField()
    class MyFieldOverrideName(widgets.WidgetsList):
        blonk = widgets.TextField(name="blink")

    tf = widgets.ListForm(fields=MyField())
    r = tf.render(format='xhtml')
    assert 'name="blonk"' in r
    assert 'id="form_blonk"' in r
    tf = widgets.ListForm(fields=MyFieldOverrideName())
    r = tf.render(format='xhtml')
    assert 'name="blink"' in r
    assert 'id="form_blink"' in r

def test_textarea():
    w = widgets.TextArea(rows=20, cols=30)
    output = w.render(format='xhtml')
    assert 'rows="20"' in output
    assert 'cols="30"' in output
    output = w.render(rows=50, cols=50, format='xhtml')
    assert 'rows="50"' in output
    assert 'cols="50"' in output
    assert '> +++ </textarea>' in w.render(' +++ ', format='xhtml')

def test_render_field_for():
    """
    Using the render_field_for method of a FormFieldsContainer we can
    render the widget instance associated to a particular field name.
    """
    class MyFields(widgets.WidgetsList):
        name = widgets.TextField()
        age = widgets.TextArea()
    tf = widgets.ListForm(fields=MyFields())
    output = tf.render_field_for("name", format='xhtml')
    assert 'name="name"' in output
    assert '<input' in output
    assert 'type="text"' in output
    output = tf.render_field_for("name", attrs={'onclick':'hello'},
        format='xhtml')
    assert 'onclick="hello"' in output
    output = tf.render_field_for("age", format='xhtml')
    assert 'name="age"' in output
    assert '<textarea' in output
    output = tf.render_field_for("age", rows="1000", cols="2000",
        format='xhtml')
    assert 'rows="1000"' in output
    assert 'cols="2000"' in output

def test_css_classes():
    """A FormField supports css_classes, they are added after the original
    class. They can be provided at construction or at display time, the latter
    overrides the former but attrs overrides everything"""
    w = widgets.TextField(name="foo")
    output = w.render(format='xhtml')
    assert 'class="textfield"' in output
    w = widgets.TextField(name="foo", css_classes=["bar", "bye"])
    output = w.render(format='xhtml')
    assert 'class="textfield bar bye"' in output
    output = w.render(css_classes=["coke", "pepsi"], format='xhtml')
    assert 'class="textfield coke pepsi"' in output
    w = widgets.TextField(name="foo",
        css_classes=["bar", "bye"], attrs={'class':'again'})
    output = w.render(format='xhtml')
    assert 'class="again"' in output
    output = w.render(css_classes=["coke", "pepsi"], format='xhtml')
    assert 'class="again"' in output
    output = w.render(css_classes=["coke", "pepsi"],
        attrs={'class':'funny'}, format='xhtml')
    assert 'class="funny"' in output

def test_ticket272():
    """ TextFields with a "name" attribute = "title" should be OK """
    w = widgets.TableForm(fields=[widgets.TextField(name='title')])
    output = w.render(format='xhtml')
    assert 'value' not in output


class TestSchemaValidation:
    """ Tests the validation of a CompoundWidget is done correctly with a
    Schema validator and no validators on the child widgets. """
    class Fields(widgets.WidgetsList):
        name = widgets.TextField()
        age = widgets.TextField()
        passwd = widgets.PasswordField()
        passwd2 = widgets.PasswordField()

    class FieldsSchema(validators.Schema):
        chained_validators = [validators.FieldsMatch('passwd', 'passwd2')]

        name = validators.UnicodeString()
        age = validators.Int()
        passwd = validators.NotEmpty()
        passwd2 = validators.UnicodeString()

    form = widgets.TableForm(fields=Fields(), validator=FieldsSchema())

    def test_goodvalues(self):
        values = dict(name=u'Jos\xc3\xa9', age="99", passwd="fado",
                      passwd2="fado")

        values, errors = catch_validation_errors(self.form, values)
        print values
        assert values['age'] == 99
        assert not errors

    def test_badvalues(self):
        values = dict(name=u'Jos\xc3\xa9', age="99", passwd="fado",
                      passwd2="fadO")

        values, errors = catch_validation_errors(self.form, values)
        print errors
        assert "passwd2" in errors.keys()

class TestSchemaValidationWithChildWidgetsValidators:
    """ Tests the validation of a CompoundWidget is done correctly with a
    Schema validator and independent validators on the each of the child
    widgets. """
    class Fields(widgets.WidgetsList):
        name = widgets.TextField(validator = validators.UnicodeString())
        age = widgets.TextField(validator = validators.Int())
        passwd = widgets.PasswordField(validator = validators.NotEmpty())
        passwd2 = widgets.PasswordField(validator = validators.UnicodeString())

    class FieldsSchema(validators.Schema):
        chained_validators = [validators.FieldsMatch('passwd', 'passwd2')]


    form = widgets.TableForm(fields=Fields(), validator=FieldsSchema())

    def test_goodvalues(self):
        values = dict(name=u'Jos\xc3\xa9', age="99", passwd="fado",
                      passwd2="fado")

        values, errors = catch_validation_errors(self.form, values)
        print values
        assert values['age'] == 99
        assert not errors.keys()

    def test_widget_validator_failure(self):
        values = dict(name=u'Jos\xc3\xa9', age="ninetynine", passwd="fado",
                      passwd2="fado")
        values, errors = catch_validation_errors(self.form, values)
        print values, errors
        assert "age" in errors.keys()


    def test_widget_validator_and_schema_failure(self):
        values = dict(name=u'Jos\xc3\xa9', age="ninetynine", passwd="fado",
                      passwd2="fadO")
        values, errors = catch_validation_errors(self.form, values)
        print values, errors
        assert "age" in errors.keys()
        assert "passwd2" in errors.keys()

def test_param_descriptor():
    class Base(widgets.Widget):
        params = ["param1", "param2"]
        param1 = "original"
        param2 = "original"

    class Sub(Base):
        param1 = lambda self: "overrided"
        param2 = "overrided"

    base = Base()
    assert base.param1 == "original", "descriptor is not created correctly"
    assert base.param2 == "original", "descriptor is not created correctly"

    sub = Sub()
    assert sub.param1 == "overrided", "callable params are not being overrided"
    assert sub.param2 == "overrided", "normal params are not being overrided"

def test_param_descriptor_mutable_class_attrs():
    class Wid(widgets.Widget):
        params = ['attrs']
        attrs = {}

    w1 = Wid(attrs={'test':True})
    w2 = Wid()

    assert w1.attrs == {'test':True}
    assert w2.attrs == {}

def test_param_descriptor_properties():
    class Wid(widgets.Widget):
        params = ['attrs']
        def _set_attrs(self, attrs):
            self._attrs = attrs
        def _get_attrs(self):
            return self._attrs
        attrs = property(_get_attrs, _set_attrs)

    w1 = Wid(attrs={'test':True})
    assert w1.attrs == {'test':True}

def test_dict_as_validator():
    class Foo(widgets.InputWidget):
        validator = validators.Int()
    a = Foo()
    b = Foo(validator=dict(not_empty=True))
    assert not a.validator.not_empty
    assert b.validator.not_empty
    assert a.validator is not b.validator

def test_params_doc():
    """Tests params_doc are picked from all bases giving priority to the
    widget's own"""
    class BaseA(widgets.Widget):
        params_doc = {'a':1}
    class BaseB(widgets.Widget):
        params_doc = {'b':2}
    class WidgetC(BaseA, BaseB):
        params_doc = {'c':3, 'a':4}
    widC = WidgetC()
    assert widC.params_doc == {'a':4, 'b':2, 'c':3}

def test_selectfield_with_with_non_iterable_option_elements():
    options = ["python", "java", "pascal"]
    w = widgets.SingleSelectField(options=options)
    output = w.render(format='xhtml')
    assert '<option value="python">' in output
    assert '<option value="java">' in output
    assert '<option value="pascal">' in output
    output = w.render(value="python", format='xhtml')
    assert '<option selected="selected" value="python">' in output
    assert '<option value="java">' in output
    assert '<option value="pascal">' in output
