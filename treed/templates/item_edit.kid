<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Editing ${item.title}</title>
</head>
<body>
<div id="header">&nbsp;</div>
<div id="main_content">
  ${sidebar()}
  <div id="page-content">
  <form action="edit" method="post">
    <table>
      <tr>
	<th colspan="2"><input type="text" name="title"
      value="${item.title}" size="50" /> 
	</th>
	<th colspan="2"><select name="status">
	<option value="OPEN" selected="selected" py:if="item.status == 'OPEN'">OPEN</option>
	<option value="OPEN" py:if="item.status != 'OPEN'">OPEN</option>
	<option value="CLOSED" selected="selected" py:if="item.status == 'CLOSED'">CLOSED</option>
	<option value="CLOSED" py:if="item.status != 'CLOSED'">CLOSED</option>
	</select>
	</th>
      </tr>

      <tr>
	<th>assigned to:</th>
	<td>${item.assigned_to.display_name} <a
	href=""><img class="edit" src="/static/images/edit.gif"/></a></td>
	<th>owner:</th>
	<td>${item.owner.display_name} <a
	href=""><img class="edit" src="/static/images/edit.gif"/></a></td>
      </tr>

      <tr>
	<th>modified:</th>
	<td>${item.modified}</td>
	<th>added:</th>
	<td>${item.added}</td>
      </tr>

      <tr>
	<td colspan="4">
	<textarea cols="70" rows="10" name="description">${item.description}</textarea>
	</td>
      </tr>

      <tr>
        <td colspan="4">
	<input type="submit" value="save changes"/>
	</td>
      </tr>


      <tr py:if="item.parents"><th>Parents:</th>
	<td colspan="3">
	  <ul py:if="item.parents" class="parents"> 
	    <li py:for="parent in item.get_parents()"><a href="/item/${parent.id}/">${parent.title}</a></li>
	  </ul>
	</td>
      </tr>
      </table>

    </form>
  </div>
  <!-- End of getting_started -->
</div>
</body>
</html>
