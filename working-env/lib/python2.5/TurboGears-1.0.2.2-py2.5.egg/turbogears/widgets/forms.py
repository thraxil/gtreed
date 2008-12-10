from cherrypy import request
from turbogears import validators, expose
from turbogears.util import setlike, Bunch, request_available
from turbogears.widgets.base import Widget, CompoundWidget, WidgetsList, \
                                    CoreWD, RenderOnlyWD

try:
    set
except NameError:
    from sets import Set as set

__all__ = ["InputWidget", "CompoundInputWidget", "RepeatingInputWidget",
           "FormField", "FormFieldsContainer", "CompoundFormField",
           "RepeatingFormField", "Label", "TextField", "PasswordField",
           "HiddenField", "FileField", "Button", "SubmitButton", 
           "ResetButton", "ImageButton", "CheckBox", "TextArea",
           "SelectionField", "SingleSelectField", "MultipleSelectField", 
           "RadioButtonList", "CheckBoxList", "FieldSet", 
           "RepeatingFieldSet", "Form", "TableForm", "ListForm", 
           "WidgetsList"]

#############################################################################
# Functions and classes to manage input widgets                             #
#############################################################################
def append_to_path(widget, repetition):
    path = []
    if request_available():
        if hasattr(request, "tg_widgets_path"):
            path = request.tg_widgets_path
        else:
            request.tg_widgets_path = path
    if (not path) or (path[-1].widget is not widget):
        path.append(Bunch(widget=widget,
                          repetition=repetition))
        return True
    else:
        return False

def pop_from_path():
    if request_available() and hasattr(request, "tg_widgets_path"):
        request.tg_widgets_path.pop()

def get_path(default_widget, default_repetition):
    default_path = [Bunch(widget=default_widget,
                          repetition=default_repetition)]
    return getattr(request, "tg_widgets_path", default_path)

def update_path(func):
    def _update_path(self, *args, **kw):
        update = append_to_path(self, None)
        returnval = func(self, *args, **kw)
        if update:
            pop_from_path()
        return returnval
    return _update_path

def adapt_path(path):
    return [(i.widget.name, i.repetition) for i in path]

def path_from_item(item, base_path=None):
    path = []
    if isinstance(item, basestring):
        path = item.split('.')
        index = 0
        for key in path:
            if '-' in key:
                a, b = key.split('-')
                path[index] = (a, int(b))
            else:
                path[index] = (key, None)
            index += 1
    elif hasattr(item, "name"):
        path = [(item.name, None)]
    if base_path:
        if not isinstance(base_path[0], tuple):
            base_path = adapt_path(base_path)
        path = base_path + path
    return path

def retrieve_value_by_path(value, path):
    if not path:
        return None
    else:
        if not isinstance(path[0], tuple):
            path = adapt_path(path)
        returnval = value
        for name, index in path:
            if isinstance(returnval, dict):
                returnval = returnval.get(name)
            if index is not None:
                if isinstance(returnval, list):
                    try:
                        returnval = returnval[index]
                    except IndexError:
                        returnval = None
                else:
                    returnval = None
        return returnval

def retrieve_params_by_path(params, path):
    if not path:
        return None
    else: 
        if not isinstance(path[0], tuple):
            path = adapt_path(path)
        for name, index in path:
            params_to_parse = params.copy()
            params = {}
            for k,v in params_to_parse.iteritems():
                if isinstance(v, dict):
                    if name in v:
                        params[k] = v[name]
                        if index is not None:
                            if isinstance(params[k], list):
                                try:
                                    params[k] = params[k][index]
                                except IndexError:
                                    params[k] = None
                            else:
                                params[k] = None
        return params

def build_name_from_path(path, repeating_marker='-', nesting_marker='.'):
    name = []
    for item in path:
        if item.repetition is not None:
            name.append(item.widget.name + repeating_marker + str(item.repetition))
        else:
            name.append(item.widget.name)
    return nesting_marker.join(name)

###############################################################################
# Base class for a widget that can generate input fort the app.
###############################################################################

