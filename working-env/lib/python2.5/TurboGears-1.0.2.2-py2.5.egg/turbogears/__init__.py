"TurboGears Front-to-Back Web Framework"

import pkg_resources

from turbogears import config
from turbogears.controllers import expose, flash, validate, redirect, \
                                   error_handler, exception_handler, url
from turbogears import controllers, view, database, validators, command, \
                       i18n, widgets, startup, scheduler
from turbogears.release import version as __version__, author as __author__, \
                               email as __email__, license as __license__, \
                               copyright as __copyright__
from turbogears.widgets import mochikit
from turbogears.config import update_config
from turbogears.paginate import paginate

from turbogears.startup import start_server

extensions = pkg_resources.iter_entry_points("turbogears.extensions")
for entrypoint in extensions:
    ext = entrypoint.load()
    if hasattr(ext, "tgsymbols"):
        globals().update(ext.tgsymbols())

i18n.install() # adds _ (gettext) to builtins namespace


__all__ = ["url", "expose", "redirect", "validate", "flash",
           "error_handler", "exception_handler",
           "view", "controllers", "update_config",
           "database", "command", "validators", "mochikit", "widgets",
           "config", "start_server", "scheduler"]
