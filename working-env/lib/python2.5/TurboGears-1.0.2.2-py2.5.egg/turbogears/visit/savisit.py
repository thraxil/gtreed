import turbogears
from datetime import *
from sqlalchemy import *
from sqlalchemy.ext.assignmapper import assign_mapper

from turbogears.visit.api import BaseVisitManager, Visit
from turbogears import config
from turbogears.database import bind_meta_data, metadata, session, get_engine
from turbogears.util import load_class

import logging
log = logging.getLogger("turbogears.identity.savisit")

visit_class = None

class SqlAlchemyVisitManager(BaseVisitManager):

    def __init__(self, timeout):
        global visit_class
        super(SqlAlchemyVisitManager,self).__init__(timeout)
        visit_class_path = config.get("visit.saprovider.model",
                               "turbogears.visit.savisit.TG_Visit")
        visit_class = load_class(visit_class_path)
        bind_meta_data()
        if visit_class is TG_Visit:
            assign_mapper(session.context, visit_class, visits_table)

    def create_model(self):
        '''
        Create the Visit table if it doesn't already exist
        '''
        visit_class.mapper.local_table.create(checkfirst=True)

    def new_visit_with_key(self, visit_key):
        visit = visit_class(visit_key=visit_key,
                        expiry=datetime.now()+self.timeout)
        session.save(visit)
        return Visit(visit_key, True)

    def visit_for_key(self, visit_key):
        '''
        Return the visit for this key or None if the visit doesn't exist or has
        expired.
        '''
        visit = visit_class.lookup_visit(visit_key)
        if not visit:
            return None
        now = datetime.now(visit.expiry.tzinfo)
        if visit.expiry < now:
            return None

        # Visit hasn't expired, extend it
        self.update_visit(visit_key, now+self.timeout)
        return Visit(visit_key, False)

    def update_queued_visits(self, queue):
        # TODO this should be made transactional
        table = visit_class.mapper.mapped_table
        # Now update each of the visits with the most recent expiry
        for visit_key,expiry in queue.items():
            log.info("updating visit (%s) to expire at %s", visit_key,
                      expiry)
            get_engine().execute(table.update(table.c.visit_key==visit_key,
                              values={'expiry': expiry}))

# The Visit table

visits_table = Table('tg_visit', metadata,
    Column('visit_key', String(40), primary_key=True),
    Column('created', DateTime, nullable=False, default=datetime.now),
    Column('expiry', DateTime)
)

class TG_Visit(object):

    def lookup_visit(cls, visit_key):
        return Visit.get(visit_key)
    lookup_visit = classmethod(lookup_visit)

