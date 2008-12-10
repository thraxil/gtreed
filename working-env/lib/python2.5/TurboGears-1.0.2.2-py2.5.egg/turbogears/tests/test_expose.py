import cherrypy
import simplejson

from turbogears import controllers, expose
from turbogears.testutil import create_request, capture_log, get_log, \
                                print_log

class ExposeRoot(controllers.RootController):
    [expose("turbogears.tests.simple")]
    [expose("json")]
    def with_json(self):
        return dict(title="Foobar", mybool=False, someval="foo")

    [expose("turbogears.tests.simple")]
    [expose("json", accept_format = "text/javascript", as_format="json")]
    [expose('cheetah:turbogears.tests.textfmt', accept_format="text/plain")]
    def with_json_via_accept(self):
        return dict(title="Foobar", mybool=False, someval="foo")

cherrypy.root = ExposeRoot()
logged = None

def test_gettinghtml():
    global logged
    capture_log("turbogears.controllers")
    create_request("/with_json")
    logged = get_log()
    body = cherrypy.response.body[0]
    print body
    assert "Paging all foo" in body

def test_gettingjson():
    create_request("/with_json?tg_format=json")
    print "\n".join(logged)
    body = cherrypy.response.body[0]
    print body
    assert '"title": "Foobar"' in body

def test_gettingjsonviaaccept():
    create_request("/with_json_via_accept",
            headers=dict(Accept="text/javascript"))
    print "\n".join(logged)
    body = cherrypy.response.body[0]
    print body
    assert '"title": "Foobar"' in body

def test_getting_json_with_accept_but_using_tg_format():
    capture_log("turbogears.controllers")
    create_request("/with_json_via_accept?tg_format=json")
    print_log()
    print "\n".join(logged)
    body = cherrypy.response.body[0]
    print body
    assert '"title": "Foobar"' in body

def test_getting_plaintext():
    create_request("/with_json_via_accept",
        headers=dict(Accept="text/plain"))
    print "\n".join(logged)
    print cherrypy.response.body[0]
    assert cherrypy.response.body[0] == "This is a plain text for foo."
    
def test_allow_json():
    class NewRoot(controllers.RootController):
        [expose(template="turbogears.test.simple", allow_json=True)]
        def test(self):
            return dict(title="Foobar", mybool=False, someval="niggles")

    cherrypy.root = NewRoot()
    capture_log("turbogears.controllers")
    create_request("/test", headers= dict(accept="text/javascript"))
    print_log()
    print cherrypy.response.body[0]
    values = simplejson.loads(cherrypy.response.body[0])
    assert values == dict(title="Foobar", mybool=False, someval="niggles",
        tg_flash=None)
    assert cherrypy.response.headers["Content-Type"] == "text/javascript"

    create_request("/test?tg_format=json")
    print cherrypy.response.body[0]
    values = simplejson.loads(cherrypy.response.body[0])
    assert values == dict(title="Foobar", mybool=False, someval="niggles",
        tg_flash=None)
    assert cherrypy.response.headers["Content-Type"] == "text/javascript"

