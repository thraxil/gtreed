
import os.path
import tempfile

from turbogears.i18n import sogettext
import turbogears

def setup_module():
    basedir = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__)))), "tests")
    locale_dir = os.path.join(basedir, 'locale')
    turbogears.config.update({
        'i18n.locale_dir':locale_dir,
        'i18n.domain':'messages',
        'i18n.default_locale':'en',
        'i18n.get_locale':lambda: 'en',
        'i18n.run_template_filter':False,
        'sqlobject.dburi':"sqlite:///" + tempfile.gettempdir()  + "/testlocaledb"
    })
    sogettext.create_so_catalog(["en","fi"], "messages")

