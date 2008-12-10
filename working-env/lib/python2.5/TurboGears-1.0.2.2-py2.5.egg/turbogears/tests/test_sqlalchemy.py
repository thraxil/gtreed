"Tests for SQLAlchemy support"

import cherrypy

from sqlalchemy import *
from sqlalchemy.ext.activemapper import ActiveMapper, column, one_to_many

from turbogears import config, redirect, expose, database, errorhandling
from turbogears.testutil import create_request, capture_log, print_log, \
                                sqlalchemy_cleanup
from turbogears.database import session, metadata, bind_meta_data
from turbogears.controllers import RootController

config.update({"sqlalchemy.dburi" : "sqlite:///:memory:"})

bind_meta_data()

metadata.engine.echo = True

users_table = Table("users", metadata,
    Column("user_id", Integer, primary_key=True),
    Column("user_name", String(40)),
    Column("password", String(10))
    )

class User(object):
    def __repr__(self):
        return "(User %s, password %s)" % (self.user_name, self.password)

usermapper = mapper(User, users_table)

class Person(ActiveMapper):
    class mapping:
        id = column(Integer, primary_key=True)
        name = column(String(40))
        addresses = one_to_many("Address")
    
class Address(ActiveMapper):
    class mapping:
        id = column(Integer, primary_key=True)
        address = column(String(40))
        city = column(String(40))
        person_id = column(Integer, foreign_key=ForeignKey("person.id"))

def setup_module():
    metadata.create_all()

def teardown_module():
    sqlalchemy_cleanup()

def test_query_in_session():
    i = users_table.insert()
    i.execute(user_name="globbo", password="thegreat!")
    query = session.query(User)
    globbo = query.select_by(user_name="globbo")[0]
    assert globbo.password == "thegreat!"
    users_table.delete().execute()

def test_create_and_query():
    i = users_table.insert()
    i.execute(user_name="globbo", password="thegreat!")
    s = users_table.select()
    r = s.execute()
    assert len(r.fetchall()) == 1
    users_table.delete().execute()

def test_active_mapper():
    p = Person(name="Ford Prefect")
    a = Address(address="1 West Guildford", city="Betelgeuse")
    p.addresses.append(a)
    session.flush()
    session.clear()
    q = session.query(Person)
    ford = q.select_by(name="Ford Prefect")[0]
    assert ford is not p
    assert len(ford.addresses) == 1

class MyRoot(RootController):
    def no_error(self, name):
        p = Person(name=name)
        raise redirect("/confirm")
    no_error = expose()(no_error)

    def e_handler(self, tg_exceptions=None):
        cherrypy.response.code = 501
        return "An exception ocurred: %r (%s)" % ((tg_exceptions,)*2)

    def create_person(self, **kw):
        id = kw.pop('id', None)
        if id is not None:
            kw['id'] = int(id)
        p = Person(**kw)
        return "No exceptions ocurred"
    create_person = expose()(create_person)
    create_person = errorhandling.exception_handler(e_handler)(create_person)

def test_implicit_trans_no_error():
    capture_log("turbogears.database")
    cherrypy.root = MyRoot()
    create_request("/no_error?name=A.%20Dent")
    print_log()
    session.clear()
    q = session.query(Person)
    arthur = q.select_by(name="A. Dent")[0]

def test_raise_sa_exception():
    capture_log("turbogears.database")
    cherrypy.root = MyRoot()
    create_request("/create_person?id=20")
    output = cherrypy.response.body[0]
    print output
    assert "No exceptions" in output

    create_request("/create_person?id=20")
    output = cherrypy.response.body[0]
    print output
    
    # Note that the specific DB2API may be either OperationalError or
    # IntegrityError depending on what version of sqlite and pysqlite
    # is used.
    assert "SQLError" in output
    assert cherrypy.response.code == 501

    
