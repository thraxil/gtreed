import os
import itertools
import pkg_resources
import warnings
from turbogears import view, validators, startup, config
from turbogears.util import setlike, to_unicode, copy_if_mutable
from turbogears.widgets.meta import MetaWidget, load_kid_template

try: 
    set
except NameError: 
    from sets import Set as set

__all__ = ["load_widgets", "all_widgets", "Widget", "CompoundWidget",
           "WidgetsList", "register_static_directory",
           "static", "Resource", "Link", "CSSLink", "JSLink", 
           "Source", "CSSSource", "JSSource", "js_location", "mochikit",
           "WidgetDescription", "set_with_self"]


class Enum(set):
    """Enum used at js_locations which is less strict than 
    ``turbogears.utils.Enum`` and serves our purposes as well as allowing
    any object with ``retrieve_javascript``, ``retrieve_css``, and 
    ``location`` attributes to provide resources to the template when
    scanned in ``turbogears.controllers._process_output``.

    
    Example:

        >>> locations = Enum('bodytop', 'bodybottom', head')
        >>> locations.head == locations.head
        True
        >>> locations.head == locations.bodybottom
        False
        >>> locations.head in locations
        True
        >>> locations.foo
        Traceback (most recent call last):
        ...
        AttributeError

    """
    def __init__(self, *args):
        set.__init__(self, args)

    def __getattr__(self, name):
        if name in self:
            return name
        raise AttributeError

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ', '.join(map(repr, self)))

# Keeps a count of the each declared widget in a WidgetsList instance
# so their order is preserved.
counter = itertools.count()

# Load all widgets provided by the widget entry point
def load_widgets():
    for widget_mod in pkg_resources.iter_entry_points("turbogears.widgets"):
        widget_mod.load()

all_widgets = set()

PlainHTML = load_kid_template("""
                              <html xmlns:py="http://purl.org/kid/ns#"
                                  py:replace="elements" 
                              />
                              """,
                              modname="turbogears.widgets.plainhtml"
                             )[0]

