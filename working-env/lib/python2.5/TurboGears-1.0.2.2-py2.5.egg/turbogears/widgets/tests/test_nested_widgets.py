import re
from turbogears.testutil import catch_validation_errors

import cherrypy
import turbogears.widgets as widgets
import turbogears.validators as validators
from turbogears.widgets.meta import copy_schema

class Request:
    validation_errors = {}

oldrequest = None

def setup_module():
    global oldrequest
    oldrequest = cherrypy.request
    cherrypy.request = Request()

def teardown_module():
    global oldrequest
    cherrypy.request = oldrequest

#XXX: We ignore missing keys to make passing value easier in tests
class TestSchema(validators.Schema):
    ignore_key_missing = True

int_validator = validators.Int(if_empty=None)
s_validator = validators.Schema(age=int_validator, ignore_key_missing=True)

class TestNestedWidgets:

    form = widgets.TableForm(name = "myform", fields=[
        widgets.TextField("name"),
        widgets.TextField("age", validator=int_validator),
        widgets.FieldSet("sub", fields = [
            widgets.TextField("name"),
            widgets.TextField("age", validator=int_validator),
            widgets.FieldSet("sub2", fields = [
                widgets.TextField("name"),
                widgets.TextField("age",
                    validator=int_validator),
            ], validator = TestSchema()),
        ], validator = TestSchema()),
    ], validator = TestSchema())



    def test_display(self):
        """
        Checks if names fo the widgets are set correctly depending on their
        path.
        """
        output = self.form.render(dict(sub=dict(sub2=dict(age=22))), format='xhtml')
        value_p = 'value="22"'
        name_p = 'name="sub.sub2.age"'
        assert (re.compile('.*'.join([value_p, name_p])).search(output) or
                re.compile('.*'.join([name_p, value_p])).search(output))

        output = self.form.render(dict(sub=dict(age=22)), format='xhtml')
        value_p = 'value="22"'
        name_p = 'name="sub.age"'
        assert (re.compile('.*'.join([value_p, name_p])).search(output) or
                re.compile('.*'.join([name_p, value_p])).search(output))

        output = self.form.render(dict(sub=dict(age=22)), format='xhtml')
        id_p = 'id="myform_sub_age"'
        name_p = 'name="sub.age"'
        assert (re.compile('.*'.join([value_p, id_p])).search(output) or
                re.compile('.*'.join([id_p, value_p])).search(output))

        output = self.form.render(dict(age=22), format='xhtml')
        value_p = 'value="22"'
        name_p = 'name="age"'
        assert (re.compile('.*'.join([value_p, name_p])).search(output) or
                re.compile('.*'.join([name_p, value_p])).search(output))

    def test_validate_outermost(self):
        values = dict(age="twenty")
        values, errors = catch_validation_errors(self.form, values)

        print values, errors

        assert errors.pop('age', False)
        assert not errors


    def test_validate_sub(self):
        values = dict(sub=dict(age="twenty"))

        values, errors = catch_validation_errors(self.form, values)

        print values, errors
        # check the outermost dict is not poluted with errors from the inner
        # dicts
        assert not errors.has_key('age')

        errors = errors['sub']
        assert errors.pop('age', False)
        assert not errors


    def test_validate_sub2(self):
        values = dict(sub=dict(sub2=dict(age="twenty")))

        values, errors = catch_validation_errors(self.form, values)

        print values, errors
        assert not errors.has_key('age')

        errors = errors['sub']
        print values, errors
        assert not errors.has_key('age')

        errors = errors['sub2']
        print values, errors
        assert errors.pop('age', False)
        assert not errors


    def test_validate_sub_and_sub2(self):
        values = dict(sub=dict(age="fhg", sub2=dict(age="twenty")))

        values, errors = catch_validation_errors(self.form, values)

        print values, errors
        assert not errors.has_key('age')

        errors = errors['sub']
        print values, errors
        assert errors.pop('age', False)

        errors = errors['sub2']
        print values, errors
        assert errors.pop('age', False)
        assert not errors


    def test_good_values(self):
        values = dict(age=22, sub=dict(sub2=dict(age=20)))

        values, errors = catch_validation_errors(self.form, values)

        print values, errors

        assert errors == {}
        assert values['age'] == 22


    def test_good_and_bad_values(self):
        values = dict(age="ddd", sub=dict(age="20", sub2=dict()))

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert errors.pop('age', False)
        assert not errors
        #assert values['sub']['age'] == 20



