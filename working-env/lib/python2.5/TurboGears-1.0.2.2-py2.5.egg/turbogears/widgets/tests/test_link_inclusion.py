import turbogears
import cherrypy

from turbogears import widgets, testutil

def test_table_widget_js():
    """
    The TableForm Widget can require JavaScript and CSS resources. Addresses
    ticket #425. Should be applicable to any widget.
    """
    class MyTableWithJS(widgets.TableForm):
        javascript = [widgets.JSLink(mod=widgets.static, name="foo.js"),
                      widgets.JSSource("alert('hello');")]
        css = [widgets.CSSLink(mod=widgets.static, name="foo.css")]

    form = MyTableWithJS(fields=[widgets.TextField(name='title')]) 

    class MyRoot(turbogears.controllers.RootController):
        def test(self):
            return dict(form=form)
        test = turbogears.expose(template=".form")(test)

    cherrypy.root = MyRoot()
    testutil.createRequest("/test")
    output = cherrypy.response.body[0]
    print output
    assert 'foo.js' in output
    assert "alert('hello');" in output
    assert 'foo.css' in output

def test_calendardatepicker_js():

    class MyRoot(turbogears.controllers.RootController):
        def test(self):
            return dict(widget=widgets.CalendarDatePicker())
        test = turbogears.expose(template=".widget")(test)
            
    cherrypy.root = MyRoot()

    # testing default language (en)
    testutil.createRequest("/test")
    output = cherrypy.response.body[0]
    print output
    assert 'calendar/calendar.js' in output
    assert 'calendar/calendar-setup.js' in output
    assert 'calendar/lang/calendar-en.js' in output

    # testing french language
    testutil.createRequest("/test", headers={"Accept-Language":"fr"})
    output = cherrypy.response.body[0]
    print output
    assert 'calendar/lang/calendar-fr.js' in output
