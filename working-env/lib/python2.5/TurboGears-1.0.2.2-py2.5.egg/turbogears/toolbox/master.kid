<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">

<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css" />
    <link py:strip="1" py:for="css in tg_css">${css.display()}</link>
    <link py:strip="1" py:for="js in tg_js_head">${js.display()}</link>
    <meta py:replace="item[:]"/>
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'">
    <div py:strip="1" py:for="js in tg_js_bodytop">${js.display()}</div>
    <table id="top" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td id="logo">
                <a href="/" border="0"><img src="/tg_static/images/toolbox_logo.png" border="0"/></a>
            </td>
            <td valign="bottom"><img src="/tg_static/images/toolbox_top_vertical_line.png" border="0"/></td>
        </tr>
    </table>

    <div py:if="tg_flash" class="flash" py:content="tg_flash"></div>

    <div py:replace="[item.text]+item[:]"/>

    <div py:strip="1" py:for="js in tg_js_bodybottom">${js.display()}</div>
</body>
</html>
