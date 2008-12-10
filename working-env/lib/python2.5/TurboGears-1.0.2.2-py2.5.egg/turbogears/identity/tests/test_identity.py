# coding=UTF-8
import re
import unittest
import cherrypy
import turbogears
from turbogears import testutil, database, identity, config, startup
from turbogears.identity.soprovider import TG_User, TG_Group, TG_Permission

#hub = database.AutoConnectHub("sqlite:///:memory:")
hub = database.PackageHub("turbogears.identity")

class RestrictedArea(turbogears.controllers.Controller, identity.SecureResource):

    require = identity.in_group('peon')

    def index(self):
        return "restricted_index"
    index = turbogears.expose()(index)

    def in_admin_group(self):
        return 'in_admin_group'
    in_admin_group = turbogears.expose()(in_admin_group)
    in_admin_group = identity.require(identity.in_group('admin'))(in_admin_group)

    def in_other_group(self):
        return 'in_other_group'
    in_other_group = turbogears.expose()(in_other_group)
    in_other_group = identity.require(identity.in_group('other'))(in_other_group)

    def in_admin_group_explicit_check(self):
        if 'admin' not in identity.current.groups:
            raise identity.IdentityFailure("You need to be an Admin")
        else:
            return 'in_admin_group'
    in_admin_group_explicit_check = turbogears.expose()(
        in_admin_group_explicit_check)

    def in_other_group_explicit_check(self):
        if 'other' not in identity.current.groups:
            raise identity.IdentityException
        else:
            return 'in_other_group'
    in_other_group_explicit_check = turbogears.expose()(
        in_other_group_explicit_check)

class IdentityRoot(turbogears.controllers.RootController):

    def index(self):
        pass
    index = turbogears.expose()(index)

    def identity_failed(self):
        return 'identity_failed_answer'
    identity_failed = turbogears.expose()(identity_failed)

    #@turbogears.expose()
    #@identity.require(identity.not_anonymous())
    def logged_in_only(self):
        return 'logged_in_only'
    logged_in_only = turbogears.expose()(logged_in_only)
    logged_in_only = identity.require(identity.not_anonymous())(logged_in_only)

    #@turbogears.expose()
    #@identity.require(identity.in_group('peon'))
    def in_peon_group(self):
        return 'in_peon_group'
    in_peon_group = turbogears.expose()(in_peon_group)
    in_peon_group = identity.require(identity.in_group('peon'))(in_peon_group)

    def test_exposed_require(self):
        if not hasattr(self.in_peon_group, '_require'):
            return 'no _require attr'
        if not isinstance(self.in_peon_group._require, identity.in_group):
            return 'not correct class'
        if 'peon' != self.in_peon_group._require.group_name:
            return 'not correct group name'
        return '_require is exposed'
    test_exposed_require= turbogears.expose()(test_exposed_require)

    def in_admin_group(self):
        return 'in_admin_group'
    in_admin_group = turbogears.expose()(in_admin_group)
    in_admin_group = identity.require(identity.in_group('admin'))(in_admin_group)

    def has_chopper_permission(self):
        return 'has_chopper_permission'
    has_chopper_permission = turbogears.expose()(has_chopper_permission)
    has_chopper_permission = identity.require(identity.has_permission('chops_wood'))(has_chopper_permission)

    def has_boss_permission(self):
        return "has_boss_permission"
    has_boss_permission = turbogears.expose()(has_boss_permission)
    has_boss_permission = identity.require(identity.has_permission('bosses_people'))(has_boss_permission)

    def logout(self):
        identity.current.logout()
        return "logged out"
    logout = turbogears.expose()(logout)

    def user_email(self):
        return identity.current.user.email_address
    user_email = turbogears.expose()(user_email)
    user_email = identity.require(identity.not_anonymous())(user_email)

    peon_area = RestrictedArea()

    def new_user_setup(self, user_name, password):
        return '%s %s' % (user_name, password)
    new_user_setup = turbogears.expose()(new_user_setup)


