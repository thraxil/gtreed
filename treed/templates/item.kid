<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">


<head>

<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>GTreeD: ${item.title}</title>
<script type="text/javascript">
var ITEM_ID = ${item.id};
</script>
<script type="text/javascript"
	src="/static/javascript/dragdropreorder.js"></script>
<link rel="alternate" href="/atom/${item.id}/"
	type="application/atom+xml" title="Atom feed for
	${item.title}" />
<link rel="stylesheet" href="/static/css/print.css" type="text/css" media="print"/>
</head>
<body>
<div id="header">&nbsp;</div>
<div id="main_content">
  ${sidebar()}
  ${flash()}
  <div id="page-content">

    <p id="actions"><a href="edit_form">edit</a></p>    

    <table>
      <tr>
	<th colspan="2"><h1 id="title">${item.title}</h1> 
	  <div id="title-edit" class="edit-form">
	    <form action="/item/${item.id}/update" method="post" onsubmit="update('title',this.title.value)">
	      <p>
		<input type="text" name="title" value="${item.title}"/><br />
		<input type="submit" value="save title" />
	      </p>
	    </form>
	  </div>
	</th>
	<th
	colspan="2"><span
	class="${item.status}">${item.status}</span> 
	  [
	  <a href="close" py:if="item.status == 'OPEN'">close</a>
	  <a href="reopen" py:if="item.status == 'CLOSED'">reopen</a>
	]</th>
      </tr>

<!--      <tr>
	<th>assigned to:</th>
	<td>${item.assigned_to.display_name}</td>
	<th>owner:</th>
	<td>${item.owner.display_name}</td>
      </tr> -->

      <tr>
	<th>modified:</th>
	<td>${item.modified}</td>
	<th>added:</th>
	<td>${item.added}</td>
      </tr>

      <tr>
	<td colspan="4" py:if="item.description">
	  <p py:if="item.description">${item.description}</p>
	  
	</td>
      </tr>
      <tr py:if="item.parents"><th>Parents:</th>
	<td colspan="3">
	  <ul py:if="item.parents" class="parents"> 
	    <li py:for="parent in
	    item.get_parents()"><img src="/static/images/blank.png"
     width="10" height="10" alt="" border="0" class="turnbuckle"/> 
	      <span py:for="gp in parent.parent_trail()">
		<a href="/item/${gp.id}/">${gp.title}</a> /
	      </span>
	      <a
	    href="/item/${parent.id}/">${parent.title}</a>
	      <span class="list-controls">
	    [<a href="detach?parent_id=${parent.id}">detach</a>]</span></li>
	  </ul>

	</td>
      </tr>

      <tr>
	<th>Children:</th>
	<td colspan="3" >
	  <ul id="children-list">
	    <li py:for="child in item.get_open_children()" 
	  class="${item.status} draggable" id="li-${child.id}">
<img py:if="len(child.children) == 0" src="/static/images/blank.png"
     width="10" height="10" alt="" border="0" class="turnbuckle"/>
<a py:if="len(child.children) > 0"
   href=""
   title="show/hide children"
   onclick="showSubitems(${child.id},false);return false"
   ><img src="/static/images/arrow_right.png" 
	 width="10" height="10" alt="&gt;"
	 border="0" class="turnbuckle"/></a>
<input type="checkbox" name="check-${child.id}" class="checkbox" 
onchange="selectChild(${child.id})"
/>
<a href="/item/${child.id}/">${child.title}</a>

	  <span class="list-controls">
	    [<a href="/item/${child.id}/close" title="close">x</a>
	    <a href="add" title="add sub item"
	    onclick="toggleNextActionForm('${child.id}'); return false">+</a>
	    <a href="/item/${child.id}/edit_form" title="edit">e</a>
	    ]
	  </span>

	  <div class="nextactionform invisible" id="na-${child.id}">
            <form action="/item/${child.id}/add" method="post" onsubmit="addSubItem(${child.id},this.title.value);this.title.value = ''; return false">
              add sub item: 
              <input type="text" name="title" value="" size="40" /><input type="submit" value="add"/>
            </form>
          </div>
	  <ul class="subitems invisible" id="subitems-${child.id}"/>

	</li>
    </ul>
    <form action="add" method="post" onsubmit="addSubItem(${item.id},this.title.value);this.title.value = ''; return false"> 
	<p><label>title: <input type="text" name="title"
	size="50"/></label><input type="submit" value="add"
	/></p>
    </form>

<ul py:if="item.get_closed_children()"> Closed Children
	    <li py:for="child in item.get_closed_children()" 
	  class="${child.status}" id="li-${child.id}">
<img py:if="len(child.children) == 0" src="/static/images/blank.png"
     width="10" height="10" alt="" border="0" class="turnbuckle"/>
<a py:if="len(child.children) > 0"
   href=""
   title="show/hide children"
   onclick="showSubitems(${child.id},false);return false"
   ><img src="/static/images/arrow_right.png" 
	 width="10" height="10" alt="&gt;"
	 border="0" class="turnbuckle"/></a>

<a href="/item/${child.id}/">${child.title}</a>

	  <span class="list-controls">
	    [<a href="/item/${child.id}/reopen"
	    title="reopen">reopen</a>]
	    [<a href="/item/${child.id}/delete" title="delete"
	    onclick="return confirm('are you sure?')">delete</a>]
	  </span>
	</li>
    </ul>


    </td>
	</tr>
      </table>
    

  </div>
  <!-- End of getting_started -->
</div>
</body>
</html>
