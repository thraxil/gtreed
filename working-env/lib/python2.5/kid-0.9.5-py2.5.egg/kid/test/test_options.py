"""Kid properties tests."""

__revision__ = "$Rev: 451 $"
__date__ = "$Date: 2006-12-19 08:05:46 -0500 (Tue, 19 Dec 2006) $"
__author__ = "David Stanek <dstanek@dstanek.com>"
__copyright__ = "Copyright 2006, David Stanek"
__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"

import kid.options
from kid.test.util import raises

def test_init():
    opts = dict(encoding="utf-8", output="html")

    options = kid.options.Options(opts)
    assert options.get("encoding") == "utf-8"
    assert options.get("output") == "html"

    options = kid.options.Options(opts, stuff=0)
    assert options.get("encoding") == "utf-8"
    assert options.get("output") == "html"
    assert options.get("stuff") == 0

    options = kid.options.Options(encoding="utf-8", output="html")
    assert options.get("encoding") == "utf-8"
    assert options.get("output") == "html"

def test_setters_getters0():
    options = kid.options.Options()
    options.set("encoding", "utf-8")
    options.set("output", "html")
    assert options.get("encoding") == "utf-8"
    assert options.get("output") == "html"

    assert options.get("not there", 0) == 0
    o = object()
    assert options.get("not there", o) == o

    options.remove("not there")
    options.remove("encoding")
    assert options.get("encoding") is None

def test_setters_getters1():
    options = kid.options.Options()
    options["encoding"] = "utf-8"
    options["output"] = "html"
    assert options["encoding"] == "utf-8"
    assert options["output"] == "html"

    def cause_error(name):
        return options[name]
    raises(KeyError, cause_error, "not there")

    def cause_error(name):
        del options[name]
    raises(KeyError, cause_error, "not there")
    del options["encoding"]
    assert options.get("encoding") is None

def test_isset():
    options = kid.options.Options(test=0)
    assert options.isset("test") == True
    assert options.isset("not there") == False
