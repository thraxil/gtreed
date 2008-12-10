import sys
import os
import kid
import tempfile

from datetime import datetime

import turbogears
from turbogears.command.i18n import InternationalizationTool

work_dir = tempfile.mkdtemp()
locale_dir = os.path.join(work_dir, 'locale')
tool = None

turbogears.config.update({
    'i18n.locale_dir':locale_dir,
    'i18n.domain':'testmessages',
})

def setup(m):
    global tool
    tool = InternationalizationTool('0.9')

def teardown(m):
    import shutil
    shutil.rmtree(work_dir)

def test_creates_locale_dir():
    "Verify the locale directory got created as needed."
    assert not os.path.isdir(locale_dir)
    test_src_dir = os.path.join(work_dir, 'src')
    sys.argv = ['i18n.py', '--src-dir', test_src_dir, 'collect'] 
    tool.run()
    assert os.path.isdir(locale_dir), "locale directory not created"
