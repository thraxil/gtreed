var req;
var current_item_id;
var sidebar = false; // whether the submenu being built is in the sidebar
var showing = new Array();

function toggleVisible(elem) {
        toggleElementClass("invisible", elem);
    }

    function makeVisible(elem) {
        removeElementClass(elem, "invisible");
    }

    function makeInvisible(elem) {
        addElementClass(elem, "invisible");
    }

    function isVisible(elem) {
        // you may also want to check for
        // getElement(elem).style.display == "none"
        return !hasElementClass(elem, "invisible");
    };

function toggleNextActionForm(id) {
   var form = $('na-' + id);
   toggleVisible(form);
}

function turnBuckle(id,children) {
   if (children > 0) {
      var oc = "showSubitems(" + id + "," + sidebar + ");return false;";

      var a = A({"title" : "hide/show children", "href" : "",
	 "onclick" : oc }, 
		IMG({"src" : "/static/images/arrow_right.png",
		      "width" : "10", "height" : "10", "alt" : ">", 
		      "border" : "0", "class" : "turnbuckle"}));
      return a;
   } else {
      return IMG({"src" : "/static/images/blank.png",
	    "width" : "10", "height" : "10", "alt" : "", 
	    "border" : "0", "class" : "turnbuckle"});
   }
}

function addSubItemButton(id) {
   return A({"href" : "add", "title" : "add sub item",
      "onclick" : "toggleNextActionForm(" + id + "); return false"},
	    "+");
}

function actions(id) {
   if (sidebar) {
      if (ITEM_ID) {
	 return SPAN({"class" : "list-controls"}, " [", 
		     A({'href' : "/item/" + id + "/reparent?item_id=" + ITEM_ID,
		     "onclick" : "reparent(" + id + "); return false;"},">"),
		     " ",
		     A({'href' : "/item/" + id + "/add_child?item_id=" + ITEM_ID,
		     "onclick" : "addChild(" + id + "); return false;"},">>"),
		     "] ");
      } else {
	 return SPAN();
      }
   } else {
      return SPAN({"class" : "list-controls"}, " [",
		  A({'href' : "/item/" + id + "/close"},"x"),
		  " ",
		  addSubItemButton(id),
		  " ",
		  A({'href' : "/item/" + id + "/edit_form","title" : "edit"},"e"),
		  "] ");
   }
}

function liId(id) {
   if (sidebar) {
      return "sidebar-li-" + id;
   } else {
      return "li-" + id;
   }
}

function subItemForm(id) {
   if (sidebar) { return SPAN();}

   return DIV({"class" : "nextactionform invisible",
      "id" : "na-" + id},
              FORM({"action" : "/item/" + id + "/add",
		 "method" : "post",
		 "onsubmit" : "addSubItem(" + id + ",this.title.value);this.title.value = ''; return false"},
		   "add sub item: ",
		   INPUT({"type" : "text",
		      "name" : "title",
		      "value" : "",
		      "size" : "40"}),
		   INPUT({"type" : "submit",
		      "value" : "add"})));
}

function checkbox(id) {
   if (sidebar) { return SPAN();}
   return INPUT({"type" : "checkbox", "name" : "check-" + id,
   "class" : "checkbox", "onchange" : "selectChild(" + id + ")"});
}

function createItem(subitem) {
   var title = subitem['title'];
   var id = subitem['id'];
   var status = subitem['status'];
   var children = subitem['children'].length;

   
   return LI({'class' : status + " draggable", 'id' : liId(id)},
	     turnBuckle(id,children),
	     " ",
	     checkbox(id),
	     A({'href' : "/item/" + id + "/"},
	       subitem['title']),
	     actions(id),
	     subItemForm(id),
	     subitemsUl(id));   
}

function subitemsId(id) {
   if (sidebar) {
      return "sidebar-subitems-" + id;
   } else {
      return "subitems-" + id;
   }
}

function subitemsUl(id) {
   return UL({'class' : 'subitems invisible',
      'id' : subitemsId(id)});
}

function subitemsCallback(items) {
   var subitems = items['subitems'];
   var ul = $(subitemsId(current_item_id));
   for (var i = 0; i < subitems.length; i++) {
      var li = createItem(subitems[i]);
      ul.appendChild(li);
   }
   toggleVisible(ul);
}

function subitemsError(err) {
   alert("subitems request failed: " + err);
}

function showSubitems(item_id,s) {
   current_item_id = item_id;
   sidebar = s;
    var el = $(liId(item_id));
    var tb = el.getElementsByTagName("img")[0];

    if (showing[item_id] == 1) {
       hideSubItems(item_id);
       showing[item_id] = 0;
       tb.src = "/static/images/arrow_right.png";
    } else {
       showing[item_id] = 1;
       hideSubItems(item_id);
       tb.src = "/static/images/arrow_down.png";
       var url = "/item/" + item_id + "/subitems";
       d = loadJSONDoc(url);
       d.addCallbacks(subitemsCallback,subitemsError);
    }
}



function hideSubItems(item_id) {
    // just remove the ul and replace it.
   var ul = $(subitemsId(item_id));
   var li = $(liId(item_id));
   var placeholder = subitemsUl(item_id);
   if (ul && li) swapDOM(ul,placeholder);
      toggleVisible(ul);
}

function selectChild(id) {
   toggleElementClass("selected",$("li-" + id));

}

function selectedChildren() {
   var s = [];
   forEach(getElementsByTagAndClassName("input","checkbox"),
	   function (el) {
	      if(el.checked) {
		 s.push(el.name.substr(6));
	      }
	   });
   return s;
}

function reparent(target_id) {
   var s = selectedChildren();
   var url = "/item/" + target_id + "/reparent";
   var keys = [];
   if (s.length == 0) {
      // there are no children selected so we use the item_id
      s = [item_id];
   }
   for (var i = 0; i < s.length; i++) {keys.push("item_id");}
   var qs = queryString(keys,s);
   document.location = url + "?" + qs;
}

function addChild(target_id) {
   var s = selectedChildren();
   var url = "/item/" + target_id + "/add_child";
   var keys = [];
   if (s.length == 0) {
      // there are no children selected so we use the item_id
      s = [item_id];
   }
   for (var i = 0; i < s.length; i++) {keys.push("item_id");}
   var qs = queryString(keys,s);
   document.location = url + "?" + qs;

}

function subItemAdded(result) {
   var id        = result['id'];
   var title     = result['title'];
   var parent_id = result['parent_id'];
   result['status'] = 'OPEN';
   result['children'] = [];
   var li = createItem(result);
   var ul = $("children-list");
   if (parent_id != ITEM_ID) {
      // it's a child
      ul = $("subitems-" + parent_id);
      
   }
   ul.appendChild(li);
   if (parent_id != ITEM_ID) {
      // if the turnbuckle is closed, open it
      if (!isVisible(ul)) {
	 showSubitems(parent_id,false);
	 var el = $(liId(parent_id));
	 var tb = el.getElementsByTagName("img")[0];
	 var oc = Function("showSubitems(" + parent_id + ",false);return false;");
	 tb.onclick = oc;
      }
   }
}

function addSubItem(target_id,title) {
   var url = "/item/" + target_id + "/add_json";
   var d = loadJSONDoc(url,{"title" : title});
   d.addCallback(subItemAdded);
}
