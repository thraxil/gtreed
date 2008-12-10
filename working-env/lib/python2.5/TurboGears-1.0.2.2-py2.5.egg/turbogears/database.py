"""Provides convenient access to an SQLObject-managed database."""

import sys
import time
import logging

try:
    import sqlobject
    from sqlobject.dbconnection import ConnectionHub, Transaction, TheURIOpener
    from sqlobject.util.threadinglocal import local as threading_local
except ImportError:
    sqlobject = None

import cherrypy
from cherrypy.filters.basefilter import BaseFilter

import dispatch
from turbogears import config
from turbogears.util import remove_keys
from turbogears.genericfunctions import MultiorderGenericFunction

log = logging.getLogger("turbogears.database")

_engine = None

# Provide support for sqlalchemy
try:
    import sqlalchemy
    from sqlalchemy.ext import activemapper, sessioncontext

    def get_engine():
        "Retreives the engine based on the current configuration"
        global _engine
        if not _engine:
            alch_args = dict()
            for k, v in config.config.configMap["global"].items():
                if "sqlalchemy" in k:
                    alch_args[k.split(".")[-1]] = v
            dburi = alch_args.pop('dburi')
            if not dburi:
                raise KeyError("No sqlalchemy database config found!")
            _engine = sqlalchemy.create_engine(dburi, **alch_args)
            metadata.connect(_engine)
        elif not metadata.is_bound():
            metadata.connect(_engine)
        return _engine

    def create_session():
        "Creates a session with the appropriate engine"
        return sqlalchemy.create_session(bind_to=get_engine())

    metadata = activemapper.metadata
    session = activemapper.Objectstore(create_session)
    activemapper.objectstore = session

    def bind_meta_data():
        get_engine()

except ImportError:
    sqlalchemy = None


try:
    set
except NameError:
    from sets import Set as set

hub_registry = set()

# This dictionary stores the AutoConnectHubs used for each
# connection URI
_hubs = dict()


