import warnings
from turbojson.jsonify import encode
from turbogears.widgets.base import CSSLink, JSLink, CSSSource, JSSource, \
                                    Widget, CoreWD, static, js_location
from turbogears.widgets.forms import SelectionField

try: 
    set
except NameError: 
    from sets import Set as set

__all__ = ["Tabber", "SyntaxHighlighter", "JumpMenu"]

class Tabber(Widget):
    """This widget includes the tabber js and css into your rendered
    page so you can create tabbed divs by assigning them the 'tabber' 
    and 'tabbertab' classes.
    """
    css = [CSSLink(static,"tabber/tabber.css", media="screen")]
    def __init__(self, tabber_options={}, use_cookie=False, hide_on_load=True,
                 *args, **kw):
        super(Tabber, self).__init__(*args, **kw)
        js = []
        # First some sanity-check   
        if use_cookie and (tabber_options.has_key('onLoad') or
                           tabber_options.has_key('onClick')):
            warnings.warn("Cannot use cookies if overriden by "
                          "tabber_options['onClick'] or "
                          "tabber_options['onLoad']. Undefined behavior.")
        # Build the js list in it's correct order
        if use_cookie:
            js.append(JSLink(static, "tabber/tabber_cookie.js"))
        if tabber_options:
            js.append(JSSource("var tabberOptions = %s;" % 
                               encode(tabber_options)))
        if use_cookie:
            js.append(JSSource("""
                               try {
                                   tabberOptions
                               } catch(e){ 
                                   tabberOptions = {};
                               }
                               tabberOptions['onLoad'] = tabber_onload;
                               tabberOptions['onClick'] = tabber_onclick;
                               tabberOptions['cookie'] = 'TGTabber';"""))
        if hide_on_load:
            js.append(JSSource(
"document.write('<style type=\"text/css\">.tabber{display:none;}<\/style>');"))
        js.append(JSLink(static, "tabber/tabber-minimized.js",
                         location=js_location.bodytop))
        self.javascript = js
        

class TabberDesc(CoreWD):
    name = "Tabber"
    for_widget = Tabber()
    template = """<div class="tabber">
        <div class="tabbertab"><h2>Tab 1</h2></div>
        <div class="tabbertab"><h2>Tab 2</h2></div>
        <div class="tabbertab"><h2>Tab 3</h2></div>
        </div>"""

class SyntaxHighlighter(Widget):
    """This widget includes the syntax highlighter js and css into your 
    rendered page to syntax-hightlight textareas named 'code'. The supported
    languages can be listed at the 'languages' __init__ parameter.
    """
    available_langs = set([
        'CSharp',
        'Css',
        'Delphi',
        'Java',
        'JScript',
        'Php',
        'Python',
        'Ruby',
        'Sql',
        'Vb',
        'Xml',
        ])
    css = [CSSLink(static,"sh/SyntaxHighlighter.css")]

    def __init__(self, languages=['Python', 'Xml']):
        javascript = [
            JSLink(static, 'sh/shCore.js', location=js_location.bodybottom)
            ]
        for lang in languages:
            if lang not in self.available_langs:
                raise ValueError, ("Unsupported language %s. Available "
                                   "languages: '%s'" % 
                                   (lang, ', '.join(self.available_langs)))
            source = "sh/shBrush%s.js" % lang
            javascript.append(
                JSLink(static, source, location=js_location.bodybottom)
                )
        javascript.append(
            JSSource(
                "dp.SyntaxHighlighter.HighlightAll('code');",
                location=js_location.bodybottom
                )
            )
        self.javascript = javascript 

class SyntaxHighlighterDesc(CoreWD):
    name = "Syntax Highlighter"
    for_widget = SyntaxHighlighter()
    template = """\
    <textarea name="code" class="py">
        def say_hello():
            print "Hello world!"
    </textarea>"""

class JumpMenu(SelectionField):
    """
    Choose a link from the menu, 
    the page will be redirect to the selected link.
    """
    js = JSSource("""
    <!--
    function TG_jumpMenu(targ,f,restore){ 
      eval(targ+".location='"+f.options[f.selectedIndex].value+"'");
      if (restore) f.selectedIndex=0;
    }
    //-->
    """)
    
    template = """
    <select xmlns:py="http://purl.org/kid/ns#"
        name="${name}"
        class="${field_class}"
        id="${field_id}" 
        onchange="TG_jumpMenu('parent',this,0)"
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
    javascript = [js]
    _selected_verb = 'selected'
    params = ["attrs"]
    params_doc = {'attrs' : 'Dictionary containing extra (X)HTML attributes for'
                            ' the select tag'}
    attrs = {}

class JumpMenuDesc(CoreWD):
    name = "Jump Menu"
    for_widget = JumpMenu("your_jump_menu_field",
                          options=[('http://www.python.org', "Python"),
                                   ('http://www.turbogears.org', "TurboGears"),
                                   ('http://www.python.org/pypi', "Cheese Shop"),
                                   ('http://www.pythonware.com/daily/', "Daily Python")],
                          #default='http://www.turbogears.org'
                          )
