<?xml version="1.0" encoding="utf-8"?>
<?python
from turbogears import url
?>
<feed version="0.3" xmlns="http://purl.org/atom/ns#" xmlns:py="http://purl.org/kid/ns#">

  <id py:content="id">id</id>
  <title py:if="hasattr(self, 'title')" py:content="title">myfeed</title>
  <modified py:if="hasattr(self, 'updated')" py:content="updated">modified</modified>
  <author py:if="hasattr(self, 'author')">
    <name py:content="author['name']">name</name>
    <email py:if="author.has_key('email')" py:content="author['email']">email</email>
    <uri py:if="author.has_key('uri')" py:content="author['uri']">uri</uri>
  </author>
  <link py:if="hasattr(self, 'href')" rel="alternate" href="${href}" />
  <copyright py:if="hasattr(self, 'rights')" py:content="rights">copyright</copyright>
  <tagline py:if="hasattr(self, 'subtitle')" py:content="subtitle">tagline</tagline>

  <entry py:for="entry in entries">
    <title py:if="entry.has_key('title')" py:content="entry['title']">title</title>
    <id py:if="entry.has_key('id')" py:content="entry['id']">id</id>
    <modified py:if="entry.has_key('updated')" py:content="entry['updated']">modified</modified>
    <link py:if="entry.has_key('link')" rel="alternate" href="${entry['link']}" />
    <issued py:if="entry.has_key('published')" py:content="entry['published']">issued</issued>
    <author py:if="entry.has_key('author')">
        <name py:content="entry['author']['name']">name</name>
        <email py:if="entry['author'].has_key('email')" py:content="entry['author']['email']">email</email>
        <uri py:if="entry['author'].has_key('uri')" py:content="entry['author']['uri']">uri</uri>
    </author>
    <content py:if="entry.has_key('content')" py:content="entry['content']">content</content>
    <summary py:if="entry.has_key('summary')" py:content="entry['summary']">summary</summary>
    <copyright py:if="entry.has_key('rights')" py:rights="entry['rights']">copyright</copyright>

  </entry>

</feed>
