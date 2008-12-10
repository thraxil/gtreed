import cherrypy
import socket
import struct
import threading
import types
import turbogears
from turbogears.identity.exceptions import *
from turbogears.identity import *
from turbogears.decorator import weak_signature_decorator

class Predicate(object):
    '''
    Generic base class for testing true or false for a condition.
    '''
    def eval_with_object( self, obj, errors=None ):
        '''
        Determine whether the predicate is True or False for the given object.
        '''
        raise NotImplementedError

    def append_error_message( self, errors=None ):
        if errors is None:
            return
        errors.append( self.error_message % self.__dict__ )


class CompoundPredicate(Predicate):
    '''
    A predicate composed of other predicates.
    '''
    def __init__(self, *predicates):
        self.predicates= predicates


class All(CompoundPredicate):
    '''
    A compound predicate that evaluates to true only if all sub-predicates
    evaluate to true for the given input.
    '''
    def eval_with_object( self, obj, errors=None ):
        '''
        Return true if all sub-predicates evaluate to true.
        '''
        for p in self.predicates:
            if not p.eval_with_object( obj, errors ):
                return False
        return True


class Any(CompoundPredicate):
    '''
    A compound predicate that evaluates to true if any one of its sub-predicates
    evaluates to true.
    '''
    error_message= "No predicates were able to grant access"

    def eval_with_object( self, obj, errors=None ):
        '''
        Return true if any sub-predicate evaluates to true.
        '''
        for p in self.predicates:
            if p.eval_with_object( obj, None ):
                return True
        self.append_error_message( errors )
        return False


class IdentityPredicateHelper(object):
    '''
    A mix-in helper class for Identity Predicates.
    '''
    def __nonzero__(self):
        return self.eval_with_object( current )


class in_group(Predicate, IdentityPredicateHelper):
    '''
    Predicate for requiring a group.
    '''
    error_message= "Not member of group: %(group_name)s"

    def __init__(self, group_name):
        self.group_name= group_name

    def eval_with_object( self, identity, errors=None ):
        if self.group_name in identity.groups:
            return True
        self.append_error_message( errors )
        return False


class in_all_groups(All, IdentityPredicateHelper):
    '''
    Predicate for requiring membership in a number of groups.
    '''
    def __init__(self, *groups):
        group_predicates= [in_group(g) for g in groups]
        super(in_all_groups,self).__init__( *group_predicates )


class in_any_group(Any, IdentityPredicateHelper):
    '''
    Predicate for requiring membership in at least one group
    '''
    error_message= "Not member of any group: %(group_list)s"

    def __init__(self, *groups):
        self.group_list= ", ".join(groups)
        group_predicates= [in_group(g) for g in groups]
        super(in_any_group,self).__init__( *group_predicates )


class not_anonymous(Predicate, IdentityPredicateHelper):
    '''
    Predicate for checking whether current visitor is anonymous.
    '''
    error_message= "Anonymous access denied"

    def eval_with_object( self, identity, errors=None ):
        if current.anonymous:
            self.append_error_message( errors )
            return False
        return True


class has_permission(Predicate, IdentityPredicateHelper):
    '''
    Predicate for checking whether the visitor has a particular permission.
    '''
    error_message= "Permission denied: %(permission_name)s"

    def __init__(self, permission_name):
        self.permission_name= permission_name

    def eval_with_object(self, identity, errors=None):
        '''
        Determine whether the visitor has the specified permission.
        '''
        if self.permission_name in identity.permissions:
            return True

        self.append_error_message( errors )
        return False


class has_all_permissions(All, IdentityPredicateHelper):
    '''
    Predicate for checking whether the visitor has all permissions.
    '''
    def __init__(self, *permissions):
        permission_predicates= [has_permission(p) for p in permissions]
        super(has_all_permissions,self).__init__( *permission_predicates )


class has_any_permission(Any, IdentityPredicateHelper):
    '''
    Predicate for checking whether the visitor has at least one permission.
    '''
    error_message= "No matching permissions: %(permission_list)s"

    def __init__(self, *permissions):
        self.permission_list= ", ".join( permissions )
        permission_predicates= [has_permission(p) for p in permissions]
        super(has_any_permission,self).__init__( *permission_predicates )


def _remoteHost():
    try:
        ips= cherrypy.request.headers.get( "X-Forwarded-For",
                                             cherrypy.request.remote_host )
        return ips.split(",")[-1].strip()
    except:
        return ""


