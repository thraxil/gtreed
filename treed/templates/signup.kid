<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:py="http://purl.org/kid/ns#"
    py:extends="'master.kid'">
<head>
<meta content="text/html; charset=utf-8" http-equiv="Content-Type" py:replace="''"/>
<title>Welcome to TurboGears</title>
</head>
<body>
<div id="header">&nbsp;</div>
<div id="main_content">
  <div id="sidebar">
    <h2>Sidebar</h2>
    <ul class="links">
    </ul>
  </div>
  <div id="page-content">
    <form action="/signup" method="post">
      <table>

	<tr>
	  <th>username:</th>
	  <td><input type="text" name="username" /></td>
	</tr>

	<tr>
	  <th>full name:</th>
	  <td><input type="text" name="fullname" /></td>
	</tr>

	<tr>
	  <th>email:</th>
	  <td><input type="text" name="email" /></td>
	</tr>

	<tr>
	  <th>password</th>
	  <td><input type="password" name="password" /></td>
	</tr>

	<tr>
	  <th>verify password</th>
	  <td><input type="password" name="pass2" /></td>
	</tr>

	<tr>
	  <td colspan="2"><input type="submit" value="signup"/></td>
	</tr>

      </table>
    </form>
  </div>
  <!-- End of getting_started -->
</div>
</body>
</html>
