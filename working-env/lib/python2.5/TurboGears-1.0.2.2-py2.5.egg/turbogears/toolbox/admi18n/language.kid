<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >

<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>admi18n :: ${language} ${code} </title>
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
                &#x00BB; <a href="language_management">Languages</a> 
                &#x00BB; ${language} (${code})
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

    <table width="100%" cellpadding="3" cellspacing="1" border="0" class="grid">
        <tr class="even">
            <td> Path </td>
            <td> ${po_message_file['path']}</td>
        </tr>
        <tr class="odd">
            <td> Modified</td>
            <td> ${po_message_file['modified']}</td>
        </tr>
        <tr class="even">
            <td> Size </td>
            <td> ${po_message_file['size']} Bytes</td>
        </tr>
        <tr class="odd">
            <td>Upload</td>
            <td>
                <form method="post" action="po_upload" enctype="multipart/form-data">
                    <input type="hidden" name="code" value="${code}" />
                    <input type="file" name="myFile" /><input type="submit" value="Upload" />
                </form>
            </td>
        </tr>
        <tr class="even">
            <td colspan="2">
                <input type="button"
                    onclick="document.location.href='lang_file?code=${code}'"
                    value="Download message file"
                />
            </td>
        </tr>

    </table>

    <br />
    <?python
      google_langs = {'en':'English',
                      'it':'Italian',
                      'es':'Spanish',
                      'pt':'Portuguese',
                      'fr':'French',
                      'de':'German',
                      'zh':'Chinese',
                      'ja':'Japanese',
                      'ko':'Korean'}
    ?>
    <div py:if="code in google_langs.keys()">
        <a  href="javascript:im_feeling_lucky()"
            style="text-decoration:none"
            class="action"
            title="Get help from Google translating your strings"><img
            name="feeling_lucky"
            id="feeling_lucky"
            src="/tg_static/images/arrow_right.png" border="0" 
            alt="" /> I'm feeling lucky</a>
        <span id="feeling_lucky_settings"
            style="display:none;border-top:1px solid #e3e3e3;width:80%;margin-left:20px;background-color:#f0f0f0;padding:10px;">
            Query the Google translation service to translate from
            <select id="translate_from" style="margin-left:5px;margin-right:5px;">
                <option value="en">English</option>
                <option py:for="lang in google_langs"
                    py:if="lang != 'en' and lang != code"
                    py:content="google_langs[lang]"
                    py:attrs="dict(value=lang)"
                />
            </select>

            to ${google_langs[code]}

            <br />
            <input type="button" value="Translate Selected"
                onclick="google_translate()"
                style="margin-top:10px" />
        </span>
    </div>
    <br />

    <script type="text/javascript">
        <![CDATA[
            function google_translate()
            {
                var g_from = document.getElementById('translate_from');
                g_from = g_from.options[g_from.selectedIndex].value;
                window.frames['po_view'].google_translate(g_from,'${code}');
            }
            function im_feeling_lucky()
            {
                var img = document.getElementById('feeling_lucky');
                var isOpen = (img.src.indexOf('arrow_right.png') ==-1 )? true:false;
                if(isOpen)
                {
                    img.src = '/tg_static/images/arrow_right.png';
                    document.getElementById('feeling_lucky_settings').style.display='none';
                    //remove the checkboxes in front of the id strings
                    window.frames['po_view'].hide_checkboxes();
                }
                else
                {
                    img.src = '/tg_static/images/arrow_down.png';
                    document.getElementById('feeling_lucky_settings').style.display='block';
                    //add checkbox in front of the id strings
                    window.frames['po_view'].display_checkboxes();
                }
            }
            function sort_catalog(by_item)
            {
                var img = document.getElementById('message_'+ by_item);
                var new_img = '/tg_static/images/arrow_up_small.png';
                var direction = 'up';
                if(img.src.indexOf('transp.png') !=-1 || img.src.indexOf('arrow_up_small.png') !=-1 )
                {
                    new_img = '/tg_static/images/arrow_down_small.png';
                    direction = 'down';
                }
                var elements= document.getElementsByTagName('IMG');
                for(var i=0;i < elements.length;i++)
                {
                    var element =elements[i];
                    if(element.className !='sorter') continue;
                    element.src='/tg_static/images/transp.png';
                }
                img.src=new_img;
                po_view.location.href='po_view?code=${code}&sort_by='+ by_item +'&dir='+ direction;
            }
        ]]>
    </script>

    <table width="100%" cellpadding="3" cellspacing="1" border="0" class="grid">
        <thead style="cursor:pointer">
            <tr>
                <th width="150" onclick="sort_catalog('id')">
                    <img src="/tg_static/images/transp.png" width="10" height="10" id="message_id" class="sorter" alt="" />
                    Message id
                </th>
                <th onclick="sort_catalog('string')">
                    <img src="/tg_static/images/transp.png" width="10" height="10" id="message_string" class="sorter" alt="" />
                    Message string
                </th>
                <th width="150" onclick="sort_catalog('context')">
                    <img src="/tg_static/images/transp.png" width="10" height="10" id="message_context" class="sorter" alt="" />
                    Context
                </th>
            </tr>
        </thead>
    </table>
    <iframe src="po_view?code=${code}"
        name="po_view"
        id="po_view"
        marginwidth="0"
        marginheight="0"
        frameborder="0"
        style="width:100%;height:500px">
    </iframe>

    </td>
    </tr>
    </table>

</body>
</html>

