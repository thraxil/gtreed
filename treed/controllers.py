import logging

import cherrypy

import turbogears
from turbogears import controllers, expose, validate, redirect
from turbogears import identity

from treed.model import User,Item,ListItem,AND,OR,LIKE
from treed import json

log = logging.getLogger("treed.controllers")

def referer():
    return cherrypy.request.headerMap.get('Referer','')


class Content:
    @turbogears.expose()
    @identity.require(identity.not_anonymous())
    def default(self, *vpath, **params):
        if len(vpath) == 1:
            identifier = vpath[0]
            action = self.show
        elif len(vpath) == 2:
            identifier, verb = vpath
            verb = verb.replace('.', '_')
            action = getattr(self, verb, None)
            if not action:
                raise cherrypy.NotFound
            if not action.exposed:
                raise cherrypy.NotFound
        else:
            raise cherrypy.NotFound
        items = self.query(identifier)
        if items.count() == 0:
            raise cherrypy.NotFound
        else:
            return action(items[0], **params)

class ItemController(controllers.Controller,Content):
    def query(self,id):
        return Item.select(Item.q.id==int(id))

    @expose(template="treed.templates.item")
    def show(self,item):
        return dict(item=item)

    @expose(template="treed.templates.item_edit")
    def edit_form(self,item):
        return dict(item=item)

    @expose()
    def edit(self,item,title="",status="",description="",**kwargs):
        title = title.strip()
        if title != "":
            item.title = title
        else:
            turbogears.flash("invalid title")
        if status in ["OPEN","CLOSED"]:
            item.status = status
        else:
            turbogears.flash("invalid status")
        item.description = description
        turbogears.flash("changes saved")
        raise redirect("/item/%d/" % item.id)


    @expose()
    def add(self,item,title="",description="",**kwargs):
        title = title.strip()
        if title != "":
            i = Item(owner=item.owner,assigned_to=item.assigned_to,
                     title=title,description=description,status="OPEN")
            item.add_child(i)
        else:
            turbogears.flash("empty title. did not add item")
        raise redirect(referer())

    @expose(format="json")
    def add_json(self,item,title="",description="",**kwargs):
        title = title.strip()
        if title != "":
            i = Item(owner=item.owner,assigned_to=item.assigned_to,
                     title=title,description=description,status="OPEN")
            item.add_child(i)
            return dict(id=i.id,title=i.title,parent_id=item.id)
        else:
            return dict()


    @expose(format="json")
    def subitems(self,item):
        return dict(subitems=[i.as_dict() for i in item.get_open_children()])

    @expose()
    def detach(self,item,parent_id):
        parent = Item.get(parent_id)
        parent.remove_child(item)
        raise redirect("/item/%d/" % item.id)

    @expose()
    def close(self,item):
        success = item.close()
        if success:
            raise redirect(referer())
        else:
            return "cannot close an item with open sub-items"

    @expose()
    def reopen(self,item):
        item.status = 'OPEN'
        raise redirect(referer())

    @expose()
    def delete(self,item):
        item.destroySelf()
        raise redirect(referer())

    @expose()
    def reparent(self,item,item_id):
        iids = []
        if type(item_id) != type([]):
            iids = [item_id]
        else:
            iids = item_id

        for iid in iids:
            i = Item.get(iid)
            i.set_parent(item)
        raise redirect(referer())

    @expose()
    def add_child(self,item,item_id):
        item.add_child(Item.get(item_id))
        raise redirect(referer())

    @expose()
    def reorder_children(self,item,**kwargs):
        for k in kwargs.keys():
            if k[:5] == "item_":
                item_id = k[5:]
                i = Item.get(item_id)
                li = ListItem.select(AND(ListItem.q.parentID == item.id,
                                         ListItem.q.childID == i.id))[0]
                li.cardinality = int(kwargs[k])
        item.normalize_childrens_cardinality()
        return """<?xml version="1.0"?><done/>"""

class AtomController(controllers.Controller):
    @expose(template="treed.templates.item_atom",
            content_type="application/atom+xml",
            format='xml')
    def default(self,item_id):
        return dict(item=Item.get(item_id))

class Root(controllers.RootController):
    item = ItemController()
    atom = AtomController()
    @expose()
    def index(self):
        raise redirect("/INBOX")

    @expose(template="treed.templates.login")
    def login(self, forward_url=None, previous_url=None, *args, **kw):

        if not identity.current.anonymous \
            and identity.was_login_attempted() \
            and not identity.get_identity_errors():
            raise redirect(forward_url)

        forward_url=None
        previous_url= cherrypy.request.path

        if identity.was_login_attempted():
            msg=_("The credentials you supplied were not correct or "
                   "did not grant access to this resource.")
        elif identity.get_identity_errors():
            msg=_("You must provide your credentials before accessing "
                   "this resource.")
        else:
            msg=_("Please log in.")
            forward_url= cherrypy.request.headers.get("Referer", "/")
        cherrypy.response.status=403
        return dict(message=msg, previous_url=previous_url, logging_in=True,
                    original_parameters=cherrypy.request.params,
                    forward_url=forward_url)

    @expose(template="treed.templates.signup")
    def signup_form(self):
        return dict()

    @expose(template="treed.templates.signup")
    def signup(self,username,password,pass2,fullname,email):
        
        if password != pass2:
            return dict(msg=_("Passwords do not match"))
                        
        u = User(user_name=username,display_name=fullname,
                 email_address=email,password=password)
        u.create_initial_items()
        turbogears.flash("account created. please login")
        raise redirect("/")

    @expose()
    def logout(self):
        identity.current.logout()
        raise redirect("/")



    @expose(template="treed.templates.item")
    @identity.require(identity.not_anonymous())
    def INBOX(self,*args,**kwargs):
        i = turbogears.identity.current.user.INBOX()
        raise redirect("/item/%d/" % i.id)

    @expose(template="treed.templates.search")
    @identity.require(identity.not_anonymous())
    def search(self,q=""):
        q = q.strip()
        if q == "":
            return dict(items=[],item=None,q=q)
        else:
            items = list(Item.select(AND(OR(LIKE(Item.q.title,"%%" + q + "%%"),
                                            LIKE(Item.q.description,"%%" + q + "%%")),
                                         Item.q.ownerID==turbogears.identity.current.user.id
                                         )))
            return dict(items=items,
                        item=None,
                        q=q)




