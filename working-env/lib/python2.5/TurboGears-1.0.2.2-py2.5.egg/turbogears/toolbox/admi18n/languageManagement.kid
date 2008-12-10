<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <title>admi18n :: Manage your language files</title>
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
    <script type="text/javascript">
    <![CDATA[
        function add_locale()
        {
            var v = document.getElementById('lang_code').value;
            if(v=='')
            {
                alert('You haven\'t selected a language');
                return;
            }
            document.location.href='language_management?add='+ v;
        }
        function load_language_list()
        {
            replaceChildNodes('new_locale_settings',SPAN(null,'[...loading...]'));
            var d = loadJSONDoc('language_list');
            d.addCallback(render_language_list);
        }
        function lang_selected(list)
        {
            var v = list.options[list.selectedIndex].value;
            document.getElementById('lang_code').value = v;
        }
        function render_language_list(results)
        {
            var selectBox = createDOM('SELECT',{'id':'language_code',
                                                'onchange':'lang_selected(this)',
                                                'name':'language_code'});
            for(var i=0;i<results['languages'].length;i++)
            {
                var lang = results['languages'][i];
                selectBox.appendChild(createDOM('OPTION',{'value':lang[0]},lang[0] +' '+ lang[1]));
            }
            replaceChildNodes('new_locale_settings',selectBox);
        }
        
        function removing(code)
        {
            if(!confirm('Are you sure you want to remove the locale '+ code +'?')) return;
            document.location.href='language_management?rem='+ code
        }
        function toggleAll(cb)
        {
            var elements = document.getElementsByTagName('INPUT');
            for(var i=0;i < elements.length;i++)
            {
                var element =elements[i];
                if(element.type!='checkbox') continue;
                if(element.name=='master') continue;
                element.checked = cb.checked;
            }
        }
        function get_selected_language_codes()
        {
            var catalog_list =[];
            var elements = document.getElementsByTagName('INPUT');
            for(var i=0;i < elements.length;i++)
            {
                var element =elements[i];
                if(element.type!='checkbox') continue;
                if(element.name=='master') continue;
                if(element.checked) catalog_list[catalog_list.length]=element.id;
            }
            if(catalog_list.length==0)
            {
                alert('You haven\'t selected any catalog');
                return;
            }
            var codes = '';
            for(var i=0;i<catalog_list.length;i++)
            {
                if(codes !='') codes+=',';
                codes+=catalog_list[i];
            }
            return codes;
        }
        function merge_catalogs()
        {
            var codes = get_selected_language_codes();
            if(!codes) return;
            document.location.href='language_management?merge='+ codes;
        }
        function compile_catalogs()
        {
            var codes = get_selected_language_codes();
            if(!codes) return;
            document.location.href='language_management?compile='+ codes;
        }
    ]]>
    </script>

    <div id="top_background">
        <div id="top">
            <h1><a href="/">Toolbox</a> &#x00BB; <a href="index">Admi18n</a> 
                &#x00BB; Languages
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
                <img src="/tg_static/images/transp.png" width="228" height="1" alt=""/>
            </td>
            <td valign="top" id="main_content">

    <h3>Manage your language files</h3>

    <p>
        Add a new language catalog <span py:if="locales">or edit the existing ones</span>
    </p>
    <br />

    <div class="infobox">
        <h5>Add a new locale</h5>
        <div>
            Language code
            <span id="new_locale_settings">
                <a href="javascript:load_language_list()" 
                    style="text-decoration:none;color:#999;font-size:10px">
                    [select from a list]</a>
            </span>:
            <input type="text" size="2" id="lang_code" name="lang_code" />
            <input type="button" value="Add New" onclick="add_locale()" />
        </div>
    </div>
    <br />


    <div id="add_locale">

        <table id="locale_overview" cellpadding="5" cellspacing="1" border="0" class="grid">
            <thead>
                <tr>
                    <th>
                        <span py:if="locales">
                            <input type="checkbox" name="master" onclick="toggleAll(this)" />
                        </span>
                    </th>
                    <th>Code</th>
                    <th>Language</th>
                    <th>Modified</th>
                    <th>Compiled</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                <tr py:if="not locales">
                    <td colspan="5" align="center" style="padding:10px;font-size:10px">No locales available for this project</td>
                </tr>
                <tr py:for="idx,locale in enumerate(locales)" class="${idx%2 and 'odd' or 'even'}">
                    <td>
                        <input type="checkbox" checked="checked" id="${locale['code']}" name="${locale['code']}" />
                    </td>
                    <td>
                        ${locale['code']}
                    </td>
                    <td>
                        ${locale['language']}
                    </td>
                    <td>
                        ${locale['modified']}
                    </td>
                    <td>
                        ${locale['compiled']}
                    </td>
                    <td>
                        <a href="language?code=${locale['code']}"
                            title="Edit Catalog"><img src="/tg_static/images/edit.png" border="0" alt="" /></a>
                        <a href="javascript:removing('${locale['code']}')"
                            title="Remove Catalog"><img src="/tg_static/images/remove.png" border="0" alt="" /></a>
                    </td>
                </tr>
            </tbody>
            <tr py:if="1==2">
                <td colspan="6" align="right">

                    <select id="locale" name="locale_by_language">
                        <option value="">Choose new language</option>
                        <option py:for="lang_code,lang_name in languages"
                            py:content="'%s  %s'% (lang_code,lang_name)"
                            py:attrs="dict(value=lang_code,title=lang_code)"
                        />
                    </select>
                    <input type="button" onclick="add_locale()" value="Add Locale" />
                </td>
            </tr>
        </table>

        <div py:if="locales">
            <br />
            <input type="button"
                onclick="compile_catalogs()"
                value="Compile selected locales to .mo files"  style="width:300px" />
            <br />
            <input type="button"
                onclick="merge_catalogs()"
                value="Merge strings with selected locales"  style="width:300px" />
        </div>
    </div>
    </td>
    </tr>
    </table>
</body>
</html>
