<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xmlns:py="http://purl.org/kid/ns#"
      xml:lang="en">
  <title>${item.title}</title>
  <link rel="alternate" type="text/html"
	href="http://gtd.thraxil.org/items/${item.id}/" />
  <link rel="self" type="application/atom+xml" 
	href="http://gtd.thraxil.org/atom/${item.id}/" />
  <updated>${item.modified.isoformat()}-05:00</updated>
  <generator uri="http://gtd.thraxil.org/" version="0.1">GTreeD</generator>
  <id>http://gtd.thraxil.org/items/${item.id}/</id>

  <entry py:for="child in item.get_open_children()">
    <author>
      <name>${child.assigned_to.display_name}</name>
    </author>
    <title>${child.title}</title>
    <link type="text/html" rel="alternate"
	  href="http://gtd.thraxil.org/item/${child.id}/"/>
    <id>http://gtd.thraxil.org/item/${child.id}/</id>
    <published>${child.added.isoformat()}-05:00</published>
    <updated>${child.modified.isoformat()}-05:00</updated>
    
    <content py:if="child.description" type="html" xml:base="http://gtd.thraxil.org/item/${child.id}/">
      ${child.description}
    </content>

    <summary py:if="child.description" type="html" xml:base="http://gtd.thraxil.org/item/${child.id}/">
      ${child.description}
    </summary>

    <summary py:if="not child.description" type="html" xml:base="http://gtd.thraxil.org/item/${child.id}/">
      ${child.title}
    </summary>
    

  </entry>

</feed>
