import unittest
from cStringIO import StringIO
import sys
import turbogears
from turbogears import controllers
from turbogears import url
from turbogears import validators
from turbogears import database
from turbogears import testutil
import cherrypy
import formencode
import pkg_resources

class SubApp(controllers.RootController):
    def index(self):
        return url("/Foo/")
    index = turbogears.expose()(index)

class MyRoot(controllers.RootController):
    def index(self):
        pass
    index = turbogears.expose()(index)

    def validation_error_handler(self, tg_source, tg_errors, *args, **kw):
        self.functionname = tg_source.__name__
        self.values = kw
        self.errors = tg_errors
        return "Error Message"

    def test(self):
        return dict(title="Foobar", mybool=False, someval="niggles")
    test = turbogears.expose(html=".simple",
            allow_json=True)(test)

    def invalid(self):
        return None
    invalid = turbogears.expose()(invalid)

    def pos(self, posvalue):
        self.posvalue = posvalue
        return ""
    pos = turbogears.expose()(pos)

    def servefile(self, tg_exceptions=None):
        self.servedit = True
        self.serve_exceptions = tg_exceptions
        return cherrypy.lib.cptools.serveFile(
            pkg_resources.resource_filename(
                "turbogears.tests", "test_controllers.py"))
    servefile = turbogears.expose()(servefile)

    def unicode(self):
        cherrypy.response.headers["Content-Type"] = "text/html"
        return u'\u00bfHabla espa\u00f1ol?'
    unicode = turbogears.expose()(unicode)

    def returnedtemplate(self):
        return dict(title="Foobar", mybool=False, someval="foo",
            tg_template="turbogears.tests.simple")
    returnedtemplate = turbogears.expose()(returnedtemplate)

    def returnedtemplate_short(self):
        return dict(title="Foobar", mybool=False, someval="foo",
            tg_template=".simple")
    returnedtemplate_short = turbogears.expose()(returnedtemplate_short)

    def exposetemplate_short(self):
        return dict(title="Foobar", mybool=False, someval="foo")
    exposetemplate_short = turbogears.expose(html=".simple")(exposetemplate_short)

    def istrue(self, value):
        self.value = value
        return str(value)
    istrue = turbogears.error_handler(validation_error_handler)(istrue)
    istrue = turbogears.validate(validators={
                'value': validators.StringBoolean()})(istrue)
    istrue = turbogears.expose()(istrue)

    def callsanother(self):
        return self.istrue(True)
    callsanother = turbogears.expose()(callsanother)

    def returnjson(self):
        return dict(title="Foobar", mybool=False, someval="foo",
            tg_html="turbogears.tests.simple")
    returnjson = turbogears.expose(format="json",
            html="turbogears.tests.simple")(returnjson)

    def allowjson(self):
        return dict(title="Foobar", mybool=False, someval="foo",
             tg_html="turbogears.tests.simple")
    allowjson = turbogears.expose(html="turbogears.tests.simple",
            allow_json=False)(allowjson)

    def impliedjson(self):
        return dict(title="Blah")
    impliedjson = turbogears.expose(format="json")(impliedjson)

    def contenttype(self):
        return "Foobar"
    contenttype = turbogears.expose(content_type="xml/atom")(contenttype)

    def save(self, submit, firstname, lastname="Miller"):
        self.submit = submit
        self.firstname = firstname
        self.lastname = lastname
        self.fullname = "%s %s" % (self.firstname, self.lastname)
        return self.fullname
    save = turbogears.error_handler(validation_error_handler)(save)
    save = turbogears.validate(validators={
        "firstname": validators.String(min=2, not_empty=True),
        "lastname": validators.String()})(save)
    save = turbogears.expose()(save)

    class Registration(formencode.Schema):
        allow_extra_fields = True
        firstname = validators.String(min=2, not_empty=True)
        lastname = validators.String()

    def save2(self, submit, firstname, lastname="Miller"):
        return self.save(submit, firstname, lastname)
    save2 = turbogears.error_handler(validation_error_handler)(save2)
    save2 = turbogears.validate(validators=Registration())(save2)
    save2 = turbogears.expose()(save2)

    def useother(self):
        return dict(tg_template="turbogears.tests.othertemplate")
    useother = turbogears.expose(html="turbogears.tests.simple")(useother)

    rwt_called = 0
    def rwt(self, func, *args, **kw):
        self.rwt_called += 1
        func(*args, **kw)

    def flash_plain(self):
        turbogears.flash("plain")
        return dict(title="Foobar", mybool=False, someval="niggles")
    flash_plain = turbogears.expose(html=".simple",
        allow_json=True)(flash_plain)

    def flash_unicode(self):
        turbogears.flash(u"\xfcnicode")
        return dict(title="Foobar", mybool=False, someval="niggles")
    flash_unicode = turbogears.expose(html=".simple",
        allow_json=True)(flash_unicode)

    def flash_data_structure(self):
        turbogears.flash(dict(uni=u"\xfcnicode", testing=[1, 2, 3]))
        return dict(title="Foobar", mybool=False, someval="niggles")
    flash_data_structure = turbogears.expose(html=".simple",
        allow_json=True)(flash_data_structure)

    def flash_redirect(self):
        turbogears.flash(u"redirect \xfcnicode")
        turbogears.redirect("/flash_redirected?tg_format=json")
    flash_redirect = turbogears.expose(html=".simple",
        allow_json=True)(flash_redirect)

    def flash_redirected(self):
        return dict(title="Foobar", mybool=False, someval="niggles")
    flash_redirected = turbogears.expose(html=".simple",
        allow_json=True)(flash_redirected)


