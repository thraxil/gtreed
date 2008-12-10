<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" />
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css" />
    <link py:strip="1" py:for="css in widget_css">${css.display()}</link>
    <script type="text/javascript">
        <![CDATA[
        var tabberOptions = {
            'onClick': function(argsObj){
                var t = argsObj.tabber;
                var id = t.id;
                if (typeof(id) == 'string' && id.indexOf('wb_tabber_') == 0) {
                    var code = 'code_' + id.substring(10,id.length);
                    dp.SyntaxHighlighter.HighlightAll(code);
                    t.onClick = null;
                }
            }
        };
        ]]>
    </script>
    <link py:strip="1" py:for="js in widget_js_head">${js.display()}</link>
    <title>TurboGears Widget Browser</title>
    <style type="text/css">
        .widgetname {font-weight:900;color:#333;}
        .sample { background-color:#FFFFDD;padding:15px;border:1px solid #C6977C; }
        .description { width:500px;font-size:10px;color:#666;padding:0;margin:0; }
        .rendered { display:block;background:#f7f7f7;border:1px solid #d7d7d7;padding:10px; }
    </style>
</head>

<body>
    <div id="top_background">
        <div id="top">
            <h1>
                <a href="/">Toolbox</a> &#x00BB; 
                <a href="index" py:strip="not viewing_one">Widget Browser</a>
                <span py:if="viewing_one" py:strip="1">&#x00BB; ${descs[0].name}</span>
            </h1>
        </div>
    </div>

    <div py:strip="1" py:for="js in widget_js_bodytop">${js.display()}</div>

    <center>
    <div id="main_content" style="width:500px">

        <div py:for="widgetdesc in descs">
            <h3 py:content="widgetdesc.name" />
            <div class="widgetclass" py:content="widgetdesc.full_class_name" />
            <div class="tabber" id="wb_tabber_${widgetdesc.full_class_name}">
                <div class="tabbertab">
                    <h2>Sample</h2>
                    <div class="sample" py:if="not widgetdesc.show_separately or viewing_one">
                        ${widgetdesc.display()}
                    </div>
                    <div class="sample" py:if="widgetdesc.show_separately and not viewing_one">
                        <p>This widget can only be <a href="${tg.url('.', name=widgetdesc.full_class_name.replace('.', '_'))}">viewed separately</a></p>
                    </div>
                </div>
                <div class="tabbertab" py:if="widgetdesc.description">
                    <h2>Description</h2>
                    <pre py:content="widgetdesc.description" />
                </div>
                <div class="tabbertab">
                    <h2>Source Code</h2>
                    <textarea name="code_${widgetdesc.full_class_name}" class="py" py:content="widgetdesc.source" />
                </div>
                <div class="tabbertab" py:if="widgetdesc.for_widget.params">
                    <h2>Parameters</h2>
                    <dl class="param_list">
                        <span py:strip="True" py:for="param_name in widgetdesc.for_widget.params">
                            <dd py:content="param_name" />
                            <dt py:content="widgetdesc.for_widget.params_doc.get(param_name, 'No doc available')" />
                        </span>
                    </dl>
                </div>
                <div py:if="widgetdesc.for_widget.template" class="tabbertab">
                    <h2>Template</h2>
                    <textarea name="code_${widgetdesc.full_class_name}" class="xml" py:content="widgetdesc.for_widget.template" />
                </div>
            </div>
            <br />
        </div>

    </div>
    </center>
    <div py:strip="1" py:for="js in widget_js_bodybottom">${js.display()}</div>
</body>
</html>
