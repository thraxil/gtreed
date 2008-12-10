import os, re

from cherrypy import request
import pkg_resources
from turbogears import util as tg_util

from turbogears.validators import FancyValidator

class HTMLCleaner(FancyValidator):
    """Strips off the ugly <br />s TinyMCE leaves the end of pasted text"""
    cleaner = re.compile(r'(\s*<br />\s*)+$').sub 
    def to_python(self, value, state=None):
        return self.cleaner('', value)


def get_available_languages():
    locale_dir = pkg_resources.resource_filename(
        "tinymce", "static/javascript/langs"
        )
    langs = filter(
        lambda l: len(l)>0, 
        [lang.split('.')[0] for lang in os.listdir(locale_dir)]
        )
    return langs

def cache_for_request(key):
    """Caches the decorated function's result for the remainder of the request.
    @params:
        key: Unique key for indexing the function's result in the cache dict
    """
    def decorator(func):
        def _cached(*args, **kw):
            if not tg_util.request_available():
                return func(*args, **kw)
            try:
                output = request._f_cache[key]
            except AttributeError:
                output = func(*args, **kw)
                request._f_cache = {key:output}
            except KeyError:
                output = request._f_cache[key] = func(*args, **kw)
            return output
        try: _cached.func_name = 'cached_' + func.func_name
        except TypeError: pass
        return _cached
    return decorator
        