if sqlobject:
    def _mysql_timestamp_converter(raw):
        """Convert a MySQL TIMESTAMP to a floating point number representing
        the seconds since the Un*x Epoch. It uses custom code the input seems 
        to be the new (MySQL 4.1+) timestamp format, otherwise code from the 
        MySQLdb module is used."""
        if raw[4] == '-':
            return time.mktime(time.strptime(raw, '%Y-%m-%d %H:%M:%S'))
        else:
            import MySQLdb.converters
            return MySQLdb.converters.mysql_timestamp_converter(raw)
            

    class AutoConnectHub(ConnectionHub):
        """Connects to the database once per thread. The AutoConnectHub also
        provides convenient methods for managing transactions."""
        uri = None
        params = {}

        def __init__(self, uri=None, supports_transactions=True):
            if not uri:
                uri = config.get("sqlobject.dburi")
            self.uri = uri
            self.supports_transactions = supports_transactions
            hub_registry.add(self)
            ConnectionHub.__init__(self)

        def _is_interesting_version(self):
            "Return True only if version of MySQLdb <= 1.0."
            import MySQLdb
            module_version = MySQLdb.version_info[0:2]
            major = module_version[0]
            minor = module_version[1]
            # we can't use Decimal here because it is only available for Python 2.4
            return (major < 1 or (major == 1 and minor < 2))

        def _enable_timestamp_workaround(self, connection):
            """Enable a workaround for an incompatible timestamp format change 
            in MySQL 4.1 when using an old version of MySQLdb. See trac ticket 
            #1235 - http://trac.turbogears.org/ticket/1235 for details."""
            # precondition: connection is a MySQLConnection
            import MySQLdb
            import MySQLdb.converters
            if self._is_interesting_version():
                conversions = MySQLdb.converters.conversions.copy()
                conversions[MySQLdb.constants.FIELD_TYPE.TIMESTAMP] = \
                    _mysql_timestamp_converter
                # There is no method to use custom keywords when using 
                # "connectionForURI" in sqlobject so we have to insert the
                # conversions afterwards.
                connection.kw["conv"] = conversions

        def getConnection(self):
            try:
                conn = self.threadingLocal.connection
                return self.begin(conn)
            except AttributeError:
                if self.uri:
                    conn = sqlobject.connectionForURI(self.uri)
                    # the following line effectively turns off the DBAPI connection
                    # cache. We're already holding on to a connection per thread,
                    # and the cache causes problems with sqlite.
                    if self.uri.startswith("sqlite"):
                        TheURIOpener.cachedURIs = {}
                    elif self.uri.startswith("mysql") and \
                         config.get("turbogears.enable_mysql41_timestamp_workaround", False):
                        self._enable_timestamp_workaround(conn)
                    self.threadingLocal.connection = conn
                    return self.begin(conn)
                raise AttributeError(
                    "No connection has been defined for this thread "
                    "or process")

        def reset(self):
            """Used for testing purposes. This drops all of the connections
            that are being held."""
            self.threadingLocal = threading_local()

        def begin(self, conn=None):
            "Starts a transaction."
            if not self.supports_transactions:
                return conn
            if not conn:
                conn = self.getConnection()
            if isinstance(conn, Transaction):
                if conn._obsolete:
                    conn.begin()
                return conn
            self.threadingLocal.old_conn = conn
            trans = conn.transaction()
            self.threadingLocal.connection = trans
            return trans

        def commit(self):
            "Commits the current transaction."
            if not self.supports_transactions:
                return
            try:
                conn = self.threadingLocal.connection
            except AttributeError:
                return
            if isinstance(conn, Transaction):
                self.threadingLocal.connection.commit()

        def rollback(self):
            "Rolls back the current transaction."
            if not self.supports_transactions:
                return
            try:
                conn = self.threadingLocal.connection
            except AttributeError:
                return
            if isinstance(conn, Transaction) and not conn._obsolete:
                self.threadingLocal.connection.rollback()

        def end(self):
            "Ends the transaction, returning to a standard connection."
            if not self.supports_transactions:
                return
            try:
                conn = self.threadingLocal.connection
            except AttributeError:
                return
            if not isinstance(conn, Transaction):
                return
            if not conn._obsolete:
                conn.rollback()
            self.threadingLocal.connection = self.threadingLocal.old_conn
            del self.threadingLocal.old_conn
            self.threadingLocal.connection.cache.clear()

    class PackageHub(object):
        """Transparently proxies to an AutoConnectHub for the URI
        that is appropriate for this package. A package URI is
        configured via "packagename.dburi" in the global CherryPy
        settings. If there is no package DB URI configured, the
        default (provided by "sqlobject.dburi") is used.

        The hub is not instantiated until an attempt is made to
        use the database.
        """
        def __init__(self, packagename):
            self.packagename = packagename
            self.hub = None

        def __get__(self, obj, type):
            if not self.hub:
                self.set_hub()
            return self.hub.__get__(obj, type)

        def __set__(self, obj, type):
            if not self.hub:
                self.set_hub()
            return self.hub.__set__(obj, type)

        def __getattr__(self, name):
            if not self.hub:
                self.set_hub()
            return getattr(self.hub, name)

        def set_hub(self):
            dburi = config.get("%s.dburi" % self.packagename, None)
            if not dburi:
                dburi = config.get("sqlobject.dburi", None)
            if not dburi:
                raise KeyError, "No database configuration found!"
            if dburi.startswith("notrans_"):
                dburi = dburi[8:]
                trans = False
            else:
                trans = True
            hub = _hubs.get(dburi, None)
            if not hub:
                hub = AutoConnectHub(dburi, supports_transactions=trans)
                _hubs[dburi] = hub
            self.hub = hub
else:
    class AutoConnectHub(object):
        pass
    
    class PackageHub(object):
        pass

def set_db_uri(dburi, package=None):
    """Sets the database URI to use either globally or for a specific
    package. Note that once the database is accessed, calling
    setDBUri will have no effect.

    @param dburi: database URI to use
    @param package: package name this applies to, or None to set the default.
    """
    if package:
        config.update({'global':
            {"%s.dburi" % package : dburi}
        })
    else:
        config.update({'global':
            {"sqlobject.dburi" : dburi}
        })

