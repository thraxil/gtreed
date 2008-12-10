<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to TurboGears</title>
</head>
<body>
<div id="header">&nbsp;</div>
<div id="main_content" py:if="not tg.identity.anonymous">
  ${sidebar()}
  <div id="page-content">
    <ul>
      <li py:for="item in tg.identity.user.top_level_items()"><a href="/item/${item.id}/">${item.title}</a></li>
    </ul>
  </div>
  <!-- End of getting_started -->
</div>
<div id="main_content" py:if="tg.identity.anonymous">
<p>you must <a href="/login">login</a>. If you don't have an account,
  you can <a href="/signup_form">sign up</a>.</p>
</div>
</body>
</html>
