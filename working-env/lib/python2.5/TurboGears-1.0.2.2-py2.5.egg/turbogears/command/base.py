"Commands for the TurboGears command line tool."
import optparse
import sys
import os
import os.path
import glob

import pkg_resources
import dispatch

import configobj

import turbogears
from turbogears.util import get_model, load_project_config, get_project_config, get_package_name
from turbogears.identity import SecureObject,from_any_host
from turbogears import config, database


sys.path.insert(0, os.getcwd())

no_connection_param = ["help", "list"]
no_model_param = ["help"]

def silent_os_remove(fname):
    """
    Tries to remove file FNAME but mutes any error that may happen.

    Returns True if file was actually removed and false otherwise
    """
    try:
        os.remove(fname)
        return True
    except os.error:
        pass
    return False

class CommandWithDB(object):
    "Base class for commands that need to use the database"
    config = None

    def __init__(self, version):
        pass

    def find_config(self):
        """Chooses the config file, trying to guess whether this is a
        development or installed project."""
        load_project_config(self.config)
        self.dburi = turbogears.config.get("sqlobject.dburi", None)
        if self.dburi and self.dburi.startswith("notrans_"):
            self.dburi = self.dburi[8:]


[dispatch.generic()]
def sacommand(command, args):
    pass

[sacommand.when("command == 'help'")]
def sahelp(command, args):
    print """TurboGears SQLAlchemy Helper

help    this display
create  create the database tables
"""
[sacommand.when("command == 'create'")]
def sacreate(command, args):
    print "Creating tables at %s" % (config.get("sqlalchemy.dburi"))
    from turbogears.database import bind_meta_data, metadata
    bind_meta_data()
    get_model()
    metadata.create_all()
    
class SQL(CommandWithDB):
    """
    Wrapper command for sqlobject-admin, and provide some sqlalchemy support.

    This automatically supplies sqlobject-admin with the database that
    is found in the config file. Will also supply the model module as
    appropriate."""

    desc = "Run the database provider manager"
    need_project = True

    def __init__(self, version):
        if len(sys.argv) == 1 or sys.argv[1][0] == "-":
            parser = optparse.OptionParser(
                usage="%prog sql [command]\n\n" \
                      "hint: '%prog sql help' will list the sqlobject " \
                      "commands",
                version="%prog " + version)
            parser.add_option("-c", "--config", help="config file",
                              dest="config")
            (options, args) = parser.parse_args(sys.argv[1:3])

            if not options.config:
                parser.error("Please provide a valid option or command.")
            self.config = options.config
            # get rid of our config option
            if not args:
                del sys.argv[1:3]
            else:
                del sys.argv[1]

        self.find_config()

    def run(self):
        "Executes the sqlobject-admin code."
        if not "--egg" in sys.argv and not turbogears.util.get_project_name():
            print "this don't look like a turbogears project"
            return
        else:
            command = sys.argv[1]
            
            if config.get("sqlalchemy.dburi"):
                try:
                    sacommand(command, sys.argv)
                except dispatch.interfaces.NoApplicableMethods:
                    sacommand("help", [])
                return
            
            sqlobjcommand = command      
            if sqlobjcommand not in no_connection_param:
                if not self.dburi:
                    print """Database URI not specified in the config file (%s).
        Please be sure it's on the command line.""" % self.config
                else:
                    print "Using database URI %s" % self.dburi
                    sys.argv.insert(2, self.dburi)
                    sys.argv.insert(2, "-c")

            if sqlobjcommand not in no_model_param:
                if not "--egg" in sys.argv:
                    eggname = glob.glob("*.egg-info")
                    if not eggname or not \
                        os.path.exists(os.path.join(eggname[0], "sqlobject.txt")):
                        eggname = self.fix_egginfo(eggname)
                    eggname = eggname[0].replace(".egg-info", "")
                    if not "." in sys.path:
                        sys.path.append(".")
                        pkg_resources.working_set.add_entry(".")
                    sys.argv.insert(2, eggname)
                    sys.argv.insert(2, "--egg")

            from sqlobject.manager import command
            command.the_runner.run(sys.argv)

    def fix_egginfo(self, eggname):
        print """
This project seems incomplete. In order to use the sqlobject commands
without manually specifying a model, there needs to be an
egg-info directory with an appropriate sqlobject.txt file.

I can fix this automatically. Would you like me to?
"""
        dofix = raw_input("Enter [y] or n: ")
        if not dofix or dofix.lower()[0] == 'y':
            oldargs = sys.argv
            sys.argv = ["setup.py", "egg_info"]
            import imp
            imp.load_module("setup", *imp.find_module("setup", ["."]))
            sys.argv = oldargs

            import setuptools
            package = setuptools.find_packages()[0]
            eggname = glob.glob("*.egg-info")
            sqlobjectmeta = open(os.path.join(eggname[0], "sqlobject.txt"), "w")
            sqlobjectmeta.write("""db_module=%(package)s.model
history_dir=$base/%(package)s/sqlobject-history
""" % dict(package=package))
        else:
            sys.exit(0)
        return eggname


