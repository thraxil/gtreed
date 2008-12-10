<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>GTreeD: search for ${q}</title>
</head>
<body>
<div id="header">&nbsp;</div>
<div id="main_content">
  ${sidebar()}
  <div id="page-content">
    <h1>search results for: ${q}</h1>
    <ul>
      <li py:for="item in items" class="${item.status}"><a href="/item/${item.id}/">${item.title}</a></li>
    </ul>

  </div>
</div>
</body>
</html>
