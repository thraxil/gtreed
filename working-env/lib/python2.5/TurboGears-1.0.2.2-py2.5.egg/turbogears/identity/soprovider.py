import random

from turbojson.jsonify import jsonify_sqlobject, jsonify
from sqlobject import *
from sqlobject.inheritance import InheritableSQLObject

import logging
log = logging.getLogger("turbogears.identity.soprovider")

from datetime import *

import turbogears

from turbogears import identity
from turbogears.database import PackageHub
from turbogears.util import load_class

import warnings

hub = PackageHub("turbogears.identity")
__connection__ = hub

try:
    set, frozenset
except NameError:
    from sets import Set as set, ImmutableSet as frozenset

def to_db_encoding(s, encoding):
    if isinstance(s, str):
        pass
    elif hasattr(s, '__unicode__'):
        s = unicode(s)
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return s

class DeprecatedAttr(object):
    def __init__(self, old_name, new_name):
        self.old_name= old_name
        self.new_name= new_name
    
    def __get__(self, obj, type=None):
        warnings.warn( "%s has been deprecated in favour of %s" %
                       (self.old_name, self.new_name), DeprecationWarning )
        return getattr( obj, self.new_name )

    def __set__(self, obj, value):
        warnings.warn( "%s has been deprecated in favour of %s" %
                       (self.old_name, self.new_name), DeprecationWarning )
        return setattr( obj, self.new_name, value )

        
# Global class references -- these will be set when the Provider is initialised.
user_class= None
group_class= None
permission_class= None
visit_class = None

class SqlObjectIdentity(object):
    def __init__(self, visit_key, user=None):
        if user:
            self._user= user
        self.visit_key= visit_key
    
    def _get_user(self):
        try:
            return self._user
        except AttributeError:
            # User hasn't already been set
            pass
        # Attempt to load the user. After this code executes, there *WILL* be
        # a _user attribute, even if the value is None.
        try:
            visit= visit_class.by_visit_key( self.visit_key )
        except SQLObjectNotFound:
            # The visit ID is invalid
            self._user= None
            return None
        try:
            self._user= user_class.get( visit.user_id )
            return self._user
        except SQLObjectNotFound:
            log.warning( "No such user with ID: %s", visit.user_id )
            self._user= None
            return None
    user= property(_get_user)
    
    def _get_user_name(self):
        if not self.user:
            return None
        return self.user.user_name
    user_name= property(_get_user_name)

    def _get_anonymous(self):
        return not self.user
    anonymous= property(_get_anonymous)
    
    def _get_permissions(self):
        try:
            return self._permissions
        except AttributeError:
            # Permissions haven't been computed yet
            pass
        if not self.user:
            self._permissions= frozenset()
        else:
            self._permissions= frozenset([p.permission_name for p in self.user.permissions])
        return self._permissions
    permissions= property(_get_permissions)
    
    def _get_groups(self):
        try:
            return self._groups
        except AttributeError:
            # Groups haven't been computed yet
            pass
        if not self.user:
            self._groups= frozenset()
        else:
            self._groups= frozenset([g.group_name for g in self.user.groups])
        return self._groups
    groups= property(_get_groups)

    def logout(self):
        '''
        Remove the link between this identity and the visit.
        '''
        try:
            if self.visit_key != None:
                visit= visit_class.by_visit_key(self.visit_key)
                visit.destroySelf()
        except SQLObjectNotFound:
            # If no visit exists in the database, we don't need to destroy it.
            pass
        # Clear the current identity
        anon= SqlObjectIdentity(None,None)
        #XXX if user is None anonymous will be true, no need to set attr.
        #anon.anonymous= True
        identity.set_current_identity( anon )

    