#############################################################################
# Widgets base classes                                                      #
#############################################################################
class Widget(object):
    """
    A TurboGears Widget.
    
   '__init__' and 'update_params' are the only methods you might need to
   care extending.

    Attributes you should know about:
    
    name      : The name of the widget.
    template  : Kid template for the widget.
    default   : Default value for the widget.
    css       : List of CSSLinks and CSSSources for the widget. These
                will be automatically pulled and inserted in the
                page template that displays it.
    javascript: List of JSLinks and JSSources for the widget. Same as css.
    is_named  : A property returning True if the widget has overrided it's
                default name.
    params    : All parameter names listed here will be treated as special
                parameters. This list is updated by the metaclass and 
                always contains *all* params from the widget itself and
                all it's bases. Can be used as a quick reminder of all
                the params your widget has at it's disposal. They all
                behave the same and have the same priorities regarding their
                overridal. Read on...
    params_doc: A dictionary containing 'params' names as keys and their
                docstring as value. For documentation at the widget browser.

   All initialization parameters listed at the class attribute "params" can be 
   defined as class attributes, overriden at __init__ or at display time. They 
   will be treated as special params for the widget, which means:
   
   1) You can fix default values for them when sublcassing Widget.

   2) If passed as **params to the constructor, the will be bound automatically
      to the widget instance, taking preference over any class attributes 
      previously defined. Mutable attributes (dicts and lists) defined as class
      attributes are safe to modify as care is taken to copy them so the class 
      attribute remains unchanged. 

   3) They can be further overrided by passing them as keyword args to 
      display(). This will only affect that display() call in a thread-safe 
      way.

   4) A callable can be passed and it will be called automatically when sending
      variables to the template. This can be handy to pick up parameters which 
      change in every request or affect many widgets simultaneously.
    """

    __metaclass__ = MetaWidget

    name = "widget"
    template = None
    default = None
    css = []
    javascript = []
    params = []
    params_doc = {}

    def __init__(self, name=None, template=None, default=None, **params):
        """
        All initialization has to take place in this method. It's not 
        thread-safe to mutate widget's attributes outside this method or 
        anytime after widget's first display.

        *Must* call super(MyWidget, self).__init__(*args, **kw) cooperatively,
        unless, of course, your know what you're doing. Preferably this should
        be done before any actual work is done in the method.

        Parameters:

        name     : The widget's name. In input widgets, this will also be the
                   name of the variable that the form will send to the 
                   controller. This is the only param that is safe to pass as a 
                   positional argument to __init__.
        template : The template that the widget should use to display itself.
                   Currently only Kid templates are supported. You can both
                   initialize with a template string or with the path to a
                   file-base template: "myapp.templates.widget_tmpl"
        default  : Default value to display when no value is passed at display
                   time.
        **params : Keyword arguments specific to your widget or to any of it's
                   bases. If listed at class attribute 'params' the will be
                   bound automatically to the widget instance.

        Note: Do not confuse these parameters with parameters listed at 
        "params". Some widgets accept parameters at the constructor which are
        not listed params, these parameter won't be passed to the template, be
        automatically called, etc..
        """
        self._declaration_counter = counter.next()
        if name:
            self.name = name
        if template:
            (self.template_c, self.template) = load_kid_template(template)
        if default:
            self.default = default
        # logic for managing the params attribute
        for param in self.__class__.params:
            if param in params:
                # make sure we don't keep references to mutables
                setattr(self, param, copy_if_mutable(params.pop(param)))
            else:
                if hasattr(self, param):
                    # make sure we don't alter mutable class attributes
                    value = copy_if_mutable(getattr(self.__class__, param),
                                            True)
                    if value[1]:
                        # re-set it only if mutable
                        setattr(self, param, value[0])
                else:
                    setattr(self, param, None)
        for unused in params.iterkeys():
            warnings.warn('keyword argument "%s" is unused at %r instance' % (
                unused, self.__class__.__name__))

    def adjust_value(self, value, **params):
        """
        Adjusts the value sent to the template on display.
        """
        if value is None:
            return self.default
        else:
            return value

    def update_params(self, params):
        """
        This method will have the last chance to update the variables sent to 
        the template for the specific request. All parameters listed at class 
        attribute 'params' will be available at the 'params' dict this method 
        receives.

        *Must* call super(MyWidget, self).update_params(params) cooperatively,
        unless, of course, your know what you're doing. Preferably this should
        be done before any actual work is done in the method.
        """
        pass

    # The following methods are needed to be a well behaved widget, however,
    # there is rarely the need to override or extend them if inheritting
    # directly or indirectly from Widget.

    # update_data has been deprecated
    update_data = update_params

    def __call__(self, *args, **params):
        """
        Delegate to display. Used as an alias to avoid tiresome typing
        """
        return self.display(*args, **params)

    def display(self, value=None, **params):
        """
        Display the widget in a Kid template. Returns an elementtree node 
        instance. If you need serialized output in a string call 'render'
        instead.
        Probably you will not need to override or extend if inhertitting from
        Widget.

        @params:

        value    : The value to display in the widget.
        **params : Extra parameters specific to the widget. All keyword params
                   supplied will pass through the update_params method which will 
                   have a last chance to modify them before reaching the
                   template. 
        """

        if not getattr(self, 'template_c', False):
            warnings.warn("Widget instance '%r' has no template defined" % self)
            return None
        # logic for managing the params attribute
        for param in self.__class__.params:
            if param in params:
                param_value = params[param]
                if callable(param_value):
                    param_value = param_value()
            else:
                # if the param hasn't been overridden (passed as a keyword
                # argument inside **params) put the corresponding instance
                # value inside params.
                param_value = getattr(self, param, None)
            # make sure we don't pass a reference to mutables
            params[param] = copy_if_mutable(param_value)
        params["name"] = self.name
        params["value"] = to_unicode(self.adjust_value(value, **params))
        self.update_params(params)
        # update_data has been deprecated
        self.update_data(params)
        return view.engines.get('kid').transform(params, self.template_c)

    def render(self, value=None, format="html", **params):
        """
        Exactly the same as display() but return serialized output instead.
        Useful for debugging or to display the widget in a non-Kid template like
        Cheetah, STAN, ...
        """ 
        elem = self.display(value, **params)
        t = PlainHTML(elements=elem)
        return t.serialize(output=format, fragment=True)

    def retrieve_javascript(self):
        """
        Return a setlike instance with all the JSLinks and JSSources the
        widget needs.
        """ 
        scripts = setlike()
        for script in self.javascript:
            scripts.add(script)
        return scripts

    def retrieve_css(self):
        """
        Return a setlike instance with all the CSSLinks and CSSSources the
        widget needs.
        """ 
        css = setlike()
        for cssitem in self.css:
            css.add(cssitem)
        return css

    def _get_is_named(self):
        """
        Return True if the widget has overrided it's default name, else False.
        """
        if self.name != "widget":
            return True
        else:
            return False
    is_named = property(_get_is_named)

    def __setattr__(self, key, value):
        if self._locked:
            raise ValueError, \
                "It is not threadsafe to modify widgets in a request"
        else:
            return super(Widget, self).__setattr__(key, value)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, ', '.join(
            ["%s=%r" % (var, getattr(self, var))
                for var in ['name'] + self.__class__.params]))

