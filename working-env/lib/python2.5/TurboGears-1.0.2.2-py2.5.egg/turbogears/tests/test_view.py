# -*- coding: utf-8 -*- 

from turbogears import view, config
import unittest

class TestView(unittest.TestCase):

    def test_UnicodeValueAppearingInATemplateIsFine(self):
        ustr = u"micro-eXtreme Programming ( µ XP): Embedding XP Within Standard Projects"
        info = dict(someval=ustr)
        val = view.render(info, template="turbogears.tests.simple")
        self.failUnless(u"Paging all " + ustr in val.decode("utf-8"))

    def test_templateRetrievalByPath(self):
        config.update({'server.environment' : 'development'})
        from turbokid import kidsupport
        ks = kidsupport.KidSupport()
        cls = ks.load_template("turbogears.tests.simple")
        assert cls is not None
        t = cls()
        t.someval = "hello"
        filled = str(t)
        assert "groovy" in filled
        assert "html" in filled
        
        # the following import should not fail, if everything is working correctly.
        import turbogears.tests.simple

    def test_default_output_encoding(self):
        info = dict(someval="someval")
        # default encoding is utf-8
        val = view.render(info, template="turbogears.tests.simple")
        assert 'utf-8' in view.cherrypy.response.headers["Content-Type"]
        config.update({'tg.defaultview':'kid', 'kid.encoding':'iso-8859-1'})
        val = view.render(info, template="turbogears.tests.simple")
        assert 'iso-8859-1' in view.cherrypy.response.headers["Content-Type"]
