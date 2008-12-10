from datetime import timedelta, datetime

from sqlobject import *
from sqlobject.sqlbuilder import *

from turbogears.visit.api import BaseVisitManager, Visit
from turbogears.database import PackageHub
from turbogears import config
from turbogears.util import load_class

hub = PackageHub("turbogears.visit")
__connection__ = hub

import logging

log = logging.getLogger("turbogears.visit.sovisit")

visit_class = None

class SqlObjectVisitManager(BaseVisitManager):
    def __init__(self, timeout):
        global visit_class
        visit_class_path = config.get("visit.soprovider.model", 
            "turbogears.visit.sovisit.TG_Visit")
        visit_class = load_class(visit_class_path)
        if visit_class:
            log.info("Succesfully loaded \"%s\"" % visit_class_path)
        super(SqlObjectVisitManager,self).__init__( timeout )

    def create_model(self):
        try:
            # Create the Visit table if it doesn't already exist (idea from CatWalk)
            hub.begin()
            visit_class.createTable(ifNotExists=True)
            hub.commit()
            hub.end()
        except KeyError:
            # No database configured...
            log.info( "No database is configured: Visit Tracking is disabled." )
            return

    def new_visit_with_key(self, visit_key):
        hub.begin()
        visit= visit_class( visit_key=visit_key, expiry=datetime.now()+self.timeout )
        hub.commit()
        hub.end()
        return Visit( visit_key, True )

    def visit_for_key(self, visit_key):
        '''
        Return the visit for this key or None if the visit doesn't exist or has
        expired.
        '''
        visit= visit_class.lookup_visit( visit_key )
        now= datetime.now()
        if not visit or visit.expiry < now:
            return None
        # Visit hasn't expired, extend it
        self.update_visit( visit_key, now+self.timeout )
        return Visit( visit_key, False )

    def update_queued_visits(self, queue):
        if hub is None: # if VisitManager extension wasn't shutted down cleanly
            return
        hub.begin()
        try:
            conn= hub.getConnection()
            try:
                # Now update each of the visits with the most recent expiry
                for visit_key,expiry in queue.items():
                    u= Update( visit_class.q, {visit_class.q.expiry.fieldName:expiry},
                               where=(visit_class.q.visit_key==visit_key) )
                    conn.query( conn.sqlrepr(u) )
                hub.commit()
            except:
                hub.rollback()
                raise
        finally:
            hub.end()

class TG_Visit(SQLObject):
    class sqlmeta:
        table="tg_visit"

    visit_key= StringCol( length=40, alternateID=True,
                          alternateMethodName="by_visit_key" )
    created= DateTimeCol( default=datetime.now )
    expiry= DateTimeCol()

    def lookup_visit( cls, visit_key ):
        try:
            return cls.by_visit_key( visit_key )
        except SQLObjectNotFound:
            return None
    lookup_visit= classmethod(lookup_visit)
