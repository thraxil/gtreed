import time

import cherrypy

import turbogears
from warnings import warn

class FeedController(turbogears.controllers.Controller):
    """ Object for generating feeds in multiple formats """

    def __init__(self, default="atom1.0"):
        self.default = default
        self.formats = ["atom1.0", "atom0.3", "rss2.0"]

    def date_to_3339(self, date):
        date = date.strftime("%Y-%m-%dT%H:%M:%SZ")
        return date

    def date_to_822(self, date):
        date = date.strftime("%a, %d %b %Y %H:%M:%S GMT")
        return date
    
    def depr_entrys(self, feed):
        if "entrys" in feed:
            warn("You should use 'entries' instead of 'entrys'",
                DeprecationWarning, 3)
            feed['entries'] = feed['entrys']
            del feed['entrys']

    def format_dates(self, feed, format):
        if format == 822:
            convert_date = self.date_to_822
        else:
            convert_date = self.date_to_3339
        if feed.has_key('updated'):
            feed["updated"] = convert_date(feed["updated"])
        self.depr_entrys(feed)
        for entry in feed['entries']:
            if entry.has_key('updated'):
                entry["updated"] = convert_date(entry["updated"])
            if entry.has_key('published'):
                entry["published"] = convert_date(entry["published"])
        return feed

    def index(self):
        raise cherrypy.HTTPRedirect(turbogears.url("%s" % self.default))
    index = turbogears.expose()(index)

    def atom1_0(self, **kwargs):
        feed = self.get_feed_data(**kwargs)
        self.format_dates(feed, 3339)
        feed["href"] = turbogears.url("/") + "atom1.0"
        self.depr_entrys(feed)
        return feed
    atom1_0 = turbogears.expose(template="turbogears.feed.atom1_0",
                    format="xml", content_type="application/atom+xml")(atom1_0)

    def atom0_3(self, **kwargs):
        feed = self.get_feed_data(**kwargs)
        self.format_dates(feed, 3339)
        feed["href"] = turbogears.url("/") + "atom0.3"
        self.depr_entrys(feed)
        return feed
    atom0_3 = turbogears.expose(template="turbogears.feed.atom0_3",
                    format="xml", content_type="application/atom+xml")(atom0_3)

    def rss2_0(self, **kwargs):
        feed = self.get_feed_data(**kwargs)
        self.format_dates(feed, 822)
        self.depr_entrys(feed)
        return feed
    rss2_0 = turbogears.expose(template="turbogears.feed.rss2_0",
                    format="xml", content_type="application/rss+xml")(rss2_0)
