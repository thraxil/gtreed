import cherrypy
import random
from datetime import *

import turbogears
from turbogears import identity
from turbogears.util import load_class
from turbogears.database import session
from turbojson.jsonify import *

import logging
log = logging.getLogger("turbogears.identity.saprovider")

try:
    set, frozenset
except NameError:
    from sets import Set as set, ImmutableSet as frozenset

# Global class references --
# these will be set when the Provider is initialised.
user_class = None
group_class = None
permission_class = None
visit_class = None

class SqlAlchemyIdentity(object):

    def __init__(self, visit_key, user=None):
        if user:
            self._user = user
        self.visit_key = visit_key

    def _get_user(self):
        try:
            return self._user
        except AttributeError:
            # User hasn't already been set
            pass
        # Attempt to load the user. After this code executes, there *WILL* be
        # a _user attribute, even if the value is None.
        visit = session.query(visit_class).get_by(visit_key = self.visit_key)
        if not visit:
            self._user = None
            return None
        self._user = session.query(user_class).get(visit.user_id)
        return self._user
    user = property(_get_user)

    def _get_user_name(self):
        if not self.user:
            return None
        return self.user.user_name
    user_name = property(_get_user_name)

    def _get_anonymous(self):
        return not self.user
    anonymous = property(_get_anonymous)

    def _get_permissions(self):
        try:
            return self._permissions
        except AttributeError:
            # Permissions haven't been computed yet
            pass
        if not self.user:
            self._permissions = frozenset()
        else:
            self._permissions = frozenset([
                    p.permission_name for p in self.user.permissions])
        return self._permissions
    permissions = property(_get_permissions)

    def _get_groups(self):
        try:
            return self._groups
        except AttributeError:
            # Groups haven't been computed yet
            pass
        if not self.user:
            self._groups = frozenset()
        else:
            self._groups = frozenset([g.group_name for g in self.user.groups])
        return self._groups
    groups = property(_get_groups)

    def logout(self):
        '''
        Remove the link between this identity and the visit.
        '''
        if not self.visit_key:
            return
        try:
            visit = session.query(visit_class).get_by(visit_key=self.visit_key)
            session.delete(visit)
            # Clear the current identity
            anon = SqlAlchemyIdentity(None,None)
            identity.set_current_identity(anon)
        except:
            pass
        else:
            session.flush()


class SqlAlchemyIdentityProvider(object):
    '''
    IdentityProvider that uses a model from a database (via SQLAlchemy).
    '''

    def __init__(self):
        super(SqlAlchemyIdentityProvider, self).__init__()
        get=turbogears.config.get

        global user_class, group_class, permission_class, visit_class

        user_class_path = get("identity.saprovider.model.user",
                              None)
        user_class = load_class(user_class_path)
        group_class_path = get("identity.saprovider.model.group",
                                None)
        group_class = load_class(group_class_path)
        permission_class_path = get("identity.saprovider.model.permission",
                                    None)
        permission_class = load_class(permission_class_path)
        visit_class_path = get("identity.saprovider.model.visit",
                               None)
        log.info("Loading: %s", visit_class_path)
        visit_class = load_class(visit_class_path)
        # Default encryption algorithm is to use plain text passwords
        algorithm = get("identity.saprovider.encryption_algorithm", None)
        self.encrypt_password = lambda pw: \
                                    identity._encrypt_password(algorithm, pw)

    def create_provider_model(self):
        '''
        Create the database tables if they don't already exist.
        '''
        user_class.mapper.local_table.create(checkfirst=True)
        group_class.mapper.local_table.create(checkfirst=True)
        permission_class.mapper.local_table.create(checkfirst=True)
        visit_class.mapper.local_table.create(checkfirst=True)

    def validate_identity(self, user_name, password, visit_key):
        '''
        Look up the identity represented by user_name and determine whether the
        password is correct.

        Must return either None if the credentials weren't valid or an object
        with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        user = session.query(user_class).get_by(user_name=user_name)
        if not user:
            log.warning("No such user: %s", user_name)
            return None
        if not self.validate_password(user, user_name, password):
            log.info("Passwords don't match for user: %s", user_name)
            return None

        log.info("associating user (%s) with visit (%s)", user.user_name,
                  visit_key)
        # Link the user to the visit
        link = session.query(visit_class).get_by(visit_key=visit_key)
        if not link:
            link = visit_class(visit_key=visit_key, user_id=user.user_id)
            session.save(link)
        else:
            link.user_id = user.user_id
        session.flush()
        return SqlAlchemyIdentity(visit_key, user)

    def validate_password(self, user, user_name, password):
        '''
        Check the supplied user_name and password against existing credentials.
        Note: user_name is not used here, but is required by external
        password validation schemes that might override this method.
        If you use SqlAlchemyIdentityProvider, but want to check the passwords
        against an external source (i.e. PAM, LDAP, Windows domain, etc),
        subclass SqlAlchemyIdentityProvider, and override this method.
        '''
        return user.password == self.encrypt_password(password)

    def load_identity(self, visit_key):
        '''
        Lookup the principal represented by user_name.
        Return None if there is no principal for the given user ID.

        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        return SqlAlchemyIdentity(visit_key)

    def anonymous_identity(self):
        '''
        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        return SqlAlchemyIdentity(None)

    def authenticated_identity(self, user):
        '''
        Constructs Identity object for user that has no associated visit_key.
        '''
        return SqlAlchemyIdentity(None, user)