class InputWidget(Widget):
    validator = None
    params = ["convert"]
    params_doc = {'convert': 'Should the value be coerced by the validator at '
                             'display?'}
    convert = True

    def __init__(self, name=None, validator=None, **params):
        """Initializes an input widget.

        It accepts the following parameters (besides those listed at params):

          name: 
             Name of the input element. Will be the name of the variable
             the widget's input will be available at when submitted.

          validator: 
             Formencode validator that will validate and coerce the input
             this widget generates.
        """
        if name is not None and ('-' in name or '.' in name):
            raise ValueError, ("The name of an InputWidget must not contain "
                               "the '-' or '.' characters")
        super(InputWidget, self).__init__(name, **params)
        if validator:
            self.validator = validator

    def _get_path(self):
        return get_path(self, None)[:]
    _get_path = update_path(_get_path)
    path = property(_get_path)

    def _get_name_path(self):
        if self.path and getattr(self.path[0].widget, "form", False):
            return self.path[1:]
        else:
            return self.path
    name_path = property(_get_name_path)

    def _get_is_validated(self):
        if self.path:
            validated_form = getattr(request, "validated_form", None)
            form = self.path[0].widget
            if form is validated_form:
                return True
            else:
                return False
        else:
            return False
    is_validated = property(_get_is_validated)

    def _retrieve_validator_from_validation_schema(self):
        root_widget = self.path[0].widget
        if root_widget is self:
            return self.validator
        else:
            if getattr(root_widget, "form", False):
                name_path = self.name_path
            else:
                name_path = self.name_path[1:]
            validator = root_widget.validator
            for name in [i.widget.name for i in name_path]:
                if hasattr(validator, "fields"):
                    validator = validator.fields.get(name)
                elif hasattr(validator, "validators"):
                    for v in validator.validators:
                        if hasattr(v, "fields") and (name in v.fields):
                            validator = v.fields[name]
                            break
                else:
                    break
            return validator

    def adjust_value(self, value, **params):
        if hasattr(request, "input_values") and self.is_validated:
            input_submitted = True
            iv = retrieve_value_by_path(request.input_values, self.name_path)
        else:
            input_submitted = False
            iv = None
        # there are some input fields that when nothing is checked/selected
        # instead of sending a nice name="" are totally missing from
        # input_values, this little workaround let's us manage them nicely
        # without interfering with other types of fields, we need this to
        # keep track of their empty status otherwise if the form is going to be
        # redisplayed for some errors they end up to use their defaults values
        # instead of being empty since FE doesn't validate a failing Schema.
        # posterity note: this is also why we need if_missing=None in
        # validators.Schema, see ticket #696.
        no_input_if_empty = getattr(self, "no_input_if_empty", False)
        if iv is not None or (input_submitted and no_input_if_empty):
            value = iv
        else:
            if value is None:
                value = self.default
            if self.validator and params["convert"] and not input_submitted:
                value = self.validator.from_python(value)
        return value

    def display(self, value=None, **params):
        return super(InputWidget, self).display(value, **params)
    display = update_path(display)

    def _get_fq_name(self):
        return build_name_from_path(self.name_path)
    _get_fq_name = update_path(_get_fq_name)
    fq_name = property(_get_fq_name)

    def _get_error(self):
        errors = getattr(request, "validation_errors", {})
        return retrieve_value_by_path(errors, self.name_path)
    _get_error = update_path(_get_error)
    error = property(_get_error)

    def update_params(self, d):
        super(InputWidget, self).update_params(d)
        d["name"] = build_name_from_path(self.name_path)
        errors = getattr(request, "validation_errors", {})
        d["error"] = retrieve_value_by_path(errors, self.name_path)

class CompoundInputWidget(CompoundWidget, InputWidget):
    def update_params(self, params):
        super(CompoundInputWidget, self).update_params(params)
        params['error_for'] = lambda f: self.error_for(f, True)

    def value_for(self, item, value):
        """Return the value for a child widget. ``item`` is the child
        widget instance or it's name, ``value`` is a dict containing the
        value for this compound widget."""
        path = path_from_item(item)
        return retrieve_value_by_path(value, path) 

    def params_for(self, item, **params):
        """Return the parameters for a child widget. ``item`` is the child
        widget instance or it's name, ``params`` is a dict containing the
        parameters passed to this compound widget."""
        path = path_from_item(item)
        return retrieve_params_by_path(params, path)

    def error_for(self, item, suppress_errors=False):
        """Return's the Invalid exception associated to a child widget from 
        request local storage. ``item`` is the child widget instance or it's
        name."""
        if self.is_validated:
            path = path_from_item(item, self.name_path)
            errors = getattr(request, "validation_errors", {})
            returnval = retrieve_value_by_path(errors, path)
            if suppress_errors and \
               isinstance(returnval, dict) or isinstance(returnval, list):
                return None
            else:
                return returnval
        else:
            return None

    def dictify_value(self, value):
        """Converts a value into a dict suitable for propagating values to
        child widgets. If value is a dict it will pass thorugh, if it other
        kind of object, attributes which match child widgets' names will be 
        tried to fetch."""
        if isinstance(value, dict):
            return value
        else:
            value_as_dict = {}
            for w in self.iter_member_widgets():
                try:
                    value_as_dict[w.name] = getattr(value, w.name)
                except AttributeError:
                    pass
            return value_as_dict

    def adjust_value(self, value=None, **params):
        """Adjust a value for displaying in a widget."""
        if value is not None:
            value = self.dictify_value(value)
        return super(CompoundWidget, self).adjust_value(value, **params)

