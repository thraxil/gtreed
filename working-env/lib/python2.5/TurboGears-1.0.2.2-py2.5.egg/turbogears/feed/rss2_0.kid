<?python
from turbogears import url
?>
<rss version="2.0" xmlns:py="http://purl.org/kid/ns#">
<channel>

  <title py:if="hasattr(self, 'title')" py:content="title">myfeed</title>
  <link py:if="hasattr(self, 'link')" py:content="link">link</link>
  <description py:if="hasattr(self, 'subtitle')" py:content="subtitle">description</description>
  <lastBuildDate py:if="hasattr(self, 'updated')" py:content="updated">lastBuildDate</lastBuildDate>
  <language py:if="hasattr(self, 'lang')" py:content="lang">lang</language>
  <generator py:if="hasattr(self, 'generator')" py:content="generator">generated</generator>

  <item py:for="entry in entries">
    <title py:if="entry.has_key('title')" py:content="entry['title']">title</title>
    <guid py:if="entry.has_key('id')" py:content="entry['id']">guid</guid>
    <link py:if="entry.has_key('link')" py:content="entry['link']">link</link>
    <pubDate py:if="entry.has_key('published')" py:content="entry['published']">pubDate</pubDate>
    <description py:if="entry.has_key('summary')" py:content="entry['summary']">description</description>
  </item>
  
</channel>
</rss>
