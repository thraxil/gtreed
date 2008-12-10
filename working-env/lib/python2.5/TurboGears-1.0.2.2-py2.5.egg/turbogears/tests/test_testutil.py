import cherrypy

import turbogears
from turbogears import controllers
from turbogears import testutil

class MyRoot(controllers.RootController):
    def set_name(self, name):
        cookies = cherrypy.response.simple_cookie
        cookies['name'] = name
        return "Hello " + name
    set_name = turbogears.expose()(set_name)

    def get_name(self):
        cookies = cherrypy.request.simple_cookie
        if 'name' in cookies:
            return cookies['name'].value
        else:
            return "cookie not found"
    get_name = turbogears.expose()(get_name)
        

def test_browser_session():
    cherrypy.root = MyRoot()
    bs = testutil.BrowsingSession()
    bs.goto('/get_name')
    assert bs.response == 'cookie not found'
    bs.goto('/set_name?name=me')
    bs.goto('/get_name')
    assert bs.response == 'me'

def test_browser_session_for_two_users():
    cherrypy.root = MyRoot()
    bs1 = testutil.BrowsingSession()
    bs2 = testutil.BrowsingSession()
    bs1.goto('/set_name?name=bs1')
    bs2.goto('/set_name?name=bs2')
    bs1.goto('/get_name')
    assert bs1.response == 'bs1'
    bs2.goto('/get_name')
    assert bs2.response == 'bs2'