class RepeatingRange(object):
    def __init__(self, repetitions, bunch):
        self.__sequence = repetitions
        self.__next_value = 0
        self.__bunch = bunch

    def __iter__(self):
        return self

    def next(self):
        try:
            value = self.__sequence[self.__next_value]
        except IndexError:
            raise StopIteration
        else:
            self.__next_value += 1
            self.__bunch.repetition = value
            return value

class RepeatingInputWidget(CompoundInputWidget):
    """Base class for a compound widget which can be repeated."""
    repeating = True
    params = ["repetitions"]
    params_doc = {'repetitions': 'Number of repetitions that should be '
                                 'rendered'}
    repetitions = 1

    def update_params(self, d):
        path_reference = self.path[-1]
        repetition = path_reference.repetition
        if repetition is not None:
            path_reference.repetition = None
        super(RepeatingInputWidget, self).update_params(d)
        if repetition is None:
            repetitions = d.pop("repetitions")
            if isinstance(repetitions, int):
                repetitions = range(repetitions)
        else:
            repetitions = [repetition]
        d["repetitions"] = RepeatingRange(repetitions, path_reference)

    def value_for(self, item, value):
        """Return the value for a child widget. ``item`` is the child
        widget instance or it's name, ``value`` is a dict containing the
        value for this compound widget."""
        if isinstance(value, list):
            try:
                value = value[self.path[-1].repetition]
            except IndexError:
                value = None
        else:
            value = None
        path = path_from_item(item)
        return retrieve_value_by_path(value, path) 

    def params_for(self, item, **params):
        """Return the parameters for a child widget. ``item`` is the child
        widget instance or it's name, ``params`` is a dict containing the
        parameters passed to this compound widget."""
        item_params = {}
        for k,v in params.iteritems():
            if isinstance(v, list) and k is not "repetitions":
                try:
                    item_params[k] = v[self.path[-1].repetition]
                except IndexError:
                    pass
        path = path_from_item(item)
        return retrieve_params_by_path(item_params, path)
    
    def dictify_value(self, value):
        """Converts a list of values into a list of dicts suitable for 
        propagating values to child widgets. If value is a list of dicts it 
        will pass thorugh, if it other kind of object, attributes which match 
        child widgets' names will be
        tried to fetch."""
        return [super(RepeatingInputWidget, self).dictify_value(v)
                for v in value]

#############################################################################
# Base classes                                                              #
#############################################################################
class FormField(InputWidget):
    """An input widget that can be included inside a Form or Fieldset.

    It accepts the following parameters (besides those listed at params):

    label
       The label text that the container form/fieldset will generate for the 
       widget. If empty, the capitalized name will be used.
    help_text
       The help text that the container form/fieldset will generate for the 
       widget.
    """
    _name = "widget"
    label = None
    help_text = None
    params = ["field_class", "css_classes"]
    params_doc = {'field_class' : 'CSS class for the field',
                  'css_classes' : 'List of extra CSS classes for the field'}
    field_class = None
    css_classes = []

    def _get_name(self):
        return self._name
    def _set_name(self, name):
        self._name = name
        if self.label is None:
            self.label = name.capitalize()
    name = property(_get_name, _set_name)

    def _get_is_required(self):
        validator = self._retrieve_validator_from_validation_schema()
        if validator is None:
            return False
        else:
            try:
                validator.to_python('')
            except validators.Invalid:
                return True
            else:
                return False
    is_required = property(_get_is_required)

    def _get_field_id(self):
        return build_name_from_path(self.path, '_', '_')
    field_id = property(_get_field_id)

    def __init__(self, name=None, label=None, help_text=None, **kw):
        super(FormField, self).__init__(name, **kw)
        if label is not None:
            self.label = label
        if help_text is not None:
            self.help_text = help_text
        if self.field_class is None:
            self.field_class = self.__class__.__name__.lower()

    def update_params(self, d):
        super(FormField, self).update_params(d)
        if self.is_required:
            d["field_class"] = " ".join([d["field_class"], "requiredfield"])
        if d["css_classes"]:
            d["field_class"] = " ".join([d["field_class"]] + d["css_classes"])
        d["label"] = self.label
        d["help_text"] = self.help_text
        d["field_id"] = self.field_id

