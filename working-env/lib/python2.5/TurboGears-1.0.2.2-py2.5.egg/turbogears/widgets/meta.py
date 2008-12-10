import threading
import copy
import warnings
import kid
from new import instancemethod
from itertools import ifilter, count
from turbogears import validators
from formencode.schema import Schema

try:
    set
except NameError:
    from sets import Set as set

__all__ = ["MetaWidget", "load_kid_template"]

param_prefix = '_param_'

class MetaWidget(type):
    def __new__(cls, name, bases, dct):
        # update_data has been deprecated
        if 'update_data' in dct and name != "Widget":
            warnings.warn(
                "update_data has been renamed update_params, please "
                "rename your method. "
                "Note: this warning will be removed once 1.0 is "
                "released and your actual code will stop working.",
                DeprecationWarning, 2)
        # Makes sure we get the union of params and member_widgets
        # from all our bases.
        params_set = set(dct.get('params', []))
        # template_vars has been deprecated
        if 'template_vars' in dct:
            params_set.update(dct['template_vars'])
            warnings.warn(
                "Use of template_vars inside a widget is deprecated, "
                "use params instead. "
                "Note: this warning will be removed once 1.0 is "
                "released and your actual code will stop working.",
                DeprecationWarning, 2)
        member_widgets_set = set(dct.get('member_widgets', []))
        compound = False
        for base in bases:
            params_set.update(getattr(base, 'params', []))
            if getattr(base, 'compound', False):
                member_widgets_set.update(getattr(base, 'member_widgets', []))
                compound = True
        for param in params_set:
            # Swap all params listed at 'params' with a ParamDescriptor
            try:
                dct[param_prefix+param] = dct[param]
                dct[param] = ParamDescriptor(param)
            except KeyError:
                # declared in a superclass, skip it...
                pass
        dct['params'] = list(params_set)
        #XXX: Remove when deprecation is effective
        dct['template_vars'] = dct['params']
        if compound:
            dct['member_widgets'] = list(member_widgets_set)
        # Pick params_doc from all bases giving priority to the widget's own
        params_doc = {}
        for base in bases:
            params_doc.update(getattr(base, 'params_doc', {}))
        params_doc.update(dct.get('params_doc', {}))
        dct['params_doc'] = params_doc
        return super(MetaWidget, cls).__new__(cls, name, bases, dct)

    def __init__(cls, name, bases, dct):
        if "__init__" in dct:
            dct["__init__"] = _decorate_widget_init(dct["__init__"])
            cls.__init__ = dct["__init__"]
        super(MetaWidget, cls).__init__(name, bases, dct)
        modname = "%s.%s" % (cls.__module__, name) 
        if cls.template:
            (cls.template_c,
             cls.template) = load_kid_template(cls.template, modname)
        cls._locked = False

#############################################################################
# Method decorators and other MetaWidget helpers                            #
#############################################################################

class ParamDescriptor(object):
    """Descriptor to support automatic callable support for widget params."""
    def __init__(self, param_name):
        self.param_name = param_prefix + param_name

    def __get__(self, obj, typ=None):
        if obj is None:
            # return the original class attribute. This makes the descriptor
            # almost invisible
            return getattr(typ, self.param_name)
        param = getattr(obj, self.param_name)
        if callable(param):
            return param()
        return param

    def __set__(self, obj, value):
        setattr(obj, self.param_name, value)

def lockwidget(self, *args, **kw):
    "Sets this widget as locked the first time it's displayed."
    gotlock = self._displaylock.acquire(False)
    if gotlock:
        del self.display
        self._locked = True
    output = self.__class__.display(self, *args, **kw)
    if gotlock:
        self._displaylock.release()
    return output

