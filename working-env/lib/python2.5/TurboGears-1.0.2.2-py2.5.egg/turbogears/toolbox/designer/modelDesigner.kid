<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>ModelDesigner</title>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css" />
    <script type="text/javascript" src="/tg_static/js/tool-man/core.js"></script>
    <script type="text/javascript" src="/tg_static/js/tool-man/events.js"></script>
    <script type="text/javascript" src="/tg_static/js/tool-man/css.js"></script>
    <script type="text/javascript" src="/tg_static/js/tool-man/coordinates.js"></script>
    <script type="text/javascript" src="/tg_static/js/tool-man/drag.js"></script>
    <script type="text/javascript" src="/tg_static/js/tool-man/dragsort.js"></script>
    <script type="text/javascript" src="/tg_static/js/MochiKit.js"></script>

    <script type="text/javascript" src="/tg_toolbox/designer/javascript/modelDesigner.js"></script>
    <link type="text/css" rel="stylesheet" href="/tg_toolbox/designer/css/style.css" />
    <link type="text/css" rel="stylesheet" href="/tg_widgets/turbogears.widgets/sh/SyntaxHighlighter.css" />
</head>

<body>
    <div id="top_background">
        <div id="top">
            <h1><a href="/">Toolbox</a> &#x00BB; ModelDesigner</h1>
        </div>
    </div>

    <form name="myform" action="">
        <input type="hidden" name="model_exists" py:attrs="{'value':model_exists}" />
        <input type="hidden" name="model_name" py:attrs="{'value':model_name}" />
    </form>

    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td id="left_col" valign="top">
                <img src="/tg_static/images/transp.png" width="228" height="1" alt="" />
                <div class="container">

                    <table cellpadding="0" cellspacing="0" border="0">
                        <tr>
                            <td>
                                <select id="sample_models" style="font-size:10px">
                                    <option value="none">Sample models</option>
                                    <option py:if="session_file_exists" selected="selected"
                                        value="model_designer_session_file">Existing Designer Session</option>

                                    <option py:for="session in session_list"
                                        py:content="session"
                                        py:attrs="dict(value=session)"
                                    />
                                </select>
                            </td>
                            <td>
                                <button onclick="designer.loadSampleModel()" 
                                    style="font-size:10px;text-align:center;width:40px">Load</button>
                            </td>
                        </tr>
                    </table>
                    <br />

                    <!--<button onclick="designer.retrieveCurrentModel()" >Load current model</button>
                    -->
                    <button onclick="designer.saveCurrentSession()" >Save Current Session</button>
                    <br />
                    <button onclick="blankSlate()" >Clear Current Session</button>
                    <br />
                    <button onclick="designer.loadModelSettings()" id="add_model"
                        accesskey="m"
                        title="Create a new class (m)"
                        >Add new class <u>M</u></button>

                    <div id="models"></div>
                </div>
            </td>
            <td id="main_content">
                <table id="tab" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                        <td><a href="javascript:designer.settingsView()" accesskey="t">Se<u>t</u>tings</a> </td>
                        <td><a accesskey="g" href="javascript:designer.codeView()"><u>G</u>enerate Code</a> </td>
                        <td><a href="javascript:designer.diagramView()" accesskey="d"><u>D</u>iagram</a> </td>
                    </tr>
                </table>
                <iframe name="diagram" id="diagram" src="about:blank" style="display:none"></iframe>
                <div id="canvas"></div>

            </td>
        </tr>
    </table>

    <script type="text/javascript" src="/tg_widgets/turbogears.widgets/sh/shCore.js"></script>
    <script type="text/javascript" src="/tg_widgets/turbogears.widgets/sh/shBrushPython.js"></script>
    <script type="text/javascript" src="/tg_widgets/turbogears.widgets/sh/shBrushXml.js"></script>

    <script type="text/javascript">
        var dragsort = ToolMan.dragsort()
        var junkdrawer = ToolMan.junkdrawer()
    </script>
</body>
</html>