def _match_ip(cidr, ip):
    if not '/' in cidr:
        return cidr == ip
    else:
        try:
            b,m = cidr.split('/')
            shift = 32 - int(m)
            a1 = struct.unpack('!L', socket.inet_aton(b))[0] >> shift
            a2 = struct.unpack('!L', socket.inet_aton(ip))[0] >> shift
            return a1 == a2
        except:
            return False


class from_host(Predicate, IdentityPredicateHelper):
    '''
    Predicate for checking whether the visitor's host is an allowed host.
    Note: We never want to announce what the list of allowed hosts is, because
    it is way too easy to spoof an IP address in a TCP/IP packet.
    '''
    error_message= "Access from this host is not permitted."

    def __init__(self, host):
        self.host= host

    def eval_with_object( self, obj, errors=None ):
        '''
        Match the visitor's host against the criteria.
        '''
        ip = _remoteHost()
        if _match_ip( self.host, ip ):
            return True
        self.append_error_message( errors )
        return False


class from_any_host(Any, IdentityPredicateHelper):
    '''
    Predicate for checking whether the visitor's host is one of a number of
    permitted hosts.
    '''
    error_message= "Access from this host is not permitted."

    def __init__(self, hosts):
        host_predicates= [from_host(h) for h in hosts]
        super(from_any_host,self).__init__( *host_predicates )


def require(predicate, obj=None):
    '''
    Function decorator that checks whether the current user is a member of the
    groups specified and has the permissions required.
    '''
    def entangle(fn):
        def require(func, self, *args, **kwargs):
            try:
                errors= []
                if predicate is None or \
                   predicate.eval_with_object(current, errors):
                   return fn(self, *args, **kwargs)
            except IdentityException, e:
                errors= [str(e)]

            raise IdentityFailure(errors)

        fn._require= predicate
        return require
    return weak_signature_decorator(entangle)

def _secureResourceDecorator( fn ):
    '''
    A decorator function used by the SecureResourceMeta metaclass.
    '''
    def _wrapper( self, *args, **kwargs ):
        predicate= getattr( self.__class__, "require", None )

        try:
            errors= []
            if predicate is None or \
               predicate.eval_with_object( current, errors ):
               return fn( self, *args, **kwargs )
        except IdentityException, e:
            errors= [str(e)]

        raise IdentityFailure( errors )

    try:
        _wrapper.func_name= fn.func_name
    except TypeError:
        pass
    if hasattr( fn, "exposed" ):
        _wrapper.exposed= fn.exposed
    return _wrapper


def _check_method( obj, fn, predicate ):
    def _wrapper( *args, **kw ):
        errors= []
        if predicate.eval_with_object( current, errors ):
            return fn( *args, **kw )
        else:
            raise IdentityFailure( errors )
    _wrapper.exposed= True
    return _wrapper


class SecureResource(object):

    def __getattribute__( self, name ):
        from turbogears import controllers
        if name[:3]=="_cp" or name in ["require"]:
            return object.__getattribute__(self,name)
        try:
            value= object.__getattribute__(self,name)
            try:
                predicate= object.__getattribute__(self,"require")
            except AttributeError:
                predicate= turbogears.config.get( "identity.require", None )

            if predicate is None:
                raise AttributeError("SecureResource requires a require "
                                     "attribute either on the controller class "
                                     "itself or in the config file")

            errors= []
            if (isinstance( value, types.MethodType ) and
                hasattr( value, "exposed" )):
                return _check_method( self, value, predicate )
            if isinstance( value, controllers.Controller ):
                return SecureObject( value, predicate )
            # Some other property
            return value
        except IdentityException, e:
            errors= [str(e)]

        raise IdentityFailure( errors )

class SecureObject(object):
    def __init__( self, obj, require, exclude=[]):
        self._exclude = exclude
        self._object= obj
        self._require= require

    def __getattribute__( self, name ):
        from turbogears import controllers
        if name[:3]=="_cp" or name in ["_object","_require","_exclude"]:
            return object.__getattribute__(self,name)
        try:
            obj= object.__getattribute__( self, "_object" )
            value= getattr( obj, name )

            errors= []
            predicate= object.__getattribute__(self,"_require")
            if name in object.__getattribute__(self, "_exclude"):
                return value
            if (isinstance( value, types.MethodType ) and
                hasattr( value, "exposed" )):
                return _check_method( obj, value, predicate )
            if isinstance( value, controllers.Controller ):
                return SecureObject( value, predicate )
            # Some other property
            return value
        except IdentityException, e:
            errors= [str(e)]

        raise IdentityFailure( errors )
