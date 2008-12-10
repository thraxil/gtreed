import os, sys
from distutils import log
# setuptools should be on sys.path already from a .pth file

for path in sys.path:
    if 'setuptools' in path:
        setuptools_path = os.path.join(path, 'setuptools')
        __path__.insert(0, setuptools_path)
        break
else:
    raise ImportError(
        'Cannot find setuptools on sys.path; is setuptools.pth missing?')

execfile(os.path.join(setuptools_path, '__init__.py'))
import setuptools.command.easy_install as easy_install

def get_script_header(script_text, executable=easy_install.sys_executable,
                      wininst=False):
    from distutils.command.build_scripts import first_line_re
    first, rest = (script_text+'\n').split('\n',1)
    match = first_line_re.match(first)
    options = ''
    if match:
        script_text = rest
        options = match.group(1) or ''
        if options:
            options = ' '+options
    if wininst:
        executable = "python.exe"
    else:
        executable = easy_install.nt_quote_arg(executable)
    if options.find('-S') == -1:
        options += ' -S'
    shbang = "#!%(executable)s%(options)s\n" % locals()
    shbang += ("import sys, os\n"
               "join, dirname, abspath = os.path.join, os.path.dirname, os.path.abspath\n"
               "site_dirs = [join(dirname(dirname(abspath(__file__))), 'lib', 'python%s.%s' % tuple(sys.version_info[:2])), join(dirname(dirname(abspath(__file__))), 'lib', 'python')]\n"
               "sys.path[0:0] = site_dirs\n"
               "import site\n"
               "[site.addsitedir(d) for d in site_dirs]\n")
    return shbang

def install_site_py(self):
    # to heck with this, we gots our own site.py and we'd like
    # to keep it, thank you
    pass

old_process_distribution = easy_install.easy_install.process_distribution

def process_distribution(self, requirement, dist, deps=True, *info):
    old_process_distribution(self, requirement, dist, deps, *info)
    log.info('Finished installing %s', requirement)

easy_install.get_script_header = get_script_header
easy_install.easy_install.install_site_py = install_site_py
easy_install.easy_install.process_distribution = process_distribution