# A decorator that provides field_for functionality to the
# decorated FormFieldsContainer's method
def retrieve_field_for(func):
    def _retrieve_field_for(self=None, item=None, *args, **kw):
        path = path_from_item(item)
        field = self
        for name, index in path:
            if field is not None:
                field = field.get_field_by_name(name)
            append_to_path(field, index)
        if field is not None:
            returnval = func(self, field, *args, **kw)
        else:
            returnval = "Field for '%s' not found." % item
        for i in range(len(path)):
            pop_from_path()
        return returnval
    _retrieve_field_for = update_path(_retrieve_field_for)
    return _retrieve_field_for

class FormFieldsContainer(CompoundInputWidget):
    """A container for FormFields.

    Has two member_widgets lists:
       - fields
       - hidden_fields

    It provides the template with 3 useful functions:
       - field_for(name)
           Returns the child named ``name``
       - value_for(name)
           Returns the value for the child named ``name`` (name can also be
           a widget instance so fields can be iterated)
       - params_for(name)
           Returns the display-time parameters for the child named ``name`` (can
           also be a widget instance so fields can be iterated)
       - display_field_for(name)
           displays the child named ``name`` automatically propagating value
           an params. ``name`` can also be a widget instance.
       - error_for(name)
           Returns the validation error the child named ``name`` generated.
           Again, ``name`` can also be a widget instance.
    """
        
    member_widgets = ["fields", "hidden_fields"]
    fields = []
    hidden_fields = []
    params = ["disabled_fields"]
    disabled_fields = set()

    def _get_file_upload(self):
        for widget in self.iter_member_widgets():
            if getattr(widget, "file_upload", False):
                return True
        return False
    file_upload = property(_get_file_upload)

    def get_field_by_name(self, name, default=None):
        for widget in self.iter_member_widgets():
            if widget.name == name:
                return widget
        return default

    def display_field_for(self, item, value=None, **params):
        return item.display(value, **params)
    display_field_for = retrieve_field_for(display_field_for)

    def render_field_for(self, item, value=None, format="html", **params):
        return item.render(value, format, **params)
    render_field_for = retrieve_field_for(render_field_for)

    def _field_for(self, item):
        """This function should *only* be used inside a FormFieldsContainer
        template, really, else the path acrobatics will lead to unexpected
        results."""
        field = self.get_field_by_name(item, None)
        if field is None:
            raise ValueError("Field for '%s' not found." % item)
        return field

    def update_params(self, d):
        super(FormFieldsContainer, self).update_params(d)
        d["display_field_for"] = lambda f: self.display_field_for(f,
                                                                  d["value_for"](f),
                                                                  **d["params_for"](f))
        d["render_field_for"] = lambda f: self.display_field_for(f,
                                                                 d["value_for"](f),
                                                                 **d["params_for"](f))
        d["field_for"] = self._field_for
        visible_fields = []
        hidden_fields = []
        #XXX: Ugly hack, this badly needs a better fix. Note to meself:
        #     CompoundFormField has no fields or hidden_fields member_widgets, 
        #     related to [1736]'s refactoring.
        for field in d.get("fields", []) + d.get("hidden_fields", []):
            if field.name not in d["disabled_fields"]:
                if getattr(field, "hidden", False):
                    hidden_fields.append(field)
                else:
                    visible_fields.append(field)
        d["fields"] = visible_fields
        d["hidden_fields"] = hidden_fields

class CompoundFormField(FormFieldsContainer, FormField):
    is_required = False

class RepeatingFormField(RepeatingInputWidget, CompoundFormField):
    pass

#############################################################################
# Fields                                                                    #
#############################################################################
class Label(FormField):
    "A simple label for a form field."

    template = """
    <label xmlns:py="http://purl.org/kid/ns#"
        id="${field_id}"
        class="${field_class}"
        py:content="value"
    />
    """
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            'the label tag'}
    attrs = {}

class LabelDesc(CoreWD):
    for_widget = Label(default="Sample Label")

