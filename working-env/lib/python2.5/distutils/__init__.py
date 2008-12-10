import os

dirname = os.path.dirname
lib_dir = dirname(dirname(__file__))
working_env = dirname(dirname(lib_dir))

# This way we run first, but distutils still gets imported:
distutils_path = os.path.join(os.path.dirname(os.__file__), 'distutils')
__path__.insert(0, distutils_path)
exec open(os.path.join(distutils_path, '__init__.py')).read()

import dist
def make_repl(v):
    if isinstance(v, basestring):
        return v.replace('__WORKING__', working_env)
    else:
        return v
    
old_parse_config_files = dist.Distribution.parse_config_files
def parse_config_files(self, filenames=None):
    old_parse_config_files(self, filenames)
    for d in self.command_options.values():
        for name, value in d.items():
            if isinstance(value, list):
                value = [make_repl(v) for v in value]
            elif isinstance(value, tuple):
                value = tuple([make_repl(v) for v in value])
            elif isinstance(value, basestring):
                value = make_repl(value)
            else:
                print "unknown: %s=%r" % (name, value)
            d[name] = value
dist.Distribution.parse_config_files = parse_config_files

old_find_config_files = dist.Distribution.find_config_files
def find_config_files(self):
    found = old_find_config_files(self)
    system_distutils = os.path.join(distutils_path, 'distutils.cfg')
    if os.path.exists(system_distutils):
        found.insert(0, system_distutils)
    return found
dist.Distribution.find_config_files = find_config_files