class CompoundWidget(Widget):
    """A widget that can contain other widgets.

    A compund widget is a widget that can group several widgets to make a 
    complex widget. Child widget names must be listed at ther widget's
    ``member_widgets`` attribute.
    """
    compound = True
    member_widgets = []

    def __init__(self, *args, **kw):
        # logic for managing the member_widgets attribute
        for member in self.__class__.member_widgets:
            if member in kw:
                setattr(self, member, kw.pop(member))
            elif not hasattr(self, member):
                setattr(self, member, None)
        super(CompoundWidget, self).__init__(*args, **kw)

    def iter_member_widgets(self):
        """Iteratetes over all the widget's children"""
        for member in self.__class__.member_widgets:
            attr = getattr(self, member, None)
            if isinstance(attr, list):
                for widget in attr:
                    yield widget
            elif attr is not None:
                yield attr 

    def display(self, value=None, **params):
        params["member_widgets_params"] = params.copy()
        # logic for managing the member_widgets attribute
        for member in self.__class__.member_widgets:
            params[member] = getattr(self, member, None)
        return super(CompoundWidget, self).display(value, **params)

    def update_params(self, d):
        super(CompoundWidget, self).update_params(d)
        d['value_for'] = lambda f: self.value_for(f, d['value'])
        widgets_params = d['member_widgets_params']
        d['params_for'] = lambda f: self.params_for(f, **widgets_params)
 
    def value_for(self, item, value):
        """
        Pick up the value for a given member_widget 'item' from the 
        value dict passed to this widget.
        """
        name = getattr(item, "name", item)
        if isinstance(value, dict):
            return value.get(name)
        else:
            return None
 
    def params_for(self, item, **params):
        """
        Pick up the params for the given member_widget 'item' from
        the params dict passed to this widget.
        """
        name = getattr(item, "name", item)
        item_params = {}
        for k,v in params.iteritems():
            if isinstance(v, dict):
                if name in v:
                    item_params[k] = v[name]
        return item_params

    def retrieve_javascript(self):
        """
        Retrieve the javascript for all the member widgets and
        get an ordered union of them.
        """
        scripts = setlike()
        for script in self.javascript:
            scripts.add(script)
        for widget in self.iter_member_widgets():
            for script in widget.retrieve_javascript():
                scripts.add(script)
        return scripts

    def retrieve_css(self):
        """
        Retrieve the css for all the member widgets and
        get an ordered union of them.
        """
        css = setlike()
        for cssitem in self.css:
            css.add(cssitem)
        for widget in self.iter_member_widgets():
            for cssitem in widget.retrieve_css():
                css.add(cssitem)
        return css


