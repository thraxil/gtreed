from turbogears import database
from sqlobject import dbconnection
import cherrypy

hub = database.AutoConnectHub("sqlite:///:memory:")

def test_registry():
    "hubs appear in a registry"
    assert hub in database.hub_registry

def test_alwaysTransaction():
    "hub.getConnection always returns a Transaction"
    assert isinstance(hub.getConnection(), dbconnection.Transaction)
    database.end_all()
    assert not isinstance(hub.threadingLocal.connection, dbconnection.Transaction)

class DatabaseStandIn:
    committed = False
    rolled_back = False
    ended = False
    successful_called = False
    
    def __init__(self):
        self.old_commit = database.commit_all
        self.old_rollback = database.rollback_all
        self.old_end = database.end_all
        database.commit_all = self.commit
        database.end_all = self.end
        database.rollback_all = self.rollback
    
    def commit(self):
        self.committed = True
    
    def rollback(self):
        self.rolled_back = True
    
    def end(self):
        self.ended = True
        self.old_end()
        
    def successful(self):
        self.successful_called = True
    
    def failure(self):
        self.failure_called = True
        raise Warning("Oh my!")

    def redirect(self):
        self.redirect_called = True
        raise cherrypy.HTTPRedirect("/")

    def restore(self):
        database.commit_all = self.old_commit
        database.rollback_all = self.old_rollback
        database.end_all = self.end

def test_good_transaction():
    "successful runs automatically commit"
    dsi = DatabaseStandIn()
    database.run_with_transaction(dsi.successful)
    dsi.restore()
    assert dsi.successful_called
    assert dsi.committed
    assert dsi.ended

def test_bad_transaction():
    "failed runs automatically rollback"
    dsi = DatabaseStandIn()
    try:
        database.run_with_transaction(dsi.failure)
        dsi.restore()
        assert False, "exception should have been raised"
    except:
        pass
    dsi.restore()
    assert dsi.failure_called
    assert dsi.rolled_back
    assert dsi.ended

def test_redirection():
    "Redirects count as successful runs, not failures"
    dsi = DatabaseStandIn()
    try:
        database.run_with_transaction(dsi.redirect)
    except cherrypy.HTTPRedirect:
        pass
    dsi.restore()
    assert dsi.redirect_called
    assert dsi.committed
    assert dsi.ended

def test_so_to_dict():
    from sqlobject import IntCol
    from sqlobject.inheritance import InheritableSQLObject

    class Parent(InheritableSQLObject):
        _connection = hub
        a   = IntCol()

    class Child(Parent):
        _connection = hub
        b   = IntCol()

    Parent.createTable()
    Child.createTable()
    p =  Parent(a=1)
    c =  Child(a=1, b=2)

    p_dict = database.so_to_dict(p)
    assert p_dict['a'] == 1

    c_dict = database.so_to_dict(c)
    assert c_dict['a'] == 1
    assert c_dict['b'] == 2
    assert None == c_dict.get('childName', None)
    assert None == p_dict.get('childName', None)
