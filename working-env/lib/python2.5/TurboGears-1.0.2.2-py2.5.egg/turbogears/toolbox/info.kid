<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" />
    <link href="/tg_static/css/toolbox.css" type="text/css" rel="stylesheet"/>
    <title>TurboGears Toolbox</title>
    <style type="text/css">
        li { margin-bottom:2px}
    </style>
</head>

<body>
    <div id="top_background">
        <div id="top">
            <h1><a href="/">Toolbox</a> &#x00BB; Info</h1>
        </div>
    </div>

    <div style="margin-left:30px">
        <h2>TurboGears Version Info</h2>
        <ul>
            <li py:for="package in packages">
                ${package}
            </li>
        </ul>
        <h2>Installed Plugins</h2>
        <div py:for="name, pluginlist in plugins.items()">
            <h3>${name}</h3>
            <ul>
                <li py:for="plugin in pluginlist">${plugin}</li>
            </ul>
        </div>
    </div>

</body>
</html>