class TextField(FormField):
    "A standard, single-line text field."

    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="text"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        value="${value}"
        py:attrs="attrs"
    />
    """
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the input tag'}
    attrs = {}

class TextFieldDesc(CoreWD):
    name = "Text Field"
    for_widget = TextField("your_name", 
                           default="Your Name Here", 
                           attrs=dict(size="30"))

class PasswordField(FormField):
    "A password field which masks letters with * characters."

    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="password"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        value="${value}"
        py:attrs="attrs"
    />
    """
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            'the password input tag'}
    attrs = {}

class PasswordFieldDesc(CoreWD):
    name = "Password Field"
    for_widget = PasswordField("your_secret", 
                               default="Top Secret Password")

class HiddenField(FormField):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="hidden"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        value="${value}"
        py:attrs="attrs"
    />
    """
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the hidden input tag'}
    attrs = {}
    hidden = True

class HiddenFieldDesc(CoreWD, RenderOnlyWD):
    name = "Hidden Field"
    for_widget = HiddenField("hidden_one")

class FileField(FormField):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="file"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        py:attrs="attrs"
    />
    """
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the file input tag'}
    attrs = {}
    file_upload = True

class FileFieldDesc(CoreWD):
    name = "File Field"
    for_widget = FileField("your_filefield", attrs=dict(size="30"))

class Button(FormField):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="button"
        class="${field_class}"
        value="${value}"
        py:attrs="attrs"
    />
    """
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the button input tag'}
    attrs = {}

    def update_params(self, d):
        super(Button, self).update_params(d)
        if self.is_named:
            d['attrs']['name'] = d["name"]
            d['attrs']['id'] = d["field_id"]

class ButtonDesc(CoreWD):
    name = "Button"
    for_widget = Button(default="Button Value")

class SubmitButton(Button):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="submit"
        class="${field_class}"
        value="${value}"
        py:attrs="attrs"
    />
    """

class SubmitButtonDesc(CoreWD):
    name = "Submit Button"
    for_widget = SubmitButton(default="Submit Button Value")

class ResetButton(Button):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="reset"
        class="${field_class}"
        value="${value}"
        py:attrs="attrs"
    />
    """

class ResetButtonDesc(CoreWD):
    name = "Reset Button"
    for_widget = ResetButton(default="Reset Button Value")

class ImageButton(Button):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="image"
        src="${src}"
        width="${width}"
        height="${height}"
        class="${field_class}"
        value="${value}"
        py:attrs="attrs"
    />
    """
    params = ["src", "width", "height"]
    params_doc = {'src' : 'Source of the image',
                  'width' : 'Width of the image',
                  'height' : 'Height of the image'}
    src = None
    width = None
    height = None

class ImageButtonDesc(CoreWD):
    name = "Image Button"
    for_widget = ImageButton("your_image_button", src="/tg_static/images/toolbox_logo.png")

class CheckBox(FormField):
    template = """
    <input xmlns:py="http://purl.org/kid/ns#"
        type="checkbox"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        py:attrs="attrs"
    />
    """
    # an unchecked checkbox doesn't submit anything
    no_input_if_empty = True
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the checkbox input tag'}
    attrs = {}

    def __init__(self, *args, **kw):
        super(CheckBox, self).__init__(*args, **kw)
        if not self.validator:
            self.validator = validators.Bool()

    def update_params(self, d):
        super(CheckBox, self).update_params(d)
        try:
            value = self.validator.to_python(d['value'])
        except validators.Invalid:
            value = False
        if value:
            d['attrs']['checked'] = 'checked'

class CheckBoxDesc(CoreWD):
    for_widget = CheckBox(name="your_checkbox",
                          attrs=dict(checked=True),
                          help_text="Just click me...")
    template = """
    <div xmlns:py="http://purl.org/kid/ns#">
        ${for_widget.display()}
        <label for="${for_widget.field_id}" 
            py:content="for_widget.help_text" 
        />
    </div>
    """

class TextArea(FormField):
    template = """
    <textarea xmlns:py="http://purl.org/kid/ns#"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        rows="${rows}"
        cols="${cols}"
        py:attrs="attrs"
        py:content="value"
    />
    """
    params = ["rows", "cols", "attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the textarea tag',
                  'rows' : 'Number of rows to render',
                  'cols' : 'Number of columns to render'}
    rows = 7
    cols = 50
    attrs = {}

class TextAreaDesc(CoreWD):
    name = "Text Area"
    for_widget = TextArea(name="your_textarea",
                          default="Your Comment Here",
                          rows=5, cols=40)