class TestRoot(unittest.TestCase):
    def setUp(self):
        cherrypy.root = None
        cherrypy.tree.mount_points = {}
        cherrypy.tree.mount(MyRoot(), "/")
        cherrypy.tree.mount(SubApp(), "/subthing")

    def tearDown(self):
        cherrypy.root = None
        cherrypy.tree.mount_points = {}

    def test_jsFiles(self):
        'Can access the JavaScript files'
        testutil.createRequest("/tg_js/MochiKit.js")
        self.failUnlessEqual("application/x-javascript",
            cherrypy.response.headers["Content-Type"])
        self.failUnlessEqual("200 OK", cherrypy.response.status)

    def test_jsonOutput(self):
        testutil.createRequest("/test?tg_format=json")
        import simplejson
        values = simplejson.loads(cherrypy.response.body[0])
        assert values == dict(title="Foobar", mybool=False, someval="niggles",
            tg_flash=None)
        assert cherrypy.response.headers["Content-Type"] == "text/javascript"

    def test_impliedJson(self):
        testutil.createRequest("/impliedjson?tg_format=json")
        assert '"title": "Blah"' in cherrypy.response.body[0]

    def test_allowJson(self):
        testutil.createRequest("/allowjson?tg_format=json")
        assert cherrypy.response.headers["Content-Type"] == "text/html"

    def test_allowJsonConfig(self):
        "JSON output can be enabled via config."
        turbogears.config.update({'tg.allow_json':True})
        testutil.capture_log("tubrogears.controllers")
        class JSONRoot(controllers.RootController):
            def allowjsonconfig(self):
                return dict(title="Foobar", mybool=False, someval="foo",
                     tg_html="turbogears.tests.simple")
            allowjsonconfig = turbogears.expose(html="turbogears.tests.simple")(allowjsonconfig)
        testutil.print_log()
        cherrypy.root = JSONRoot()
        testutil.createRequest('/allowjsonconfig?tg_format=json')
        assert cherrypy.response.headers["Content-Type"]=="text/javascript"
        turbogears.config.update({'tg.allow_json':False})

    def test_allowJsonConfigFalse(self):
        "Make sure JSON can still be restricted with a global config on."
        turbogears.config.update({'tg.allow_json':True})
        testutil.capture_log("tubrogears.controllers")
        class JSONRoot(controllers.RootController):
            def allowjsonconfig(self):
                return dict(title="Foobar", mybool=False, someval="foo",
                     tg_html="turbogears.tests.simple")
            allowjsonconfig = turbogears.expose(html="turbogears.tests.simple")(allowjsonconfig)
        testutil.print_log()
        cherrypy.root = JSONRoot()
        testutil.createRequest('/allowjson?tg_format=json')
        print cherrypy.response.body[0]
        assert cherrypy.response.headers["Content-Type"]=="text/html"
        turbogears.config.update({'tg.allow_json':False})

    def test_invalidreturn(self):
        testutil.create_request("/invalid")
        print cherrypy.response.status
        assert cherrypy.response.status.startswith("500")

    def test_strict_parameters(self):
        turbogears.config.update({"tg.strict_parameters" : True})
        testutil.create_request("/save?submit=save&firstname=Foo&lastname=Bar&badparam=1")
        print cherrypy.response.status
        assert cherrypy.response.status.startswith("500")
        assert not hasattr(cherrypy.root, "errors")

    def test_retrieveDictDirectly(self):
        d = testutil.call(cherrypy.root.returnjson)
        assert d["title"] == "Foobar"

    def test_templateOutput(self):
        testutil.createRequest("/test")
        assert "Paging all niggles" in cherrypy.response.body[0]

    def test_throw_out_random(self):
        """A random value can be appended to the URL to avoid caching
        problems."""
        testutil.createRequest("/test?tg_random=1")
        assert "Paging all niggles" in cherrypy.response.body[0]

    def test_safariUnicodeFix(self):
        testutil.createRequest("/unicode", headers={'User-Agent' :
            "Apple WebKit Safari/412.2"})
        firstline = cherrypy.response.body[0].split('\n')[0]
        self.failUnlessEqual("&#xbf;Habla espa&#xf1;ol?", firstline)
        self.failUnless(isinstance(firstline, str))

    def test_defaultFormat(self):
        """The default format can be set via expose"""
        testutil.createRequest("/returnjson")
        firstline = cherrypy.response.body[0]
        assert '"title": "Foobar"' in firstline
        testutil.createRequest("/returnjson?tg_format=html")
        firstline = cherrypy.response.body[0]
        assert '"title": "Foobar"' not in firstline

    def test_contentType(self):
        """The content-type can be set via expose"""
        testutil.createRequest("/contenttype")
        assert cherrypy.response.headers["Content-Type"] == "xml/atom"

    def test_returnedTemplateName(self):
        testutil.createRequest("/returnedtemplate")
        data = cherrypy.response.body[0].lower()
        assert "<body>" in data
        assert 'groovy test template' in data

    def test_returnedTemplateShort(self):
        testutil.createRequest("/returnedtemplate_short")
        assert "Paging all foo" in cherrypy.response.body[0]

    def test_exposeTemplateShort(self):
        testutil.createRequest("/exposetemplate_short")
        assert "Paging all foo" in cherrypy.response.body[0]

    def test_validation(self):
        "Data can be converted and validated"
        testutil.createRequest("/istrue?value=true")
        assert cherrypy.root.value is True
        testutil.createRequest("/istrue?value=false")
        assert cherrypy.root.value is False
        cherrypy.root = MyRoot()
        testutil.createRequest("/istrue?value=foo")
        assert not hasattr(cherrypy.root, "value")
        assert cherrypy.root.functionname == "istrue"

        testutil.createRequest("/save?submit=send&firstname=John&lastname=Doe")
        assert cherrypy.root.fullname == "John Doe"
        assert cherrypy.root.submit == "send"
        testutil.createRequest("/save?submit=send&firstname=Arthur")
        assert cherrypy.root.fullname == "Arthur Miller"
        testutil.createRequest("/save?submit=send&firstname=Arthur&lastname=")
        assert cherrypy.root.fullname == "Arthur "
        testutil.createRequest("/save?submit=send&firstname=D&lastname=")
        assert len(cherrypy.root.errors) == 1
        assert cherrypy.root.errors.has_key("firstname")
        assert "characters" in cherrypy.root.errors["firstname"].msg.lower()
        testutil.createRequest("/save?submit=send&firstname=&lastname=")
        assert len(cherrypy.root.errors) == 1
        assert cherrypy.root.errors.has_key("firstname")

    def test_validationwithschema(self):
        "Data can be converted and validated with formencode.Schema instance"
        testutil.createRequest("/save2?submit=send&firstname=John&lastname=Doe")
        assert cherrypy.root.fullname == "John Doe"
        assert cherrypy.root.submit == "send"
        testutil.createRequest("/save2?submit=send&firstname=Arthur&lastname=")
        assert cherrypy.root.fullname == "Arthur "
        testutil.createRequest("/save2?submit=send&firstname=&lastname=")
        assert len(cherrypy.root.errors) == 1
        assert cherrypy.root.errors.has_key("firstname")
        testutil.createRequest("/save2?submit=send&firstname=D&lastname=")
        assert len(cherrypy.root.errors) == 1
        assert cherrypy.root.errors.has_key("firstname")

    def test_othertemplate(self):
        "'tg_html' in a returned dict will use the template specified there"
        testutil.createRequest("/useother")
        assert "This is the other template" in cherrypy.response.body[0]

    def test_runwithtrans(self):
        "run_with_transaction is called only on topmost exposed method"
        oldrwt = database.run_with_transaction
        database.run_with_transaction = cherrypy.root.rwt
        testutil.createRequest("/callsanother")
        database.run_with_transaction = oldrwt
        assert cherrypy.root.value
        assert cherrypy.root.rwt_called == 1

    def test_positional(self):
        "Positional parameters should work"
        testutil.createRequest("/pos/foo")
        assert cherrypy.root.posvalue == "foo"

    def test_flash_plain(self):
        "turbogears.flash with strings should work"
        testutil.createRequest("/flash_plain?tg_format=json")
        import simplejson
        values = simplejson.loads(cherrypy.response.body[0])
        assert values["tg_flash"]=="plain"
        assert not cherrypy.response.simple_cookie.has_key("tg_flash")

    def test_flash_unicode(self):
        "turbogears.flash with unicode objects should work"
        testutil.createRequest("/flash_unicode?tg_format=json")
        import simplejson
        values = simplejson.loads(cherrypy.response.body[0])
        assert values["tg_flash"]==u"\xfcnicode"
        assert not cherrypy.response.simple_cookie.has_key("tg_flash")

    def test_flash_on_redirect(self):
        "turbogears.flash must survive a redirect"
        testutil.createRequest("/flash_redirect?tg_format=json")
        assert cherrypy.response.status.startswith("302")
        testutil.createRequest(
            cherrypy.response.headers["Location"],
            headers=dict(Cookie=cherrypy.response.simple_cookie.output(header="").strip()))
        import simplejson
        values = simplejson.loads(cherrypy.response.body[0])
        assert values["tg_flash"]==u"redirect \xfcnicode"

    def test_double_flash(self):
        """latest set flash should have precedence"""
        # Here we are calling method that sets a flash message. However flash
        # cookie is still there. Turbogears should discard old flash message
        # from cookie and use new one, set by flash_plain().
        testutil.createRequest("/flash_plain?tg_format=json",
                               headers=dict(Cookie='tg_flash="old flash"; Path=/;'))
        import simplejson
        values = simplejson.loads(cherrypy.response.body[0])
        assert values["tg_flash"]=="plain"
        assert cherrypy.response.simple_cookie.has_key("tg_flash"), \
                "Cookie clearing request should be present"
        flashcookie = cherrypy.response.simple_cookie['tg_flash']
        assert flashcookie['expires'] == 0

    def test_set_kid_outputformat_in_config(self):
        "the outputformat for kid can be set in the config"
        turbogears.config.update({'kid.outputformat': 'xhtml'})
        testutil.createRequest('/test')
        assert '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML ' in cherrypy.response.body[0]
        turbogears.config.update({'kid.outputformat': 'html'})
        testutil.createRequest('/test')
        assert  '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML ' in cherrypy.response.body[0]

    def test_fileserving(self):
        #outputcap = StringIO()
        #sys.stdout = outputcap
        testutil.create_request("/servefile")
        assert cherrypy.root.servedit
        assert not cherrypy.root.serve_exceptions
        #assert "AssertionError" not in outputcap.getvalue()

