<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" />
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css" />
    <title>TurboGears Toolbox</title>
</head>

<body>
    <div id="top_background">
        <div id="top">
            <h1>Toolbox</h1>
        </div>
    </div>
    
    <center>
    <div id="main_content">
        <h2>Welcome to the TurboGears ToolBox </h2>
        <p>
            A collection of web based tools for TurboGears applications.
        </p>
        <p py:if="not project" style="color:red">
        Note: Some functions are not available as the toolbox was not started in a valid TurboGears project directory.
        </p>

        <table id="tools" cellpadding="8" cellspacing="0" border="0">
            <tr py:for="toolpair in toolbox">
                <td py:for="tool in toolpair" width="50%">
                    <table py:if="tool" cellpadding="6" cellspacing="0">
                        <tr >
                            <td valign="top">
                                <a py:strip="tool['disabled']" href="${tool['path']}/"><img hspace="4" align="left" src="${tool['icon']}" alt="" border="0" /></a>
                            </td>
                            <td valign="top" py:attrs="class=tool['disabled']">
                                <h4><a py:strip="tool['disabled']" href="${tool['path']}/">${tool['label']}</a></h4>
                                ${tool['description']}
                            </td>
                        </tr>
                    </table>
                </td>
           </tr>
        </table>
    </div>
    </center>

</body>
</html>
