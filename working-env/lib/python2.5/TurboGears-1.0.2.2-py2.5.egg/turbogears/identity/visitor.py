import cherrypy
import sha
import datetime
import time
import base64

try:
    from sqlobject import *
except ImportError:
    pass

import turbogears
from turbogears.identity import create_default_provider
from turbogears.identity import set_current_identity
from turbogears.identity import set_current_provider
from turbogears.identity import set_login_attempted

from turbogears.identity.exceptions import *

from turbogears import visit

import logging
log = logging.getLogger("turbogears.identity")

# Interface for the TurboGears extension
def start_extension():
    # Bail out if the application hasn't enabled this extension
    if not turbogears.config.get( "identity.on", False ):
        return
    # Identity requires that Visit tracking be enabled
    if not turbogears.config.get( "visit.on", False ):
        raise IdentityConfigurationException( "Visit tracking must be enabled (visit.on)" )
        
    log.info( "Identity starting" )
    # Temporary until tg-admin can call create_extension_model
    create_extension_model()
    # Register the plugin for the Visit Tracking framework
    visit.enable_visit_plugin( IdentityVisitPlugin() )

    
def shutdown_extension():
    # Bail out if the application hasn't enabled this extension
    if not turbogears.config.get( "identity.on", False ):
        return
    log.info( "Identity shutting down" )
    pass


def create_extension_model():
    provider= create_default_provider()
    provider.create_provider_model()
    

class IdentityVisitPlugin(object):
    def __init__(self):
        log.info( "Identity visit plugin initialised" )
        get=turbogears.config.get

        self.provider= create_default_provider()
                    
        # When retrieving identity information from the form, use the following
        # form field names. These fields will be removed from the post data to
        # prevent the controller from receiving unexpected fields.
        self.user_name_field= get( "identity.form.user_name", "user_name" )
        self.password_field= get( "identity.form.password", "password" )
        self.submit_button_name= get( "identity.form.submit", "login" )
        
        # Sources for identity information and the order in which they should be
        # checked. These terms are mapped to methods by prepending
        # "identity_from_".
        sources= get( "identity.source", "form,http_auth,visit" ).split(",")
        self.identity_sources= []
        for s in sources:
            try:
                source_method= getattr( self, "identity_from_" + s )
            except AttributeError:
                raise IdentityConfigurationException( "Invalid identity source: %s" % s )
            self.identity_sources.append( source_method )

    def identity_from_request(self, visit_key):
        '''
        Retrieve identity information from the HTTP request. Checks first for
        form fields defining the identity then for a cookie. If no identity
        is found, returns an anonymous identity.
        '''
        identity= None
        log.debug( "Retrieving identity for visit: %s", visit_key )
        for source in self.identity_sources:
            identity= source(visit_key)
            if identity:
                return identity

        log.debug( "No identity found" )
        # No source reported an identity
        identity= self.provider.anonymous_identity()
        return identity
    
    def decode_basic_credentials( self, credentials ):
        '''
        Decode base64 user_name:password credentials used in Basic Auth. Returned
        with username in element 0 and password in element 1.
        '''
        return base64.decodestring( credentials.strip() ).split( ":" )
        
    def identity_from_http_auth( self, visit_key ):
        '''
        Only basic auth is handled at the moment.
        '''
        try:
            authorisation= cherrypy.request.headers['Authorization']
        except KeyError:
            return None
        (authScheme,schemeData)= authorisation.split( " ", 1 )
        # Only basic is handled at the moment
        if "basic" != authScheme.lower():
            log.error( "HTTP Auth is not basic" )
            return None
        # decode credentials
        (user_name,password)=self.decode_basic_credentials( schemeData )
        set_login_attempted( True )
        return self.provider.validate_identity( user_name, password, visit_key )

    def identity_from_visit( self, visit_key ):
        return self.provider.load_identity( visit_key )
    
    def identity_from_form( self, visit_key ):
        '''
        Inspect the form to pull out identity information. Must have fields for
        user name, password, and a login submit button.
        
        Returns an identity dictionary or none if the form contained no identity
        information or the information was incorrect.
        '''
        params= cherrypy.request.params
        # only try to process credentials for login forms
        if params.has_key(self.submit_button_name):
            try:
                # form data contains login credentials
                user_name = params.pop(self.user_name_field)
                pw = params.pop(self.password_field)
                # just lose the submit button to prevent passing to final controller
                submit= params.pop(self.submit_button_name, None)
                submit_x = params.pop("%s.x" % self.submit_button_name, None)
                submit_y = params.pop("%s.y" % self.submit_button_name, None)
                set_login_attempted( True )
                identity= self.provider.validate_identity( user_name, pw, visit_key )
                if identity is None:
                    log.warning( "The credentials specified weren't valid" )
                    return None

                return identity
            except KeyError:
                return None
        else:
            return None
        
    def record_request( self, visit ):
        # default to keeping the identity filter off
        if not turbogears.config.get( "identity.on", True ):
            log.debug( "Identity is not enabled. Setting current identity to None" )
            set_current_identity( None )
            return

        try:
            identity= self.identity_from_request(visit.key)
        except IdentityException, e:
            log.exception( "Caught exception while getting identity from request" )
            errors= [str(e)]
            raise IdentityFailure( errors )
        
        log.debug( "Identity is available..." )
        # stash the user in the thread data for this request
        set_current_identity( identity )
        set_current_provider( self.provider )


