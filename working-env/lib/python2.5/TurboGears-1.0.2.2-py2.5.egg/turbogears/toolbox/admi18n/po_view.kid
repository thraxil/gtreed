<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#" >
<head>
    <meta content="text/html; charset=UTF-8" http-equiv="content-type" py:replace="''"/>
    <link type="text/css" rel="stylesheet" href="/tg_static/css/widget.css"></link>
    <script type="text/javascript" src="/tg_js/MochiKit.js"></script>
    <title>po_view</title>
    <style type="text/css">
        <![CDATA[
            .edit_field {width:100%;
                         height:200px;
                         font-size:11px;
                         font-family:verdana,sans-serif;}
        ]]>
    </style>
    <script type="text/javascript">
        <![CDATA[
        var editing=false;
        var edit_text =''
        function cancel_edit()
        {
           if(!editing) return;
           var el = document.getElementById('msg_'+ editing);
           el.innerHTML = edit_text;
           editing = false;
           edit_text ='';
        }

        function save_edit()
        {
           var el = document.getElementById('msg_'+ editing);
           var content =document.getElementById('text_'+ editing).value;
           el.innerHTML = content;
           var msg_id = document.getElementById('msg_id_'+ editing).innerHTML;

           var postVars = 'code=${code}';
           postVars+= '&msg_id='+ encodeURIComponent(msg_id);
           postVars+= '&msg_text='+ encodeURIComponent(content);

           var req = getXMLHttpRequest();
           req.open('POST','update_catalog',true);
           req.setRequestHeader('Content-type','application/x-www-form-urlencoded');
           var d = sendXMLHttpRequest(req,postVars);
           d.addCallback(evalJSONRequest);

           //save edit
           editing = false;
           edit_text ='';
        }
        function edit_message(idx)
        {
           if(editing == idx) return;
           cancel_edit();

           var el = document.getElementById('msg_'+ idx);
           var content = el.innerHTML;
           var txt = DIV(null,
                         createDOM('TEXTAREA',
                                   {'id':'text_'+ idx, 'class':'edit_field' },content),
                         createDOM('BR',null),
                         DIV({'style':'text-align:right'},
                             A({'href':'javascript:cancel_edit()',
                                'title':'Cancel'},
                                IMG({'border':'0','src':'/tg_static/images/discard.png'})
                              ),'  ',
                             A({'href':'javascript:save_edit()',
                                'title':'Save'},
                                IMG({'border':'0','src':'/tg_static/images/save.png'})
                              )
                          )
                        );
           replaceChildNodes(el,txt);
           el = document.getElementById('text_'+ idx);
           el.select();
           el.focus();
           editing = idx;
           edit_text = content;
        }
        function google_translate(from_lang,to_lang)
        {
            var cks = getElementsByTagAndClassName('INPUT','google_check');
            for(var i=0;i< cks.length;i++)
            {
                if(!cks[i].checked) continue;
                var n = cks[i].id;
                var idx = n.replace('check_','');
                var el = document.getElementById('msg_id_'+ idx);
                var txt = createDOM('TEXTAREA',{'name':'text_'+ idx,'style':'border:none'},el.innerHTML)
                replaceChildNodes(el,txt);
            }
            document.myform.from_lang.value = from_lang;
            document.myform.to_lang.value = to_lang;
            document.myform.submit();
        }
        function display_checkboxes()
        {
            var cks = getElementsByTagAndClassName('INPUT','google_check');
            for(var i=0;i< cks.length;i++)
            {
                cks[i].style.display='block';
                cks[i].parentNode.style.width='10px';
            }
        }
        function hide_checkboxes()
        {
            var cks = getElementsByTagAndClassName('INPUT','google_check');
            for(var i=0;i< cks.length;i++)
            {
                cks[i].style.display='none';
                cks[i].parentNode.style.width='0px';
            }
        }
        ]]>
    </script>
</head>

<body style="margin:0;padding:0">
    <form method="post" name="myform" action="">
        <input type="hidden" name="from_lang" value="" />
        <input type="hidden" name="to_lang" value="" />

        <table width="100%" cellpadding="3" cellspacing="1" border="0" class="grid" style="margin:0;padding:0">
            <tr py:for="idx,message in enumerate(catalog)"
                style="cursor:pointer"
                class="${idx%2 and 'odd' or 'even'}">
                <td valign="top" width="5" style="width:5px" id="check_cell_${idx + 1}">
                    <input type="checkbox" value="msg_id_${idx +1}" name="check_${idx + 1}"
                        id="check_${idx + 1}" class="google_check"
                        style="display:${('none','block')[visible_checkbox]}" checked="checked" />
                </td>
                <td width="150" valign="top"
                    onclick="edit_message('${idx + 1}')"
                    id="msg_id_${idx + 1}">${message['id']}
                </td>
                <td id="msg_${idx + 1}"
                    onclick="edit_message('${idx + 1}')"
                    valign="top">${message['message']}
                </td>
                <td width="150"
                    onclick="edit_message('${idx + 1}')"
                    valign="top">
                    ${message['file']}:${message['line']}
                </td>
            </tr>
        </table>
    </form>
</body>
</html>
