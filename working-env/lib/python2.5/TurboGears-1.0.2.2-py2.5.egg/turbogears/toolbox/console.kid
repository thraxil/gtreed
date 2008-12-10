<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >
<head>
    <title>Interpreter</title>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/interpreter.css" />
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css" />
    <script type="text/javascript" src="${tg.tg_js}/MochiKit.js"></script>
    <script type="text/javascript" src="/tg_static/js/interpreter.js"></script>
</head>
<body>
    <div id="top_background">
        <div id="top">
            <h1 style="text-align:left"><a href="/">Toolbox</a> &#x00BB; WebConsole</h1>
        </div>
    </div>

    <center>
        <div id="main_content">
            <form id="interpreter_form" action="">
                <div id="interpreter_area">
                    <div id="interpreter_output"></div>
                </div>
                <div id="prompt" class="code">>>> </div><input id="interpreter_text" name="input_text"
                    type="text" class="textbox" size="96" style="width:580px" />
                <br/>
                <h3>Multiline (code-block) Input:</h3>
                <textarea name="interpreter_block_text" 
                    id="interpreter_block_text" style="width:610px;height:170px" 
                    class="textbox"></textarea>
                <br />
                <input type="button" name="exec" id="exec" value="Execute" />
            </form>
        </div>
    </center>
</body>
</html>
