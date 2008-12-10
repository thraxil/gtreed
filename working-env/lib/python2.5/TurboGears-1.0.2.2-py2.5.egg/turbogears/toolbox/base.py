"""Graphical user interface for managing TurboGears projects"""

from turbogears import controllers
from turbogears.util import setlike
from turbogears import identity
import pkg_resources
import turbogears
import cherrypy
import shell
import admi18n
import designer

class Info(controllers.Controller):
    """TurboGears System Information.
       Lists your TurboGears packages and version information
    """
    __label__ ="System Info"
    __version__ = "0.1"
    __author__ = "Ronald Jaramillo"
    __email__ = "ronald@checkandshare.com"
    __copyright__ = "Copyright 2005 Ronald Jaramillo"
    __license__ = "MIT"

    icon = "/tg_static/images/info.png"

    def index(self):
        from turbogears.command.info import retrieve_info
        packages, plugins = retrieve_info()
        return dict(packages=packages, plugins=plugins)
    index = turbogears.expose(template='turbogears.toolbox.info')(index)

class WidgetBrowser(controllers.Controller):
    """Browse usage samples, description and source code for the available TurboGears Widgets"""
    __label__ ="Widget Browser"
    __version__ = "0.1"
    __author__ = "Kevin Dangoor"
    __email__ = "dangoor+turbogears@gmail.com"
    __copyright__ = "Copyright 2005 Kevin Dangoor"
    __license__ = "MIT"
    
    all_descs = None
    icon = "/tg_static/images/widgets.png"
    
    [turbogears.expose(template="turbogears.toolbox.widgets")]
    def index(self, name=None):
        from turbogears import widgets
        from turbogears.widgets import js_location, Tabber, SyntaxHighlighter
        all_descs = self.all_descs
        if not all_descs:
            widgets.load_widgets()
            all_descs = dict()
            for widgetdesc in widgets.all_widgets:
                wd = widgetdesc()
                all_descs[wd.full_class_name.replace(".", "_")] = wd
            self.all_descs = all_descs
        if name:
            all_descs = {name : all_descs[name]}
        desclist = list(all_descs.values())
        desclist.sort(cmp=lambda x,y: cmp(x.name, y.name))
        output = dict(descs=desclist, viewing_one=name != None)
        if name:
            # do not extend desclist!
            desclist = desclist + [Tabber(), SyntaxHighlighter()]
        
        css = setlike()
        js = dict()
        for l in js_location:
            js[l] = setlike()
        
        for widgetdesc in desclist:
            if not name and widgetdesc.show_separately:
                continue
            css.add_all(widgetdesc.retrieve_css())
            
            for l in js_location:
                for script in widgetdesc.retrieve_javascript():
                    if hasattr(script, "location"):
                        js[script.location].add(script)
                    else:
                        js[js_location.head].add(script)
        output["widget_css"] = css
        for l in js_location:
            output["widget_js_%s" % str(l)] = js[l]
        
        return output
    
    def __getattr__(self, widgetname):
        try:
            return self.all_descs[widgetname]
        except:
            raise AttributeError(widgetname)

class Toolbox(controllers.RootController):
    def __init__(self):
        self.toolbox = self.get_tools()

    def tool_icon(self,tool):
        icon = getattr(tool,'icon','')
        if icon: return icon

    def get_tools(self):
        tools = []
        for i in pkg_resources.iter_entry_points("turbogears.toolboxcommand"):

            tool = i.load()
            tools.append((tool,i.name))
            setattr(self, i.name, tool())
        toolbox = []
        for tool, name in tools:
            args = {
                    'path':name,
                    'label':getattr(tool,'__label__',tool),
                    'description':getattr(tool,'__doc__',''),
                    'version':getattr(tool,'__version__',''),
                    'author':getattr(tool,'__author__',''),
                    'email':getattr(tool,'__email__',''),
                    'copyright':getattr(tool,'__copyright__',''),
                    'license':getattr(tool,'__license__',''),
                    'icon':self.tool_icon(tool),
                    'disabled': False
                   }
            if not turbogears.util.get_project_name() and getattr(tool, 'need_project', False):
                args["disabled"] = 'disabled'
            toolbox.append(args)
        return toolbox
    
    def arrange_in_pairs(self,tools):
        p = [[],[]]
        for idx,tool in enumerate(tools): p[idx%2].append(tool)
        pairs = zip(p[0],p[1]) 
        if len(p[0]) > len(p[1]): pairs.append([p[0][-1],None])
        if len(p[0]) < len(p[1]): pairs.append([p[1][-1],None])
        return pairs

    def index(self):
        return dict(toolbox = self.arrange_in_pairs(self.toolbox),
                project = turbogears.util.get_project_name())
    index = turbogears.expose(template="turbogears.toolbox.main")(index)

    def noaccess(self):
        return """<h3>No access for %s</h3>
                    <p>
                       By default only localhost (127.0.0.1) 
                       has access to the Toolbox
                    </p>
                    <p>
                       You can provide access to your client by passing 
                       your host address to Toolbox as a parameter. Ex:
                    </p>
                    <pre>
                        tg-admin toolbox -c %s
                    </pre>
             """% (cherrypy.request.remoteAddr,cherrypy.request.remoteAddr)
    noaccess = turbogears.expose()(noaccess)
