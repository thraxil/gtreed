<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#">
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>admi18n :: intro</title>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css"></link>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/widget.css"></link>
    <script type="text/javascript" src="/tg_js/MochiKit.js"></script>
    <style type="text/css">
        code { color:#888; }
        .odd{background-color:#edf3fe}
        .even{background-color:#fff}
    </style>
</head>

<body>
    <div id="top_background">
        <div id="top">
            <h1><a href="/">Toolbox</a> &#x00BB; Admi18n</h1>
        </div>
    </div>

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
                <img src="/tg_static/images/transp.png" width="228" height="1" alt="" />
            </td>
            <td valign="top" id="main_content">


    <div style="width:550px">
    <h3>Welcome to admi18n</h3>
    <p>
        To internationalize your application, you have to:
    </p>
    <h4>Prepare your strings</h4>
        Mark text strings in your code using the _() function, like this
        <pre>
        <code>
        greetings = _('hello world')
        </code>
        </pre>
        You don't need to do this for text inside tags in your kid template files.
        Tagged text will be automatically collected:
        <pre>
        <code>
        &lt;strong&gt;hello world&lt;/strong&gt;
        </code>
        </pre>
        Text inside tag properties still needs to be wrapped in a function:
        <pre>
        <code>
        &lt;img src="$${_('uk_flag.gif')}" /&gt;
        </code>
        </pre>
        Date or number strings should be formatted using the turbogears.i18n formatting functions.

    <h4>Collect your strings</h4>
    <p>
        Select which files from within your project you wish to collect strings from.
        By default al python and kid files are selected
        The collected string will be saved in a '.pot' file, inside a 'locales' directory whithin your project
    </p>

    <h4>Add locales - Manage your languages</h4>
    <p>
        Choose a language you want your application localized to.
        Send your language file to a translator or edit the file directly from within the application
        Sort your messages by id, message text or context
    </p>

    <h4>Compile your catalog</h4>
    <p>Compile your message files to a machine efficient .mo file</p>

    <h4>Keep your catalog up to date</h4>
    <p>
        If you later add more strings to your source files or kid templates, collect the strings again
        and in the language management page, choose your catalogs and run 'Merge collected strings'.
        This will merge the new strings into your selected catalogs.
        Once you translate the new strings, recompile your catalog
    </p>

    <h4>And finally..</h4>
        If you want your templates to be automatically translated, add the i18n template filter to your configuration file
        <pre>
        <code>
        i18n.run_template_filter = True
        </code>
        </pre>
        You let your users change the locale of a running application by updating their session:
        <pre>
        <code>
        turbogears.i18n.set_session_locale(lang)
        </code>
        </pre>
        Of course the sessions filter should be active for this to work.
        <pre>
        <code>
        session_filter.on = True
        </code>
        </pre>
    </div>

    <h4>See also</h4>
     <p><em>tg-admin i18n</em> command provides mostly the same functionality as admi18n only via command-line interface.</p>
            </td>
        </tr>
    </table>
</body>
</html>
