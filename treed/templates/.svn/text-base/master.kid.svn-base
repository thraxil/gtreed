<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python import sitetemplate ?>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" py:extends="sitetemplate">

<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'" py:attrs="item.items()">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <meta py:replace="item[:]"/>
    <style type="text/css">
        #pageLogin
        {
            font-size: 10px;
            font-family: verdana;
            text-align: right;
        }
    </style>
    <style type="text/css" media="screen">
      @import "/static/css/style.css";
    </style>
    <script type="text/javascript" src="/static/javascript/subitems.js"></script>
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'" py:attrs="item.items()">
    <div py:replace="[item.text]+item[:]"/>
	<!-- End of main_content -->
</body>


<div py:def="flash" py:if="tg_flash" class="flash" py:content="tg_flash"></div>
<div py:def="welcome" py:if="tg.config('identity.on',False) and not 'logging_in' in locals()"
        id="pageLogin">
        <span py:if="tg.identity.anonymous">
            <a href="/login">Login</a>
        </span>
        <span py:if="not tg.identity.anonymous">
            Welcome ${tg.identity.user.display_name}.
            <a href="/logout">Logout</a>
        </span>
    </div>

<div py:def="sidebar" id="sidebar">
${welcome()}
<form action="/search" method="get"><p><input type="text" name="q"
					      value=""
					      /><input type="submit"
					      value="search" /></p></form>

  <ul class="links" py:if="not tg.identity.anonymous">
    <li py:for="menuitem in tg.identity.user.top_level_items()" id="sidebar-li-${menuitem.id}">

<img py:if="len(menuitem.get_open_children()) == 0" src="/static/images/blank.png"
     width="10" height="10" alt="" border="0" class="turnbuckle"/>
<a py:if="len(menuitem.get_open_children()) > 0"
   href=""
   title="show/hide children"
   onclick="showSubitems(${menuitem.id},true);return false"
   ><img src="/static/images/arrow_right.png" 
	 width="10" height="10" alt="&gt;"
	 border="0" class="turnbuckle"/></a>

<a
    href="/item/${menuitem.id}/">${menuitem.title}</a>
<span class="list-controls" py:if="item">
[<a href="/item/${menuitem.id}/reparent?item_id=${item.id}"
    onclick="reparent(${menuitem.id}); return false;">&gt;</a>
<a href="/item/${menuitem.id}/add_child?item_id=${item.id}"
   onclick="addChild(${menuitem.id}); return false;">&gt;&gt;</a>]
</span>

<ul class="subitems invisible" id="sidebar-subitems-${menuitem.id}"/>
      
</li>
  </ul>

</div>

</html>
