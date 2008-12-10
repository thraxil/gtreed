'''
@TODO: Laundry list of things yet to be done:
    * IdentityFilter should support HTTP Digest Auth
    * Also want to support Atom authentication (similar to digest)
'''
import md5
import sha
import threading

import cherrypy
import pkg_resources
import logging
log = logging.getLogger("turbogears.identity")

import turbogears
from turbogears.util import request_available
from turbogears.identity.exceptions import *

def create_default_provider():
    provider_plugin = turbogears.config.get( "identity.provider", "sqlobject" )
    plugins= pkg_resources.iter_entry_points( "turbogears.identity.provider",
                                              provider_plugin )

    log.debug( "Loading provider from plugin: %s", provider_plugin )

    for entrypoint in plugins:
        plugin= entrypoint.load()
        return plugin()

    raise IdentityConfigurationException( "IdentityProvider plugin missing: %s" %
                                          provider_plugin )


class IdentityWrapper(object):
    '''
    A wrapper class for the thread local data. This allows developers to access
    the current user information via turbogears.identity.current and get the
    identity for the current request.
    '''
    def identity(self):
        try:
            id= cherrypy.request.identity
        except AttributeError:
            id= None
        if not id:
            if not request_available():
                raise RequestRequiredException()
            raise IdentityManagementNotEnabledException()
        return id
        
    def __getattr__(self, name):
        '''
        return the named attribute of the global state
        '''
        identity= self.identity()
        if ("__str__"==name):
            return identity.__str__
        elif ("__repr__"==name):
            return identity.__repr__
        else:
            return getattr(identity, name)
        
    def __setattr__(self, name, value):
        '''
        stash a value in the global state
        '''
        identity= self.identity()
        setattr(identity,name,value)


class ProviderWrapper(object):
    
    def __getattr__(self, name):
        try:
            provider= cherrypy.request.identityProvider
        except AttributeError:
            try:
                provider = create_default_provider()
            except:
                provider= None
            
        if provider is None:
            if not request_available():
                raise RequestRequiredException()
            raise IdentityManagementNotEnabledException()
            
        return getattr(provider, name)

        
current= IdentityWrapper()
current_provider= ProviderWrapper()


def was_login_attempted():
    try:
        return cherrypy.request.identity_login_attempted
    except AttributeError:
        return False

                
def set_login_attempted( flag ):
    cherrypy.request.identity_login_attempted= flag
    
    
def set_current_identity(identity):
    cherrypy.request.identity = identity
    try:
        cherrypy.request.user_name = identity.user_name
    except AttributeError:
        cherrypy.request.user_name = None
    

def set_current_provider( provider ):
    cherrypy.request.identityProvider= provider

from turbogears.identity.conditions import *

def _encrypt_password(algorithm, password):
    """Hash the given password with the specified algorithm. Valid values
    for algorithm are 'md5' and 'sha1'. All other algorithm values will
    be essentially a no-op."""
    if isinstance(password, unicode):
        password_8bit = password.encode('UTF-8')
    else:
        password_8bit = password
    if "md5" == algorithm:
        hashed_password =  md5.new(password_8bit).hexdigest()
    elif "sha1" == algorithm:
        hashed_password = sha.new(password_8bit).hexdigest()
    else:
        hashed_password = password
    return hashed_password   

def encrypt_password(cleartext):
    # this next one ultimately needs to change to support SQLAlchemy
    return current_provider.encrypt_password(cleartext)

# declare what should be exported
__all__ = [ "IdentityManagementNotEnabledException",
            "IdentityConfigurationException",
            "IdentityFailure",
            "current", "current_provider",
            "set_current_identity", "set_current_provider",
            "set_identity_errors", "get_identity_errors",
            "was_login_attempted", "encrypt_password" ]