class Shell(CommandWithDB):
    """Convenient version of the Python interactive shell.
    This shell attempts to locate your configuration file and model module
    so that it can import everything from your model and make it available
    in the Python shell namespace."""

    desc = "Start a Python prompt with your database available"
    need_project = True

    def run(self):
        "Run the shell"
        self.find_config()
        
        mod = get_model()
        if mod:
            locals = mod.__dict__
        else:
            locals = dict(__name__="tg-admin")
            
        if config.get("sqlalchemy.dburi"):
            using_sqlalchemy = True
            database.bind_meta_data()
            locals.update(session=database.session,
                          metadata=database.metadata)
        else:
            using_sqlalchemy = False

        try:
            # try to use IPython if possible
            import IPython

            class CustomIPShell(IPython.iplib.InteractiveShell):
                def raw_input(self, *args, **kw):
                    try:
                        return \
                         IPython.iplib.InteractiveShell.raw_input(self,
                                                    *args, **kw)
                    except EOFError:
                        b = raw_input("Do you wish to commit your "
                                    "database changes? [yes]")
                        if not b.startswith("n"):
                            if using_sqlalchemy:
                                self.push("session.flush()")
                            else:
                                self.push("hub.commit()")
                        raise EOFError

            shell = IPython.Shell.IPShell(user_ns=locals,
                                          shell_class=CustomIPShell)
            shell.mainloop()
        except ImportError:
            import code

            class CustomShell(code.InteractiveConsole):
                def raw_input(self, *args, **kw): 
                    try:
                        import readline
                    except ImportError:
                        pass

                    try:
                        return code.InteractiveConsole.raw_input(self,
                                                        *args, **kw)
                    except EOFError:
                        b = raw_input("Do you wish to commit your "
                                      "database changes? [yes]")
                        if not b.startswith("n"):
                            if using_sqlalchemy:
                                self.push("session.flush()")
                            else:
                                self.push("hub.commit()")
                        raise EOFError

            shell = CustomShell(locals=locals)
            shell.interact()

