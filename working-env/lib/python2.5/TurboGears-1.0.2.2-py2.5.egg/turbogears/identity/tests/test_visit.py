import unittest
from turbogears import testutil
import turbogears
import cherrypy
import time

def cookie_header(morsel):
    """Returns a dict containing cookie information to pass to a server."""
    return {'Cookie': morsel.output(header="")[1:]}

class VisitRoot(turbogears.controllers.RootController):

    def index(self):
        pass
    index = turbogears.expose()(index)

class TestVisit(unittest.TestCase):

    def setUp(self):
        self._visit_on = turbogears.config.get('visit.on', False)
        turbogears.config.update({'visit.on': True})
        self.cookie_name = turbogears.config.get("visit.cookie.name", 'tg-visit')
        cherrypy.root = VisitRoot()

    def tearDown(self):
        turbogears.config.update({'visit.on': self._visit_on})

    def test_visit_response(self):
        "Test if the visit cookie is set in cherrypy.response."
        testutil.create_request("/")
        assert cherrypy.response.simple_cookie.has_key(self.cookie_name)
        # the following command shuts down the visit framework properly
        # the test still passes without it, but exceptions are thrown later
        # once nose wants to quit.
        turbogears.startup.stopTurboGears()

    def test_new_visit(self):
        "Test that we can see a new visit on the server."
        testutil.create_request("/")
        assert turbogears.visit.current().is_new
        turbogears.startup.stopTurboGears()

    def test_old_visit(self):
        "Test if we can track a visitor over time."
        testutil.create_request("/")
        morsel = cherrypy.response.simple_cookie[self.cookie_name] #first visit's cookie
        testutil.create_request("/", headers=cookie_header(morsel))
        assert not turbogears.visit.current().is_new
        turbogears.startup.stopTurboGears()

    def test_cookie_expires(self):
        "Test if the visit timeout mechanism works."
        turbogears.config.update({'visit.timeout':1.0/60.0})  # set expiration to one second
        testutil.create_request("/")
        morsel = cherrypy.response.simple_cookie[self.cookie_name]
        time.sleep(3)  # 3 seconds
        testutil.create_request("/", headers=cookie_header(morsel))
        assert cherrypy.response.simple_cookie[self.cookie_name].value != morsel.value, 'cookie values should not match'
        assert turbogears.visit.current().is_new, 'this should be a new visit, as the cookie has expired'
        turbogears.startup.stopTurboGears()