def _decorate_widget_init(func):
    """
    Ensures that the display method for the instance is overridden by
    lockwidget, that an eventual validator dict is applied to the
    widget validator and that a validation schema is generated for compound
    widgets.
    """
    def widget_init(self, *args, **kw):
        self.display = instancemethod(lockwidget, self, self.__class__)
        # We may want to move the InputWidget related logic to another
        # decorator
        input_widget = hasattr(self, "validator")
        # Makes sure we only generate a schema once in the all __init__ 
        # cooperative calls from subclasses. Same for the displaylock
        if not hasattr(self, '__initstack'):
            self._displaylock = threading.Lock()
            self.__initstack = []
        else:
            self.__initstack.append(True)
        # Manage an eventual validator dictionary that provides additional
        # parameters to the default validator (if present).
        # We remove it from kw and apply it after the execution of the
        # decorated __init__ method since only at this point we can check
        # for the presence of a default validator
        if input_widget and ("validator" in kw) \
           and isinstance(kw["validator"], dict):
            validator_dict = kw.pop("validator")
        else:
            validator_dict = None
        # Execute the decorated __init__ method
        func(self, *args, **kw)
        try:
            self.__initstack.pop()
        except IndexError:
            # We're the first __init__ called
            del self.__initstack
            if input_widget:
                # Apply an eventual validator dictionary
                if validator_dict:
                    if self.validator is not None:
                        class_validator = self.__class__.validator
                        if self.validator is class_validator:
                            # avoid modifying a validator that has been
                            # defined at class level and therefor is 
                            # shared by all instances of this widget
                            self.validator = copy.deepcopy(class_validator)
                        self.validator.__dict__.update(validator_dict)
                    else:
                        raise ValueError, ("You can't use a dictionary to "
                                           "provide additional parameters "
                                           "as the widget doesn't provide a "
                                           "default validator" )
                # Generate the validation Schema if we are a compound widget
                if getattr(self, 'compound', False):
                    widgets = self.iter_member_widgets()
                    # generate the schema associated to our widgets
                    validator = generate_schema(self.validator, widgets)
                    if getattr(self, 'repeating', False):
                        self.validator = validators.ForEach(validator)
                    else:
                        self.validator = validator
    return widget_init

#############################################################################
# Widget template support.                                                  #
#############################################################################

# Keeps a count of the widget instances which have overrided their template on
# the constructor so we can generate unique template-module names
widget_instance_serial = count()

# XXX: Maybe Widget should have a __del__ method to unload any template that
#      has been loaded during the instances initialization?
def load_kid_template(t, modname=None):
    """
    Loads the given template into the given module name, if modname is None,
    an unique one will be generated.
    Returns a tuple (compiled_tmpl, template_text (or modulepath)
    """
    if isinstance(t, basestring) and "<" in t:
        if not modname:
            modname = 'instance_template_%d' % widget_instance_serial.next()
        return (kid.load_template(t, name=modname).Template, t)
    else:
        return (t, None)

#############################################################################
# Schema generation support                                                 #
#############################################################################
class NullValidator(validators.FancyValidator):
    """ 
    A do-nothing validator. Used as a placeholder for fields with 
    no validator so they don't get stripped by the Schema.
    """
    if_missing = None

def copy_schema(schema):
    """ recursively copies a schema """
    new_schema = copy.copy(schema)
    new_schema.pre_validators = schema.pre_validators[:]
    new_schema.chained_validators = schema.chained_validators[:]
    fields = {}
    for k, v in schema.fields.iteritems():
        if isinstance(v, Schema):
            v = copy_schema(v)
        fields[k] = v
    new_schema.fields = fields
    return new_schema

def merge_schemas(to_schema, from_schema, inplace=False):
    """ 
    Recursively merges from_schema into to_schema taking care of leaving
    to_schema intact if inplace is False (default).
    """
    if not inplace: 
        to_schema = copy_schema(to_schema)

    # Recursively merge child schemas
    is_schema = lambda f: isinstance(f[1], validators.Schema)
    seen = set()
    for k, v in ifilter(is_schema, to_schema.fields.iteritems()):
        seen.add(k)
        from_field = from_schema.fields.get(k)
        if from_field:
            v = merge_schemas(v, from_field)
            to_schema.add_field(k, v)

    # Add remaining fields if we can
    can_add = lambda f: f[0] not in seen and can_add_field(to_schema, f[0])
    for field in ifilter(can_add, from_schema.fields.iteritems()):
        to_schema.add_field(*field)

    return to_schema

def add_field_to_schema(schema, widget):
    """ Adds a widget's validator if any to the given schema """
    name = widget.name
    if widget.validator is not None:
        if isinstance(widget.validator, validators.Schema): 
            # Schema instance, might need to merge 'em...
            if widget.name in schema.fields:
                assert isinstance(
                    schema.fields[name], validators.Schema
                ), "Validator for '%s' should be a Schema subclass" % name
                v = merge_schemas(schema.fields[name], widget.validator)
            else:
                v = widget.validator
            schema.add_field(name, v)
        elif can_add_field(schema, name):
            # Non-schema validator, add it if we can...
            schema.add_field(name, widget.validator)
    elif can_add_field(schema, name):
        schema.add_field(name, NullValidator())
            
def generate_schema(schema, widgets):
    """
    Generates or extends a copy of schema with all the validators from 
    the widget in the widgets list.
    """
    if schema is None:
        schema = validators.Schema()
    else:
        schema = copy_schema(schema)
    for widget in widgets:
        if widget.is_named:
            add_field_to_schema(schema, widget)
    return schema

def can_add_field(schema, field_name):
    """
    Checks if we can safely add a field. Makes sure we're not overriding
    any field in the Schema. NullValidators are ok to override. 
    """
    current_field = schema.fields.get(field_name)
    return bool(current_field is None or 
                isinstance(current_field, NullValidator))