class TestURLs(unittest.TestCase):
    def setUp(self):
        cherrypy.tree.mount_points = {}
        cherrypy.root = MyRoot()
        cherrypy.root.subthing = SubApp()
        cherrypy.root.subthing.subsubthing = SubApp()

    def test_basicurls(self):
        testutil.createRequest("/")
        self.failUnlessEqual("/foo", url("/foo"))
        self.failUnlessEqual("foo/bar", url(["foo", "bar"]))
        assert url("/foo", bar=1, baz=2) in \
                ["/foo?bar=1&baz=2", "/foo?baz=2&bar=1"]
        assert url("/foo", dict(bar=1, baz=2)) in \
                ["/foo?bar=1&baz=2", "/foo?baz=2&bar=1"]
        assert url("/foo", dict(bar=1, baz=None)) == "/foo?bar=1"

    def test_url_without_request_available(self):
        cherrypy.serving.request = None
        self.assertEquals("/foo", turbogears.url("/foo"))

    def test_approots(self):
        testutil.createRequest("/subthing/")
        self.failUnlessEqual("foo", url("foo"))
        self.failUnlessEqual("/subthing/foo", url("/foo"))

    def test_lowerapproots(self):
        testutil.create_request("/subthing/subsubthing/")
        print url("/foo")
        assert "/subthing/subsubthing/foo" == url("/foo")

    def test_approotsWithPath(self):
        turbogears.config.update({"server.webpath" : "/coolsite/root"})
        turbogears.startup.startTurboGears()
        testutil.createRequest("/coolsite/root/subthing/")
        print cherrypy.tree.mount_point()
        self.failUnlessEqual("/coolsite/root/subthing/foo",
                        url("/foo"))

    def test_redirect(self):
        turbogears.config.update({"server.webpath" : "/coolsite/root"})
        turbogears.startup.startTurboGears()
        testutil.createRequest("/coolsite/root/subthing/")
        try:
            turbogears.redirect("/foo")
            assert False, "redirect exception should have been raised"
        except cherrypy.HTTPRedirect, e:
            print e.urls
            assert "http://localhost/coolsite/root/subthing/foo" in e.urls

        try:
            raise turbogears.redirect("/foo")
            assert False, "redirect exception should have been raised"
        except cherrypy.HTTPRedirect, e:
            print e.urls
            assert "http://localhost/coolsite/root/subthing/foo" in e.urls


    def tearDown(self):
        turbogears.config.update({"server.webpath" : ""})
        turbogears.startup.startTurboGears()

def test_index_trailing_slash():
    "If there is no trailing slash on an index method call, redirect"
    cherrypy.root = SubApp()
    cherrypy.root.foo = SubApp()
    testutil.createRequest("/foo")
    print cherrypy.response.status
    assert cherrypy.response.status.startswith("302")

def test_can_use_internally_defined_arguments():
    """Tests that we can use argument names that are internally used by TG
    in controllers:_execute_func et al."""
    class App(controllers.RootController):
        def index(self, **kw):
            return "\n".join(["%s:%s" % i for i in kw.iteritems()])
        index = turbogears.expose()(index)

    cherrypy.root = App()
    testutil.createRequest("/?format=foo&template=bar&fragment=boo")
    output = cherrypy.response.body[0]
    print output
    assert "format:foo" in output
    assert "template:bar" in output
    assert "fragment:boo" in output
