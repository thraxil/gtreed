<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >

<head py:match="item.tag=='{http://www.w3.org/1999/xhtml}head'">
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title py:replace="''">Your title goes here</title>
    <link py:strip="1" py:for="css in tg_css">${css.display()}</link>
    <link py:strip="1" py:for="js in tg_js_head">${js.display()}</link>
    <meta py:replace="item[:]"/>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css"></link>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/widget.css"></link>
    <script type="text/javascript" src="/tg_js/MochiKit.js"></script>
    <style>
        .odd{background-color:#edf3fe}
        .even{background-color:#fff}
    </style>
</head>

<body py:match="item.tag=='{http://www.w3.org/1999/xhtml}body'">
    <div id="top_background">
        <div id="top">
            <h1><a href="/">Toolbox</a> &#x00BB; ModelDesigner</h1>
        </div>
    </div>
    <div py:strip="1" py:for="js in tg_js_bodytop">${js.display()}</div>
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td valign="top"  id="left_col" width="229" style="width:229px">
                <ul>
                    <li>
                        <a href="index">Introduction</a>
                    </li>
                    <li>
                        <a href="string_collection">Collect your strings</a>
                    </li>
                    <li>
                        <a href="language_management">Manage your languages</a>
                    </li>
                </ul>
                <img src="/tg_static/images/transp.png" width="228" height="1" />
            </td>
            <td valign="top" id="main_content">

                <div py:replace="[item.text]+item[:]"/>

            </td>
        </tr>
    </table>
    <br /><br />
    <br /><br />
    <div py:strip="1" py:for="js in tg_js_bodybottom">${js.display()}</div>
</body>
</html>