class SelectionField(FormField):
    # an empty selection doesn't submit anything
    no_input_if_empty = True
    _multiple_selection = False
    _selected_verb = None
    params = ["options"]
    params_doc = {'options' : 'A list of tuples with the options for the select'
                              'field'}
    options = []
    convert = False

    def __init__(self, *args, **kw):
        super(SelectionField, self).__init__(*args, **kw)
        if not self.validator:
            validator = self._guess_validator()
            if validator is not None:
                self.validator = validator
            else:
                raise ValueError, ("No validator specified and couldn't "
                                   "guess one. I cannot work properly "
                                   "without it")
        # Only override the user-provided validator if it's not a ForEach one,
        # which usually means the user needs to perform validation on the list
        # as a whole.
        if self._multiple_selection and \
           not isinstance(self.validator, validators.ForEach):
            self.validator = validators.MultipleSelection(self.validator)            

    def _guess_validator(self):
        """
        Inspect sample option value to guess validator. crude
        avoid multiple evalution if options is callable
        """
        validator = None
        sample_option = self._get_sample_option()
        if sample_option is not None:
            if isinstance(sample_option, int):
                validator = validators.Int()
            elif isinstance(sample_option, basestring):
                validator = validators.String()
            else:
                import warnings
                warnings.warn("unknown option type in SelectionField: " + \
                       repr(sample_option[0]))
        return validator

    def _get_sample_option(self):
        options = self._extend_options(self.options)
        if options:
            if isinstance(options[0][1], list):
                sample = options[0][1][0]
            else:
                sample = options[0]
            return sample[0]
        else:
            return None

    def _extend_options(self, opts):
        if (len(opts) > 0) and not isinstance(opts[0], (tuple,list)):
            new_opts = []
            for opt in opts:
                new_opts.append((opt,opt))
            return new_opts
        return opts

    def update_params(self, d):
        super(SelectionField, self).update_params(d)
        grouped_options = []
        options = []
        d['options'] = self._extend_options(d['options'])
        for optgroup in d["options"]:
            if isinstance(optgroup[1], list):
                group = True
                optlist = optgroup[1][:]
            else:
                group = False
                optlist = [optgroup]
            for i, option in enumerate(optlist):
                if len(option) is 2:
                    option_attrs = {}
                elif len(option) is 3:
                    option_attrs = dict(option[2])
                if self._is_option_selected(option[0], d['value']):
                        option_attrs[self._selected_verb] = self._selected_verb
                optlist[i] = (option[0], option[1], option_attrs)
            options.extend(optlist)
            if group:
                grouped_options.append((optgroup[0], optlist))
        # options provides a list of *flat* options leaving out any eventual
        # group, useful for backward compatibility and simpler widgets
        d["options"] = options
        if grouped_options:
            d["grouped_options"] = grouped_options
        else:
            d["grouped_options"] = [(None, options)]

    def _is_option_selected(self, option_value, value):
        try:
            value = self.validator.to_python(value)
        except validators.Invalid:
            return False
        if value is not None:
            if self._multiple_selection:
                if option_value in value:
                    return True
            else:
                if option_value == value:
                    return True
        return False

class SingleSelectField(SelectionField):
    template = """
    <select xmlns:py="http://purl.org/kid/ns#"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        py:attrs="attrs"
    >
        <optgroup py:for="group, options in grouped_options"
            label="${group}"
            py:strip="not group"
        >
            <option py:for="value, desc, attrs in options"
                value="${value}"
                py:attrs="attrs"
                py:content="desc"
            />
        </optgroup>
    </select>
    """
    _selected_verb = 'selected'
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the select tag'}
    attrs = {}

class SingleSelectFieldDesc(CoreWD):
    name = "Single Select Field"
    for_widget = SingleSelectField("your_single_select_field", 
                                   options=[(1, "Python"), 
                                            (2, "Java"), 
                                            (3, "Pascal"),
                                            (4, "Ruby")],
                                   default=2)

class MultipleSelectField(SelectionField):
    template = """
    <select xmlns:py="http://purl.org/kid/ns#"
        multiple="multiple"
        size="${size}"
        name="${name}"
        class="${field_class}"
        id="${field_id}"
        py:attrs="attrs"
    >
        <optgroup py:for="group, options in grouped_options"
            label="${group}"
            py:strip="not group"
        >
            <option py:for="value, desc, attrs in options"
                value="${value}"
                py:attrs="attrs"
                py:content="desc"
            />
        </optgroup>
    </select>
    """
    _multiple_selection = True
    _selected_verb = 'selected'
    params = ["size", "attrs"]
    params_doc = {'size' : 'Number of options to show without scrolling'}
    attrs = {}
    size = 5

