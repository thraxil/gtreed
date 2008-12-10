import cherrypy
import turbogears

def set_identity_errors( errors ):
    if isinstance( errors, basestring ):
        errors= [errors];
    cherrypy.request.identity_errors= list(errors)

def get_identity_errors():
    return getattr( cherrypy.request, "identity_errors", [] )


class IdentityException(Exception):
    '''
    Base class for all Identity exceptions.
    '''
    pass

class RequestRequiredException(IdentityException):
    '''
    An attempt was made to use a facility of Identity that requires the
    presence of an HTTP request.
    '''

    def __str__(self):
        return "An attempt was made to use a facility of the TurboGears " \
               "Identity Management framework that relies on an HTTP request "\
               "outside of a request."

        
class IdentityManagementNotEnabledException(IdentityException):
    """ User forgot to enable Identity management """
    
    def __str__(self):
        return "An attempt was made to use a facility of the TurboGears " \
               "Identity Management framework but identity management hasn't " \
               "been enabled in the config file [via identity.on]."
    
    
class IdentityConfigurationException(IdentityException):
    '''
    Exception thrown when the Identity management system hasn't been configured
    correctly. Mostly, when failure_url is not specified.
    '''
    args = ()
    def __init__(self, message):
        self.message= message
        
    def __str__(self):
        return self.message

class IdentityFailure(cherrypy.InternalRedirect, IdentityException):
    '''
    Exception thrown when an access control check fails.
    '''
    def __init__(self, errors):
        '''
        Set up the identity errors on the request and get the URL from the config
        '''
        set_identity_errors( errors )
        url= turbogears.config.get( "identity.failure_url", None )
        if url is None:
            msg= "Missing URL for identity failure"
            raise IdentityConfigurationException( msg )
        if callable(url):
            url= url( errors )
        # super(IdentityFailure,self).__init__(url) seems to not work...?
        cherrypy.InternalRedirect.__init__(self, url)