class ToolboxCommand(CommandWithDB):

    desc = "Launch the TurboGears Toolbox"

    def __init__(self, version):
        self.hostlist = ['127.0.0.1','::1']

        parser = optparse.OptionParser(
            usage="%prog toolbox [options]", version="%prog " + version)
        parser.add_option("-n", "--no-open",
                 help="don't open browser automatically",
                 dest="noopen", action="store_true",
                 default=False)
        parser.add_option("-c", "--add-client",
                help="allow the client ip address specified to connect to toolbox (Can be specified more than once)",
                dest="host", action="append", default=None)
        parser.add_option("-p", "--port",
                help="port to run the Toolbox on", dest="port", default=7654)
        parser.add_option("--conf", help="config file to use", dest="config", default=get_project_config())
        (options, args) = parser.parse_args(sys.argv[1:])
        self.port = int(options.port)
        self.noopen = options.noopen
        self.config = options.config
        if options.host:
            self.hostlist = self.hostlist + options.host
        turbogears.widgets.load_widgets()


    def openbrowser(self):
        import webbrowser
        webbrowser.open("http://localhost:%d" % self.port)

    def run(self):
        from turbogears.toolbox.catwalk import CatWalk
        import cherrypy
        from turbogears import toolbox

        try:
            if get_package_name():
                conf = turbogears.config.config_obj( configfile = self.config,
                        modulename="%s.config" % get_package_name() )
            else:
                conf = turbogears.config.config_obj( configfile = self.config )
            
            new_conf = {}
            for key in ( "sqlobject.dburi", "sqlalchemy.dburi", "visit.on", "visit.manager", "visit.saprovider.model", 
                    "identity.provider", "identity.saprovider.model.group", "identity.saprovider.model.permission",
                    "identity.saprovider.model.user", "identity.saprovider.model.visit", "identity.on"):
                new_conf[key] = conf.get("global").get(key, None) 
            turbogears.config.update({"global" : new_conf})

        except AttributeError, e:
            pass

        root = SecureObject(toolbox.Toolbox(),from_any_host(self.hostlist), exclude=['noaccess'])

        cherrypy.tree.mount(root, "/")

        turbogears.config.update({"global" : {
            "server.socket_port" : self.port,
            "server.environment" : "development",
            "server.log_to_screen" : True,
            "autoreload.on" : False,
            "server.package" : "turbogears.toolbox",
            "log_debug_info_filter.on" : False,
            "identity.failure_url" : "/noaccess"
            }})

        if not self.noopen:
            cherrypy.server.start_with_callback(self.openbrowser)
        else:
            cherrypy.server.start()


commands = None

def main():
    "Main command runner. Manages the primary command line arguments."
    # add commands defined by entrypoints
    commands = {}
    for entrypoint in pkg_resources.iter_entry_points("turbogears.command"):
        command = entrypoint.load()
        commands[entrypoint.name] = (command.desc, entrypoint)
  
    def _help():
        "Custom help text for tg-admin."

        print """
TurboGears %s command line interface

Usage: %s [options] <command>

Options:
    -c CONFIG --config=CONFIG    Config file to use
    -e EGG_SPEC --egg=EGG_SPEC   Run command on given Egg

Commands:""" % (turbogears.__version__, sys.argv[0])

        longest = max([len(key) for key in commands.keys()])
        format = "%" + str(longest) + "s  %s"
        commandlist = commands.keys()
        commandlist.sort()
        for key in commandlist:
            print format % (key, commands[key][0])


    parser = optparse.OptionParser()
    parser.allow_interspersed_args = False
    parser.add_option("-c", "--config", dest="config")
    parser.add_option("-e", "--egg", dest="egg")
    parser.print_help = _help
    (options, args) = parser.parse_args(sys.argv[1:])

    # if not command is found display help
    if not args or not commands.has_key(args[0]):
        _help()
        sys.exit()

    commandname = args[0]
    # strip command and any global options from the sys.argv
    sys.argv = [sys.argv[0],] + args[1:]
    command = commands[commandname][1]
    command = command.load()
    
    if options.egg:
        egg = pkg_resources.get_distribution(options.egg)
        os.chdir(egg.location)

    if hasattr(command,"need_project"):
        if not turbogears.util.get_project_name():
            print "This command needs to be run from inside a project directory"
            return
        elif not options.config and not os.path.isfile(turbogears.util.get_project_config()):
            print """No default config file was found.
If it has been renamed use:
tg-admin --config=<FILE> %s""" % commandname
            return
    command.config = options.config
    command = command(turbogears.__version__)
    command.run()

__all__ = ["main"]