class MultipleSelectFieldDesc(CoreWD):
    name = "Multiple Select Field"
    for_widget = MultipleSelectField("your_multiple_select_field", 
                                     options=[("a", "Python"), 
                                              ("b", "Java"), 
                                              ("c", "Pascal"),
                                              ("d", "Ruby")],
                                     default=["a","c","d"])

class RadioButtonList(SelectionField):
    template = """
    <ul xmlns:py="http://purl.org/kid/ns#"
        class="${field_class}"
        id="${field_id}"
        py:attrs="list_attrs"
    >
        <li py:for="value, desc, attrs in options">
            <input type="radio"
                name="${name}"
                id="${field_id}_${value}"
                value="${value}"
                py:attrs="attrs"
            />
            <label for="${field_id}_${value}" py:content="desc" />
        </li>
    </ul>
    """
    _selected_verb = 'checked'
    params = ["list_attrs"]
    params_doc = {'list_attrs' : 'Extra (X)HTML attributes for the ul tag'}
    list_attrs = {}

class RadioButtonListDesc(CoreWD):
    name = "RadioButton List"
    for_widget = RadioButtonList("your_radiobutton_list", 
                                 options=[(1, "Python"), 
                                          (2, "Java"), 
                                          (3, "Pascal"),
                                          (4, "Ruby")],
                                 default=4)

class CheckBoxList(SelectionField):
    template = """
    <ul xmlns:py="http://purl.org/kid/ns#"
        class="${field_class}"
        id="${field_id}"
        py:attrs="list_attrs"
    >
        <li py:for="value, desc, attrs in options">
            <input type="checkbox"
                name="${name}"
                id="${field_id}_${value}"
                value="${value}"
                py:attrs="attrs"
            />
            <label for="${field_id}_${value}" py:content="desc" />
        </li>
    </ul>
    """
    _multiple_selection = True
    _selected_verb = 'checked'
    params = ["list_attrs"]
    params_doc = {'list_attrs' : 'Extra (X)HTML attributes for the ul tag'}
    list_attrs = {}

class CheckBoxListDesc(CoreWD):
    name = "CheckBox List"
    for_widget = CheckBoxList("your_checkbox_list", 
                              options=[(1, "Python"), 
                                       (2, "Java"), 
                                       (3, "Pascal"),
                                       (4, "Ruby")],
                              default=[1,4])

class FieldSet(CompoundFormField):
    template="""
    <fieldset xmlns:py="http://purl.org/kid/ns#"
        class="${field_class}"
        id="${field_id}"
    >
        <legend py:if="legend" py:content="legend" />
        <div py:for="field in hidden_fields" 
            py:replace="field.display(value_for(field), **params_for(field))" 
        />
        <div py:for="field in fields">
            <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
            <span py:content="field.display(value_for(field), **params_for(field))" />
            <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
            <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
        </div>
    </fieldset>
    """
    params = ["legend"]
    params_doc = {'legend' : 'Text to display as the legend for the fieldset'}
    legend = None

class FieldSetDesc(CoreWD):
    name = "FieldSet"
    for_widget = FieldSet("your_fieldset",
                          legend="Range", 
                          fields=[TextField(name="lower_limit", 
                                            label="Lower Limit"),
                                  TextField(name="upper_limit",
                                            label="Upper Limit")])

class RepeatingFieldSet(RepeatingFormField):
    template="""
    <div xmlns:py="http://purl.org/kid/ns#">
    <fieldset py:for="repetition in repetitions"
        class="${field_class}"
        id="${field_id}_${repetition}"
    >
        <legend py:if="legend" py:content="legend" />
        <div py:for="field in hidden_fields" 
            py:replace="field.display(value_for(field), **params_for(field))" 
        />
        <div py:for="field in fields">
            <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
            <span py:content="field.display(value_for(field), **params_for(field))" />
            <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
            <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
        </div>
    </fieldset>
    </div>
    """
    params = ["legend"]
    params_doc = {'legend' : 'Text to display as the legend for the fieldset'}
    legend = None

class RepeatingFieldSetDesc(CoreWD):
    name = "Repeating FieldSet"
    for_widget = RepeatingFieldSet("your_repeating_fieldset",
                                   legend='Range', 
                                   repetitions=3,
                                   fields=[TextField(name="lower_limit", 
                                                     label="Lower Limit"),
                                           TextField(name="upper_limit",
                                                     label="Upper Limit")])