class TestIdentity(unittest.TestCase):

    def setUp(self):
        # identity requires visit and a failure_url
        test_config = {'visit.on': True, 'identity.on': True,
            'identity.failure_url': '/identity_failed',
            'identity.soprovider.encryption_algorithm': None}
        old_configuration = dict() 
        for key in test_config: 
            old_configuration[key] = config.get(key) 
        self._original_config = old_configuration         
        config.update(test_config)
        cherrypy.root = IdentityRoot()
        startup.startTurboGears()
        self.init_model()

    def tearDown(self):
        startup.stopTurboGears()
        config.update(self._original_config)

    def init_model(self):
        if TG_User.select().count() == 0:
            user = TG_User(user_name='samIam', email_address='samiam@example.com',
                            display_name='Samuel Amicus', password='secret')
            peon_group = TG_Group(group_name="peon", display_name="Regular Peon")
            admin_group = TG_Group(group_name="admin", display_name="Administrator")
            other_group = TG_Group(group_name="other", display_name="Another Group")
            chopper_perm = TG_Permission(permission_name='chops_wood', description="Wood Chopper")
            boss_perm = TG_Permission(permission_name='bosses_people', description="Benevolent Dictator")
            peon_group.addTG_Permission(chopper_perm)
            admin_group.addTG_Permission(boss_perm)
            user.addTG_Group(peon_group)
            user.addTG_Group(other_group)

    def test_user_password_parameters(self):
        "Controller can receive user_name and password parameters."
        testutil.create_request('/new_user_setup?user_name=test&password=pw')
        firstline = cherrypy.response.body[0]
        assert 'test pw' in firstline, firstline

    def test_user_exists(self):
        u = TG_User.by_user_name('samIam')
        assert u.email_address == 'samiam@example.com'

    def test_user_password(self):
        "Test if we can set a user password (no encryption algorithm)."
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password='password'
        u.sync()
        assert u.password=='password'
        hub.rollback()
        hub.end()
        
    def test_user_password_unicode(self):
        """Test if we can set a user password which is encoded as unicode (no 
        encryption algorithm)."""
        config.update({'identity.soprovider.encryption_algorithm':None})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password = u'garçon'
        u.sync()
        self.assertEqual(u.password, u'garçon')
        hub.rollback()
        hub.end()

    def test_user_password_hashed_sha(self):
        "Test if a sha hashed password is stored in the database."
        config.update({'identity.soprovider.encryption_algorithm':'sha1'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password = 'password'
        u.sync()
        assert u.password =='5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8'
        hub.rollback()
        hub.end()
        
    def test_user_password_hashed_sha_unicode(self):
        """Test if a sha hashed password with unicode characters is stored in 
        the database."""
        config.update({'identity.soprovider.encryption_algorithm':'sha1'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password = u'garçon'
        u.sync()
        self.failUnlessEqual(u.password, '442edb21c491a6e6f502eb79e98614f3c7edf43e')
        hub.rollback()
        hub.end()

    def test_user_password_hashed_md5(self):
        "Test if a md5 hashed password is stored in the database."
        config.update({'identity.soprovider.encryption_algorithm':'md5'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password = 'password'
        u.sync()
        assert u.password =='5f4dcc3b5aa765d61d8327deb882cf99'
        hub.rollback()
        hub.end()
        
    def test_user_password_hashed_md5_unicode(self):
        """Test if a md5 hashed password with unicode characters is stored in 
        the database."""
        config.update({'identity.soprovider.encryption_algorithm':'md5'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password = u'garçon'
        u.sync()
        self.assertEqual(u.password, 'c295c4bb2672ca8c432effc53b40bb1e')
        hub.rollback()
        hub.end()

    def test_user_password_hashed_md5_utf8string(self):
        """Test if a md5 hashed password with unicode characters is stored in 
        the database if the password is entered as str (encoded in UTF-8). This
        test ensures that the encryption algorithm does handle non-unicode
        parameters gracefully."""
        config.update({'identity.soprovider.encryption_algorithm':'md5'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.password = u'garçon'.encode('UTF-8')
        u.sync()
        self.assertEqual(u.password, 'c295c4bb2672ca8c432effc53b40bb1e')
        hub.rollback()
        hub.end()

    def test_user_password_raw(self):
        "Test that we can store raw values in the password field (without being hashed)."
        config.update({'identity.soprovider.encryption_algorithm':'sha1'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.set_password_raw('password')
        u.sync()
        assert u.password =='password'
        hub.rollback()
        hub.end()
        
    def test_user_password_raw_unicode(self):
        config.update({'identity.soprovider.encryption_algorithm':'sha1'})
        # force new config values to load
        startup.startTurboGears()
        testutil.create_request('/')
        hub.begin()
        u = TG_User.by_user_name('samIam')
        u.set_password_raw(u'garçon')
        u.sync()
        self.assertEqual(u.password, u'garçon')
        hub.rollback()
        hub.end()
        
    def test_anonymous_browsing(self):
        "Test if we can show up anonymously."
        testutil.create_request('/')
        assert identity.current.anonymous

    def test_deny_anonymous(self):
        "Test that we have secured an url from anonymous users."
        testutil.create_request('/logged_in_only')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_deny_anonymous_viewable(self):
        "Test that a logged in user can see an resource blocked from anonymous users."
        testutil.create_request('/logged_in_only?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'logged_in_only' in firstline, firstline

    def test_logout(self):
        "Test that logout works and the session is not valid anymore afterwards."
        testutil.create_request('/in_peon_group?user_name=samIam&password=secret&login=Login')
        self.assertEquals("samIam", cherrypy.serving.request.identity.user_name)

        x = re.match("Set-Cookie: (.*?); Path.*", str(cherrypy.response.simple_cookie) )
        session_id = x.group(1)
        testutil.create_request('/logout', headers={'Cookie': session_id })

        self.assertEquals(None, cherrypy.serving.request.identity.user_name)
        assert cherrypy.serving.request.identity.anonymous

    def test_logout_with_set_identity(self):
        """Test that logout works even when there is no visit_key (e.g. when 
        testutils.set_identity_user is used)."""
        request = testutil.DummyRequest()
        old_user = testutil.test_user
        user = TG_User.by_user_name("samIam")
        testutil.set_identity_user(user)
        testutil.attach_identity(request)
        testutil.set_identity_user(old_user)
        testutil.call_with_request(cherrypy.root.logout, request)
        assert request.identity.anonymous

    def test_require_group(self):
        "Test that a anonymous user"
        testutil.create_request('/in_peon_group')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_require_expose_required_permission(self):
        '''
        Test that the decorator exposes the correct permissions via _require
        attribute on the actual method.
        '''
        testutil.create_request('/test_exposed_require')
        firstline= cherrypy.response.body[0]
        assert 'require is exposed' in firstline, firstline

    def test_require_group_viewable(self):
        "Test that a user with proper group membership can see a restricted url."
        testutil.create_request('/in_peon_group?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'in_peon_group' in firstline, firstline

    def test_user_not_in_right_group(self):
        "Test that a user is denied access if they aren't in the right group."
        testutil.create_request('/in_admin_group?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_require_permission(self):
        "Test that an anonymous user is denied access to a permission restricted url."
        testutil.create_request('/has_chopper_permission')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_require_permission_viewable(self):
        "Test that a user with proper permissions can see a restricted url."
        testutil.create_request('/has_chopper_permission?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'has_chopper_permission' in firstline, firstline

    def test_user_lacks_permission(self):
        "Test that a user is denied acces if they don't have the proper permission."
        testutil.create_request('/has_boss_permission?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_user_info_available(self):
        "Test that we can see user information inside our controller."
        testutil.create_request('/user_email?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'samiam@example.com' in firstline, firstline

    def test_bad_login(self):
        "Test that we are denied access if we provide a bad login."
        testutil.create_request('/logged_in_only?user_name=samIam&password=wrong&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_restricted_subdirectory(self):
        "Test that we can restrict access to a whole subdirectory."
        testutil.create_request('/peon_area/index')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_restricted_subdirectory_viewable(self):
        "Test that we can access a restricted subdirectory if we have proper credentials."
        testutil.create_request('/peon_area/index?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'restricted_index' in firstline, firstline

    def test_decoratator_in_restricted_subdirectory(self):
        """Test that we can require a different permission in a
        protected subdirectory."""
        testutil.create_request('/peon_area/in_other_group?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'in_other_group' in firstline, firstline

    def test_decoratator_failure_in_restricted_subdirectory(self):
        """Test that we can get an identity failure from a decorator
        in a restricted subdirectory"""
        testutil.create_request('/peon_area/in_admin_group?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed_answer' in firstline, firstline

    def test_explicit_checks_in_restricted_subdirectory(self):
        """Test that explicit permission checks in a protected
        directory is handled as expected"""
        testutil.create_request('/peon_area/in_other_group_explicit_check?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'in_other_group' in firstline, firstline

    def test_throwing_identity_exception_in_restricted_subdirectory(self):
        """Test that throwing an IdentityException in a protected
        directory is handled as expected"""
        testutil.create_request('/peon_area/in_admin_group_explicit_check?user_name=samIam&password=secret&login=Login')
        firstline = cherrypy.response.body[0]
        assert 'identity_failed' in firstline, firstline


class TestTGUser(testutil.DBTest):
    model = TG_User

    def setUp(self):
        self._identity_on = config.get('identity.on', False)
        config.update({'identity.on': False})
        try:
            self._provider = cherrypy.request.identityProvider
        except AttributeError:
            self._provider= None
        cherrypy.request.identityProvider = None
        startup.startTurboGears()
        testutil.DBTest.setUp(self)

    def tearDown(self):
        testutil.DBTest.tearDown(self)
        startup.stopTurboGears()
        cherrypy.request.identityProvider = self._provider
        config.update({'identity.on': self._identity_on})

    def test_create_user(self):
        """Check that User can be created outside of a running identity provider."""
        u = TG_User(user_name='testcase', email_address='testcase@example.com',
                        display_name='Test Me', password='test')
        assert u.password=='test', u.password