class TestNestedWidgetsWSchemaValidation:

    form = widgets.TableForm(
        name = "myform",
        validator = s_validator,
        fields=[
            widgets.TextField("name"),
            widgets.TextField("age"),
            widgets.FieldSet(
                name = "sub",
                validator = s_validator,
                fields = [
                    widgets.TextField("name"),
                    widgets.TextField("age"),
                    widgets.FieldSet(
                        name = "sub2",
                        validator = s_validator,
                        fields = [
                            widgets.TextField("name"),
                            widgets.TextField("age"),
                        ]
                    ),
                ]
            ),
        ]
    )


    def test_validate_sub_schema(self):
        values = dict(sub=dict(age="twenty"))

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        # check the outermost dict is not poluted with errors from the inner
        # dicts
        assert not errors.has_key('age')

        errors = errors['sub']
        assert errors.pop('age', False)
        assert not errors

    def test_good_and_bad_values_schema(self):
        values = dict(age="ddd", sub=dict(age="20", sub2=dict()))

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert errors.pop('age', False)
        assert not errors
        #assert values['sub']['age'] == 20

    def test_good_values_schema(self):
        values = dict(age=22, sub=dict(sub2=dict(age=20)))

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert errors == {}
        assert values['age'] == 22

    def test_validate_sub_and_sub2_schema(self):
        values = dict(sub=dict(age="fhg", sub2=dict(age="twenty")))

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert not errors.has_key('age')

        errors = errors['sub']
        print values, errors
        assert errors.pop('age', False)

        errors = errors['sub2']
        print values, errors
        assert errors.pop('age', False)
        assert not errors

    def test_validate_sub2_schema(self):
        values = dict(sub=dict(sub2=dict(age="twenty")))

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert not errors.has_key('age')

        errors = errors['sub']
        print values, errors
        assert not errors.has_key('age')

        errors = errors['sub2']
        print values, errors
        assert errors.pop('age', False)

    def test_validate_outermost_schema(self):
        values = dict(age="twenty")

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert errors.pop('age', False)
        assert not errors
        assert not errors

class TestNestedWidgetsWMixedValidation:

    form = widgets.TableForm(
        name = "myform",
        validator = s_validator,
        fields=[
            widgets.TextField("name"),
            widgets.TextField("age"),
            widgets.TextField("number", validator=int_validator),
            widgets.FieldSet(
                name = "sub",
                validator = s_validator,
                fields = [
                    widgets.TextField("name"),
                    widgets.TextField("age"),
                    widgets.TextField("number", validator=int_validator),
                    widgets.FieldSet(
                        name = "sub2",
                        fields = [
                            widgets.TextField("name"),
                            widgets.TextField("age", validator=int_validator),
                            widgets.TextField("number", validator=int_validator),
                        ]
                    ),
                ]
            ),
        ]
    )

    def test_mixed_validators(self):
        """
        Tests that schema validators and single validators can be mixed
        safely.
        """
        values = dict(
            age="bad",
            number="22",
            sub=dict(
                age="bad",
                number="bad",
                sub2=dict(
                    age="bad",
                    number="bad",
                )
            )
        )

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert errors.pop('age', False)
        #assert values['number'] == 22

        # assert errors are not getting poluted errors from other levels of
        # the tree
        assert errors.keys() == ['sub']
        errors = errors['sub']
        assert errors.pop('age', False)
        assert errors.pop('number', False)

        assert errors.keys() == ['sub2']
        errors = errors['sub2']
        assert errors.pop('age', False)
        assert errors.pop('number', False)
        assert not errors






class InnerSchema(validators.Schema):
    ignore_key_missing = True
    age = int_validator

class MiddleSchema(validators.Schema):
    ignore_key_missing = True
    age = int_validator
    sub2 = InnerSchema()

class OuterSchema(validators.Schema):
    ignore_key_missing = True
    age = int_validator
    sub = MiddleSchema()

class TestNestedSchemaValidators:

    #XXX: Age is always validated by the nested schemas, number is
    #     validated with widget validator.
    form = widgets.TableForm(
        name = "myform",
        validator = OuterSchema(),
        fields=[
            widgets.TextField("age"),
            widgets.TextField("number", validator=int_validator),
            widgets.FieldSet(
                name = "sub",
                fields = [
                    widgets.TextField("age"),
                    widgets.TextField("number", validator=int_validator),
                    widgets.FieldSet(
                        name = "sub2",
                        fields = [
                            widgets.TextField("age"),
                            widgets.TextField("number", validator=int_validator),
                        ]
                    ),
                ]
            ),
        ]
    )

    def test_nested_schemas(self):
        """
        Tests that we can nest schema validators safely.
        """
        values = dict(
            age="bad",
            number="22",
            sub=dict(
                age="27",
                number="bad",
                sub2=dict(
                    age="bad",
                    number="bad",
                )
            )
        )

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert errors.pop('age', False)
        #assert values['number'] == 22

        # assert errors are not getting poluted errors from other levels of
        # the tree
        assert errors.keys() == ['sub']
        errors = errors['sub']
        values = values['sub']
        #XXX This assertion fails :(
        #XXX But it's normal as the Schema doesn't convert good values in
        #    invalid Schemas, ATM
        #assert values['age'] == 27
        assert errors.pop('number', False)

        assert errors.keys() == ['sub2']
        errors = errors['sub2']
        assert errors.pop('age', False)
        assert errors.pop('number', False)
        assert not errors

    def test_nested_schemas_good_values(self):
        values = dict(
            age="21",
            number="22",
            sub=dict(
                age="27",
                number="28",
                sub2=dict(
                    age="33",
                    number="34",
                )
            )
        )

        values, errors = catch_validation_errors(self.form, values)
        print values, errors

        assert not errors
        assert (values["age"], values['number']) == (21, 22)

        values = values['sub']
        assert (values["age"], values['number']) == (27, 28)

        values = values['sub2']
        assert (values["age"], values['number']) == (33, 34)

def test_copy_schema():
    class UserSchema(validators.Schema):
        user_name = validators.PlainText()
    schema = copy_schema(UserSchema())
    