#############################################################################
# Forms                                                                     #
#############################################################################
class Form(FormFieldsContainer):
    form = True
    name = "form"
    member_widgets = ["submit"]
    params = ["action", "method", "form_attrs", "submit_text"]
    params_doc = {'action' : 'Url to POST/GET the form data',
                  'method' : 'HTTP request method',
                  'form_attrs' : 'Extra (X)HTML attributes for the form tag',
                  'submit_text' : 'Text for the submit button',
                  'disabled_fields' : 'List of names of the fields we want to '
                                      'disable'}
    submit = SubmitButton()
    action = None
    method = "post"
    form_attrs = {}
    submit_text = None

    def update_params(self, d):
        super(Form, self).update_params(d)
        # A form is always at the beginning of the path so we just
        # use its name
        d["name"] = self.name
        if self.file_upload:
            d["form_attrs"]['enctype'] = "multipart/form-data"

    def validate(self, value, state=None):
        if self.validator:
            return self.validator.to_python(value, state)

    def _get_errors(self):
        return getattr(request, "validation_errors", None)
    errors = property(_get_errors)

class TableForm(Form):
    template = """
    <form xmlns:py="http://purl.org/kid/ns#"
        name="${name}"
        action="${action}"
        method="${method}"
        class="tableform"
        py:attrs="form_attrs"
    >
        <div py:for="field in hidden_fields" 
            py:replace="field.display(value_for(field), **params_for(field))" 
        />
        <table border="0" cellspacing="0" cellpadding="2" py:attrs="table_attrs">
            <tr py:for="i, field in enumerate(fields)" 
                class="${i%2 and 'odd' or 'even'}"
            >
                <th>
                    <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
                </th>
                <td>
                    <span py:replace="field.display(value_for(field), **params_for(field))" />
                    <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
                    <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
                </td>
            </tr>
            <tr>
                <td>&#160;</td>
                <td py:content="submit.display(submit_text)" />
            </tr>
        </table>
    </form>
    """
    params = ["table_attrs"]
    params_doc = {'table_attrs' : 'Extra (X)HTML attributes for the Table tag'}
    table_attrs = {}

class TableFormDesc(CoreWD):
    name = "Table Form"
    full_class_name = "turbogears.widgets.TableForm"
    field1 = TextField("name")
    field2 = TextField("address")
    field3 = TextField("occupation")
    field4 = PasswordField("password")
    field5 = PasswordField("reserved") # will never show
    field6 = HiddenField("hidden_info")
    for_widget = TableForm("TableForm",
                           fields=[field1, field2, field3, field4, field5, field6],
                           action="%s/save" % full_class_name,
                           submit_text="Submit Me")
    template = """
    <div>
        ${for_widget.display(disabled_fields=["reserved"])}
    </div>
    """

    def save(self, **kw):
        return """Received data from TableForm:<br />%r""" % kw
    save = expose()(save)

class ListForm(Form):
    template = """
    <form xmlns:py="http://purl.org/kid/ns#"
        name="${name}"
        action="${action}"
        method="${method}"
        class="listform"
        py:attrs="form_attrs"
    >
        <div py:for="field in hidden_fields" 
            py:replace="field.display(value_for(field), **params_for(field))" 
        />
        <ul py:attrs="list_attrs">
            <li py:for="i, field in enumerate(fields)" 
                class="${i%2 and 'odd' or 'even'}"
            >
                <label class="fieldlabel" for="${field.field_id}" py:content="field.label" />
                <span py:replace="field.display(value_for(field), **params_for(field))" />
                <span py:if="error_for(field)" class="fielderror" py:content="error_for(field)" />
                <span py:if="field.help_text" class="fieldhelp" py:content="field.help_text" />
            </li>
            <li py:content="submit.display(submit_text)" />
        </ul>
    </form>
    """
    params = ["list_attrs"]
    params_doc = {'list_attrs' : 'Extra (X)HTML attributes for the ul tag'}
    list_attrs = {}

class ListFormDesc(CoreWD):
    name = "List Form"
    full_class_name = "turbogears.widgets.ListForm"
    field1 = TextField("name")
    field2 = TextField("address")
    field3 = TextField("occupation")
    field4 = PasswordField("password")
    field5 = PasswordField("reserved") # will never show
    field6 = HiddenField("hidden_info")
    for_widget = ListForm("ListForm",
                          fields=[field1, field2, field3, field4, field5, field6],
                          action="%s/save" % full_class_name,
                          submit_text="Submit Me")
    template = """
    <div>
        ${for_widget.display(disabled_fields=["reserved"])}
    </div>
    """

    def save(self, **kw):
        return """Received data from ListForm:<br />%r""" % kw
    save = expose()(save)