class SqlObjectIdentityProvider(object):
    '''
    IdentityProvider that uses a model from a database (via SQLObject).
    '''
    
    def __init__(self):
        super(SqlObjectIdentityProvider, self).__init__()
        get=turbogears.config.get
        
        global user_class, group_class, permission_class, visit_class
        
        user_class_path= get( "identity.soprovider.model.user", 
                              __name__ + ".TG_User" )
        #log.debug('userclassp:%s'% user_class_path)
        #user_class_path = 'kronos.model.Person'
        user_class= load_class(user_class_path)
        if user_class:
            log.info("Succesfully loaded \"%s\"" % user_class_path)
        try:
            self.user_class_db_encoding= \
                user_class.sqlmeta.columns['user_name'].dbEncoding
        except (KeyError, AttributeError):
            self.user_class_db_encoding= 'UTF-8'
        group_class_path= get( "identity.soprovider.model.group",
                                __name__ + ".TG_Group" )
        group_class= load_class(group_class_path)
        if group_class:
            log.info("Succesfully loaded \"%s\"" % group_class_path)
            
        permission_class_path= get( "identity.soprovider.model.permission",
                                    __name__ + ".TG_Permission" )
        permission_class= load_class(permission_class_path)
        if permission_class:
            log.info("Succesfully loaded \"%s\"" % permission_class_path)
        
        visit_class_path= get( "identity.soprovider.model.visit",
                                __name__ + ".TG_VisitIdentity" )
        visit_class= load_class(visit_class_path)
        if visit_class:
            log.info("Succesfully loaded \"%s\"" % visit_class_path)
        
            
        # Default encryption algorithm is to use plain text passwords
        algorithm = get("identity.soprovider.encryption_algorithm", None)
        self.encrypt_password = lambda pw: \
                                    identity._encrypt_password(algorithm, pw)
            
    def create_provider_model( self ):
        # create the database tables
        try:
            hub.begin()
            user_class.createTable(ifNotExists=True)
            group_class.createTable(ifNotExists=True)
            permission_class.createTable(ifNotExists=True)
            visit_class.createTable(ifNotExists=True)
            hub.commit()
            hub.end()
        except KeyError:
            log.warning( "No database is configured: SqlObjectIdentityProvider is disabled." )
            return

    def validate_identity( self, user_name, password, visit_key ):
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
        try:
            user_name= to_db_encoding( user_name, self.user_class_db_encoding )
            user= user_class.by_user_name( user_name )
            if not self.validate_password(user, user_name, password):
                log.info( "Passwords don't match for user: %s", user_name )
                return None
            
            # Link the user to the visit
            try:
                link= visit_class.by_visit_key( visit_key )
                link.user_id= user.id
            except SQLObjectNotFound:
                link= visit_class( visit_key=visit_key, user_id=user.id )
            return SqlObjectIdentity( visit_key, user )
            
        except SQLObjectNotFound:
            log.warning( "No such user: %s", user_name )
            return None

    def validate_password(self, user, user_name, password):
        '''
        Check the supplied user_name and password against existing credentials.
        Note: user_name is not used here, but is required by external
        password validation schemes that might override this method.
        If you use SqlObjectIdentityProvider, but want to check the passwords
        against an external source (i.e. PAM, a password file, Windows domain),
        subclass SqlObjectIdentityProvider, and override this method.
        '''
        return user.password == self.encrypt_password(password)

    def load_identity( self, visit_key ):
        '''
        Lookup the principal represented by user_name. Return None if there is no
        principal for the given user ID.
        
        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        return SqlObjectIdentity( visit_key )
    
    def anonymous_identity( self ):
        '''
        Must return an object with the following properties:
            user_name: original user name
            user: a provider dependant object (TG_User or similar)
            groups: a set of group IDs
            permissions: a set of permission IDs
        '''
        return SqlObjectIdentity( None )

    def authenticated_identity(self, user):
        '''
        Constructs Identity object for user that has no associated visit_key.
        '''
        return SqlObjectIdentity(None, user)


class TG_VisitIdentity(SQLObject):
    class sqlmeta:
        table="tg_visit_identity"

    visit_key= StringCol( length=40, alternateID=True,
                          alternateMethodName="by_visit_key" )
    user_id= IntCol()


class TG_Group(InheritableSQLObject):
    '''
    An ultra-simple group definition.
    '''
    class sqlmeta:
        table="tg_group"
    
    group_name= UnicodeCol( length=16, alternateID=True,
                            alternateMethodName="by_group_name" )
    display_name= UnicodeCol( length=255 )
    created= DateTimeCol( default=datetime.now )

    # Old names
    groupId= DeprecatedAttr( "groupId", "group_name" )
    displayName= DeprecatedAttr( "displayName", "display_name" )

    # collection of all users belonging to this group
    users= RelatedJoin( "TG_User", intermediateTable="tg_user_group",
                        joinColumn="group_id", otherColumn="user_id" )

    # collection of all permissions for this group
    permissions= RelatedJoin( "TG_Permission", joinColumn="group_id", 
                              intermediateTable="tg_group_permission",
                              otherColumn="permission_id" )


def jsonify_group(obj):
    result = jsonify_sqlobject( obj )
    result["users"]= [u.user_name for u in obj.users]
    result["permissions"]= [p.permission_name for p in obj.permissions]
    return result

jsonify_group = jsonify.when('isinstance(obj, TG_Group)')(jsonify_group)


class TG_User(InheritableSQLObject):
    '''
    Reasonably basic User definition. Probably would want additional attributes.
    '''
    class sqlmeta:
        table="tg_user"
    
    user_name= UnicodeCol( length=16, alternateID=True,
                           alternateMethodName="by_user_name" )
    email_address= UnicodeCol( length=255, alternateID=True,
                               alternateMethodName="by_email_address" )
    display_name= UnicodeCol( length=255 )
    password= UnicodeCol( length=40 )
    created= DateTimeCol( default=datetime.now )

    # Old attribute names
    userId= DeprecatedAttr( "userId", "user_name" )
    emailAddress= DeprecatedAttr( "emailAddress", "email_address" )
    displayName= DeprecatedAttr( "displayName", "display_name" )

    # groups this user belongs to
    groups= RelatedJoin( "TG_Group", intermediateTable="tg_user_group",
                         joinColumn="user_id", otherColumn="group_id" )

    def _get_permissions( self ):
        perms= set()
        for g in self.groups:
            perms= perms | set(g.permissions)
        return perms
        
    def _set_password( self, cleartext_password ):
        "Runs cleartext_password through the hash algorithm before saving."
        try:
            hash = identity.current_provider.encrypt_password(cleartext_password)
        except identity.exceptions.IdentityManagementNotEnabledException:
            # Creating identity provider just to encrypt password
            # (so we don't reimplement the encryption step).
            ip = SqlObjectIdentityProvider()
            hash = ip.encrypt_password(cleartext_password)
            if hash == cleartext_password:
                log.info("Identity provider not enabled, and no encryption algorithm "
                        "specified in config.  Setting password as plaintext.")
        self._SO_set_password(hash)
        
    def set_password_raw( self, password ):
        "Saves the password as-is to the database."
        self._SO_set_password(password)


def jsonify_user(obj):
    result = jsonify_sqlobject( obj )
    del result['password']
    result["groups"]= [g.group_name for g in obj.groups]
    result["permissions"]= [p.permission_name for p in obj.permissions]
    return result

jsonify_user = jsonify.when('isinstance(obj, TG_User)')(jsonify_user)


class TG_Permission(InheritableSQLObject):
    class sqlmeta:
        table="tg_permission"
    
    permission_name= UnicodeCol( length=16, alternateID=True,
                                 alternateMethodName="by_permission_name" )
    description= UnicodeCol( length=255 )
    
    # Old attributes
    permissionId= DeprecatedAttr( "permissionId", "permission_name" )

    groups= RelatedJoin( "TG_Group", intermediateTable="tg_group_permission",
                         joinColumn="permission_id", otherColumn="group_id" )


def jsonify_permission(obj):
    result = jsonify_sqlobject( obj )
    result["groups"]= [g.group_name for g in obj.groups]
    return result

jsonify_permission = jsonify.when(
        'isinstance(obj, TG_Permission)')(jsonify_permission)

def encrypt_password(cleartext_password):
    try:
        hash = identity.current_provider.\
                            encrypt_password(cleartext_password)
    except identity.exceptions.RequestRequiredException:
        # Creating identity provider just to encrypt password
        # (so we don't reimplement the encryption step).
        ip = SqlObjectIdentityProvider()
        hash = ip.encrypt_password(cleartext_password)
        if hash == cleartext_password:
            log.info("Identity provider not enabled, and no encryption "
                    "algorithm "
                    "specified in config.  Setting password as plaintext.")
    return hash