def commit_all():
    "Commits the Transactions in all registered hubs (for this thread)"
    for hub in hub_registry:
        hub.commit()

def rollback_all():
    "Rolls back the Transactions in all registered hubs (for this thread)"
    for hub in hub_registry:
        hub.rollback()

def end_all():
    "Ends the Transactions in all registered hubs (for this thread)"
    for hub in hub_registry:
        hub.end()

[dispatch.generic(MultiorderGenericFunction)]
def run_with_transaction(func, *args, **kw):
    pass

def _use_sa(args=None):
    # check to see if sqlalchemy has been imported and configured
    return _engine is not None

[run_with_transaction.when("not _use_sa(args)")] # include "args" to avoid call being pre-cached
def so_rwt(func, *args, **kw):
    log.debug("Starting SQLObject transaction")
    try:
        try:
            retval = func(*args, **kw)
            commit_all()
            return retval
        except cherrypy.HTTPRedirect:
            commit_all()
            raise
        except cherrypy.InternalRedirect:
            commit_all()
            raise
        except:
            # No need to "rollback" the sqlalchemy unit of work, because nothing
            # has hit the db yet.
            rollback_all()
            raise
    finally:
        end_all()

def dispatch_exception(exception,args, kw):
    # errorhandling import here to avoid circular imports
    from turbogears.errorhandling import dispatch_error
    # Keep in mind func is not the real func but _expose
    real_func, accept, allow_json, controller = args[:4]
    args = args[4:]
    exc_type, exc_value, exc_trace = sys.exc_info()
    remove_keys(kw, ("tg_source", "tg_errors", "tg_exceptions"))
    try:
        output = dispatch_error(
            controller, real_func, None, exception, *args, **kw)
    except dispatch.NoApplicableMethods:
        raise exc_type, exc_value, exc_trace
    else:
        del exc_trace
        return output

[run_with_transaction.when("_use_sa(args)")] # include "args" to avoid call being pre-cached
def sa_rwt(func, *args, **kw):
    log.debug("New SA transaction")
    req = cherrypy.request
    req.sa_transaction = session.create_transaction()
    try:
        retval = func(*args, **kw)
        req.sa_transaction.commit()
    except (cherrypy.HTTPRedirect,cherrypy.InternalRedirect):
        try:
            req.sa_transaction.commit()
        except Exception,e:
            retval = dispatch_exception(e,args,kw)
        else:
            raise
    except Exception, e:
        req.sa_transaction.rollback()
        retval = dispatch_exception(e,args,kw)
    return retval

def so_to_dict(sqlobj):
    "Converts SQLObject to a dictionary based on columns"
    d = {}
    if sqlobj == None:
        # stops recursion
        return d
    for name in sqlobj.sqlmeta.columns.keys():
        d[name] = getattr(sqlobj, name)
    "id must be added explicitly"
    d["id"] = sqlobj.id
    if sqlobj._inheritable:
        d.update(so_to_dict(sqlobj._parent))
        d.pop('childName')
    return d

def so_columns(sqlclass, columns=None):
    """Returns a dict with all columns from a SQLObject including those from
    InheritableSO's bases"""
    if columns is None:
        columns = {}
    columns.update(filter(lambda i: i[0] != 'childName', 
                          sqlclass.sqlmeta.columns.items()))
    if sqlclass._inheritable:
        so_columns(sqlclass.__base__, columns)
    return columns

def so_joins(sqlclass, joins=None):
    """Returns a list with all joins from a SQLObject including those from
    InheritableSO's bases"""
    if joins is None:
        joins = []
    joins.extend(sqlclass.sqlmeta.joins)
    if sqlclass._inheritable:
        so_joins(sqlclass.__base__, joins)
    return joins

class EndTransactionsFilter(BaseFilter):
    def on_end_resource(self):
        if _use_sa():
            session.clear()
        end_all()

__all__ = ["PackageHub", "AutoConnectHub", "set_db_uri",
           "commit_all", "rollback_all", "end_all", "so_to_dict",
           "so_columns", "so_joins", "EndTransactionsFilter"]

if sqlalchemy:
    __all__.extend(["metadata", "session", "bind_meta_data"])