#############################################################################
# Declarative widgets support                                               #
#############################################################################
class MetaWidgetsList(type):
    """
    Metaclass for WidgetLists. Takes care that the resulting WidgetList
    has all widgets in the same order as they were declared.
    """
    def __new__(meta, class_name, bases, class_dict):
        declared_widgets = []
        for name, value in class_dict.items():
            if isinstance(value, Widget):
                if not value.is_named:
                    value.name = name
                declared_widgets.append(value)
                del class_dict[name]
        declared_widgets.sort(lambda a, b: cmp(a._declaration_counter,
                                               b._declaration_counter))
        cls = type.__new__(meta, class_name, bases, class_dict)
        cls.declared_widgets = declared_widgets
        return cls

class WidgetsList(list):
    """
    A widget list. That's really all. A plain old list that you can
    declare as a classs with widgets ordered as attributes. Syntactic
    sugar for an unsweet world.
    """
    __metaclass__ = MetaWidgetsList

    def __init__(self):
        super(WidgetsList, self).__init__()
        self.extend(self.declared_widgets)
        if len(self) == 0:
            warnings.warn("You have declared an empty WidgetsList")

#############################################################################
# CSS, JS and mochikit stuff                                                #
#############################################################################
def register_static_directory(modulename, directory):
    """
    Sets up a static directory for JavaScript and css files. You can refer
    to this static directory in templates as ${tg.widgets}/modulename
    """
    directory = os.path.abspath(directory)
    config.update({'/tg_widgets/%s' % modulename :
                   {
                       'static_filter.on' : True,
                       'static_filter.dir' : directory
                   }
                  }
                 )

static = "turbogears.widgets"

register_static_directory(static,
                          pkg_resources.resource_filename(__name__,
                                                          "static")
                         )

register_static_directory("turbogears",
                          pkg_resources.resource_filename("turbogears",
                                                          "static")
                         )

def set_with_self(self):
    theset = setlike()
    theset.add(self)
    return theset

class Resource(Widget):
    """
    A resource for your widget, like a link to external JS/CSS or inline
    source to include at the template the widget is displayed.
    """
    pass

class Link(Resource):
    def __init__(self, mod, *args, **kw):
        super(Link, self).__init__(*args, **kw)
        self.mod = mod

    def update_params(self, d):
        super(Link, self).update_params(d)
        d["link"] = "/%stg_widgets/%s/%s" % (startup.webpath,
                                             self.mod,
                                             self.name)

    def __hash__(self):
        return hash(self.mod + self.name)

    def __eq__(self, other):
        return self.mod == getattr(other, "mod", None) and \
            self.name == getattr(other, "name", None)


class CSSLink(Link):
    template = """
    <link rel="stylesheet" 
        type="text/css" 
        href="$link" 
        media="$media"
    />
    """
    params = ["media"]
    params_doc = {'media': 'Specify the media attribute for the css link tag'}
    media = "all"

    retrieve_css = set_with_self

js_location = Enum('head', 'bodytop', 'bodybottom')

class JSLink(Link):
    template = """
    <script type="text/javascript" src="$link"></script>
    """

    location = js_location.head

    def __init__(self, *args, **kw):
        location = kw.pop('location', None)
        super(JSLink, self).__init__(*args, **kw)
        if location:
            if location not in js_location:
                raise ValueError, "JSLink location should be in %s" % js_location
            self.location = location
        
    retrieve_javascript = set_with_self

mochikit = JSLink("turbogears", "js/MochiKit.js")

