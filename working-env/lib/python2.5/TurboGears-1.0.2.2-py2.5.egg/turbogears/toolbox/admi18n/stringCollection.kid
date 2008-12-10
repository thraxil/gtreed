<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>admi18n :: String Collection</title>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/toolbox.css"></link>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/widget.css"></link>
    <script type="text/javascript" src="/tg_js/MochiKit.js"></script>
    <style type="text/css">
        code { color:#999; }
        .odd{background-color:#edf3fe}
        .even{background-color:#fff}
    </style>
</head>

<body>
    <div id="top_background">
        <div id="top">
            <h1>
                <a href="/">Toolbox</a> &#x00BB; <a href="index">Admi18n</a> 
                &#x00BB; String Collection
            </h1>
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


    <h3>String Collection</h3>
    <div py:if="pot_message_file" id="current_pot_file">

        <table width="100%" cellpadding="3" cellspacing="1" border="0" class="grid">
            <tr class="even">
                <td> Name    </td>
                <td><a class="action" href="lang_file?code=pot">${pot_message_file['name']}</a></td>
            </tr>
            <tr class="odd">
                <td> Path </td>
                <td> ${pot_message_file['path']}</td>
            </tr>
            <tr class="even">
                <td> Modified</td>
                <td> ${pot_message_file['modified']}</td>
            </tr>
            <tr class="odd">
                <td> Size </td>
                <td> ${pot_message_file['size']} Bytes</td>
            </tr>
            <tr class="even">
                <td colspan="2">
                    <input type="button"
                        onclick="document.location.href='lang_file?code=pot'"
                        value="Download message file"
                    />
                </td>
            </tr>
        </table>

    </div>
    <p>
        Select from this overview the files you want to collect strings from:
    </p>
    <div id="file_manager">
        <script type="text/javascript">
        <![CDATA[
            function toggleSelection(checkbox_item)
            {
                var sel = checkbox_item.className.split('_#x#_');
                var selectedLevel = sel[0];
                var selectedPath = sel[1]

                var elements = document.getElementsByTagName('INPUT');
                for(var i=0;i < elements.length;i++)
                {
                    var element =elements[i];
                    if(element.type!='checkbox') continue;
                    var name = element.className;
                    var cur = name.split('_#x#_');
                    if(cur.length < 2) continue;
                    var level = cur[0];
                    var path = cur[1];
                    if(level <= selectedLevel) continue;
                    if(path.indexOf(selectedPath) !=0) continue;
                    element.checked = checkbox_item.checked;
                }
            }
        ]]>
        </script>

        <form method="post" action="">
            <table width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr py:for="idx,file in enumerate(project_files)" class="${idx%2 and 'odd' or 'even'}">
                    <td>
                        <table cellpadding="0" cellspacing="0" border="0">
                            <tr>
                                <td>
                                    <img src="/tg_static/images/transp.png"
                                        width="${file['level']*20}" height="1" alt="" />
                                </td>
                                <td>
                                    <input type="checkbox"
                                        onclick="toggleSelection(this)"
                                        checked="checked"
                                        name="files"
                                        value="${file['path']}"
                                        class="${file['level']}_#x#_${file['path']}"
                                    />
                                </td>
                                <td>
                                    <img src="/tg_static/images/folder.png" py:if="file['isdir']" alt="" />
                                    <img src="/tg_static/images/file.png" py:if="not file['isdir']" alt="" />
                                    ${file['file_name']}
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>

            <br />
            <input type="submit" value="Collect strings and generate a .pot file" />
        </form>

    </div>
    </td>
    </tr>
    </table>
</body>
</html>
