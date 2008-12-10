import turbogears
from turbogears import controllers
import sys
import StringIO
from code import InteractiveConsole
from textwrap import TextWrapper

class WebConsole(controllers.RootController):
    """Web based Python interpreter"""
    __label__='WebConsole'
    
    icon = "/tg_static/images/shell.png"

    def __init__(self, width=80):
        self.console = None

        try:
            sys.ps1
        except AttributeError:
            sys.ps1 = '>>> '
        try:
            sys.ps2
        except AttributeError:
            sys.ps2 = '... '
        
    def process_request(self, line):
        more, output = self._process_request(line)
        return dict(more=more, output=output)
    process_request = turbogears.expose()(process_request)

    def process_multiline_request(self, block):
        outlines = []
        response = ''
        
        lines = [line for line in block.split('\n')]
        
        for line in lines:	
            more, output = self._process_request(line)
            
            if output[-1] == '\n':     # we'll handle the newlines later.
                output = output[:-1]
            
            outlines.append(output)
        
        return dict(more=more,output='\n'.join(outlines))
    process_multiline_request = turbogears.expose()(process_multiline_request)

    def _process_request(self, line):
        if len(self.console.buffer):
            prompt = sys.ps2
        else:
            prompt = sys.ps1
            
        myout = StringIO.StringIO()
        
        output = "%s%s" % ( prompt, line )
        # hopefully python doesn't interrupt in this block lest we'll get some curious output.
        try:
            sys.stdout = myout
            sys.stderr = myout
            more = self.console.push(line)
        finally:
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        
        stdout = myout.getvalue()
        
        if stdout: output = '%s\n%s' % ( output, stdout )
        
        return ( more, output.rstrip() )

    def new_console(self):
        locs = dict(__name__='tg-admin',__doc__=None,reload_console=self.new_console)
        mod = turbogears.util.get_model()
        if mod:
            locs.update(mod.__dict__)
        self.console = InteractiveConsole(locals=locs)

    def index(self):
        if not self.console:
            self.new_console()
        return dict()
    index = turbogears.expose(html="turbogears.toolbox.console")(index)