class Source(Resource):
    params = ["src"]

    def __init__(self, src, *args, **kw):
        super(Source, self).__init__(*args, **kw)
        self.src = src

    def __hash__(self):
        return hash(self.src)

    def __eq__(self, other):
        return self.src == getattr(other, "src", None)

class CSSSource(Source):
    template = """
    <style type="text/css" media="$media">$src</style>
    """
    params = ["media"]
    params_doc = {'src': 'The CSS source for the link',
                  'media' : 'Specify the media the css source link is for'}
    media = "all"

    retrieve_css = set_with_self

class JSSource(Source):
    template = """
    <script type="text/javascript">$src</script>
    """
    location = js_location.head

    def __init__(self, src, location=None):
        if location:
            if location not in js_location:
                raise ValueError, "JSSource location should be in %s" % js_location
            self.location = location
        super(JSSource, self).__init__(src)

    retrieve_javascript = set_with_self

#############################################################################
# Classes for supporting the toolbox widget browser                         #
#############################################################################
just_the_widget = load_kid_template("""
                                    <div xmlns:py="http://purl.org/kid/ns#"
                                      py:content="for_widget.display()"
                                    />
                                    """
                                   )[0]

class MetaDescription(MetaWidget):
    """
    Metaclass for widget descriptions. Makes sure the widget browser knows
    about all of them as soon as they come into existence.
    """
    def __init__(cls, name, bases, dct):
        super(MetaDescription, cls).__init__(name, bases, dct)
        register = dct.get("register", True)
        if name != "WidgetDescription" and register:
            all_widgets.add(cls)

class WidgetDescription(CompoundWidget):
    """
    A description for a Widget. Make's the 'for_widget' widget appear in the 
    browser.
    It's a nice way to show off to your friends your coolest new widgets and
    to have a testing platform while developing them.
    """
    __metaclass__ = MetaDescription

    template = just_the_widget
    for_widget = None
    member_widgets = ["for_widget"]
    show_separately = False

    def _get_name(self):
        return self.for_widget_class.__name__
    name = property(_get_name)

    def _get_widget_class(self):
        return self.for_widget.__class__
    for_widget_class = property(_get_widget_class)

    def _get_description(self):
        return self.for_widget_class.__doc__
    description = property(_get_description)

    def _get_full_class_name(self):
        cls = self.for_widget_class
        return "%s.%s" % (cls.__module__, cls.__name__)
    full_class_name = property(_get_full_class_name)

    def _get_source(self):
        import inspect
        return inspect.getsource(self.__class__)
    source = property(_get_source)

    def retrieve_css(self):
        return self.for_widget.retrieve_css()

    def retrieve_javascript(self):
        return self.for_widget.retrieve_javascript()

class CoreWD(WidgetDescription):
    register = False

    def _get_full_class_name(self):
        cls = self.for_widget_class
        return "turbogears.widgets.%s" % (cls.__name__)
    full_class_name = property(_get_full_class_name)

class RenderOnlyWD(WidgetDescription):
    register = False
    template = """
    <div>
        This widget will render like that:<br/><br/>
        <tt class="rendered">${for_widget.render(value)}</tt>
    </div>
    """
    
    def retrieve_javascript(self):
        return setlike()
    
    def retrieve_css(self):
        return setlike()

#############################################################################
# CSS and JS WidgetDescription's                                            #
#############################################################################
class CSSLinkDesc(CoreWD, RenderOnlyWD):
    name = "CSS Link"
    for_widget = CSSLink("turbogears", "css/yourstyle.css")

class JSLinkDesc(CoreWD, RenderOnlyWD):
    name = "JS Link"
    for_widget = JSLink("turbogears", "js/yourscript.js")

class CSSSourceDesc(CoreWD, RenderOnlyWD):
    name = "CSS Source"
    for_widget = CSSSource("""body { font-size:12px; }""")

class JSSourceDesc(CoreWD, RenderOnlyWD):
    name = "JS Source"
    for_widget = JSSource("document.title = 'Hello World';")
