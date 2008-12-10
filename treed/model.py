from datetime import datetime, timedelta
from sqlobject import *
from turbogears import identity 
from turbogears.database import PackageHub

hub = PackageHub("treed")
__connection__ = hub

soClasses=['User','Group','Visit','VisitIdentity','Item','ListItem',
           'Permission']

class Visit(SQLObject):
    class sqlmeta:
        table = "visit"

    visit_key = StringCol(length=40, alternateID=True,
                          alternateMethodName="by_visit_key")
    created = DateTimeCol(default=datetime.now)
    expiry = DateTimeCol()

    def lookup_visit(cls, visit_key):
        try:
            return cls.by_visit_key(visit_key)
        except SQLObjectNotFound:
            return None
    lookup_visit = classmethod(lookup_visit)

class VisitIdentity(SQLObject):
    visit_key = StringCol(length=40, alternateID=True,
                          alternateMethodName="by_visit_key")
    user_id = IntCol()


class Group(SQLObject):
    """
    An ultra-simple group definition.
    """

    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    class sqlmeta:
        table = "tg_group"

    group_name = UnicodeCol(length=16, alternateID=True,
                            alternateMethodName="by_group_name")
    display_name = UnicodeCol(length=255)
    created = DateTimeCol(default=datetime.now)

    # collection of all users belonging to this group
    users = RelatedJoin("User", intermediateTable="user_group",
                        joinColumn="group_id", otherColumn="user_id")

    # collection of all permissions for this group
    permissions = RelatedJoin("Permission", joinColumn="group_id", 
                              intermediateTable="group_permission",
                              otherColumn="permission_id")


class User(SQLObject):
    """
    Reasonably basic User definition. Probably would want additional attributes.
    """
    # names like "Group", "Order" and "User" are reserved words in SQL
    # so we set the name to something safe for SQL
    class sqlmeta:
        table = "tg_user"

    user_name = UnicodeCol(length=16, alternateID=True,
                           alternateMethodName="by_user_name")
    email_address = UnicodeCol(length=255, alternateID=True,
                               alternateMethodName="by_email_address")
    display_name = UnicodeCol(length=255)
    password = UnicodeCol(length=40)
    created = DateTimeCol(default=datetime.now)

    # groups this user belongs to
    groups = RelatedJoin("Group", intermediateTable="user_group",
                         joinColumn="user_id", otherColumn="group_id")

    owned_items = MultipleJoin('Item',joinColumn='owner_user_id')
    assigned_items = MultipleJoin('Item',joinColumn='assigned_to_user_id')

    def _get_permissions(self):
        perms = set()
        for g in self.groups:
            perms = perms | set(g.permissions)
        return perms

    def _set_password(self, cleartext_password):
        "Runs cleartext_password through the hash algorithm before saving."
        hash = identity.encrypt_password(cleartext_password)
        self._SO_set_password(hash)

    def set_password_raw(self, password):
        "Saves the password as-is to the database."
        self._SO_set_password(password)

    def create_initial_items(self):
        i = Item(owner=self,assigned_to=self,title="INBOX",description="INBOX")
        p = Item(owner=self,assigned_to=self,title="Projects")
        s = Item(owner=self,assigned_to=self,title="Someday/Maybe")
        t = Item(owner=self,assigned_to=self,title="Ticklers")
        o = Item(owner=self,assigned_to=self,title="Outbox",description="Items assigned to other people")
        h = Item(owner=self,assigned_to=self,title="@Home")
        w = Item(owner=self,assigned_to=self,title="@Work")
        m = Item(owner=self,assigned_to=self,title="Months")
        t.add_child(m)
        d = Item(owner=self,assigned_to=self,title="Days")
        t.add_child(d)
        dow = Item(owner=self,assigned_to=self,title="Day of Week")
        t.add_child(dow)
        tomorrow = Item(owner=self,assigned_to=self,title="Tomorrow")
        t.add_child(tomorrow)
        next_week = Item(owner=self,assigned_to=self,title="Next Week")
        t.add_child(next_week)
        next_month = Item(owner=self,assigned_to=self,title="Next Month")
        t.add_child(next_month)
        next_year = Item(owner=self,assigned_to=self,title="Next Year")
        t.add_child(next_year)
        for month in ["January","February","March","April","May","June","July",
                      "August","September","October","November","December"]:
            m.add_child(Item(owner=self,assigned_to=self,title=month,description="Tickler for %s" % month))
        for day in range(1,32):
            d.add_child(Item(owner=self,assigned_to=self,title=str(day),description="Tickler for %d" % day))
        for day in ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]:
            dow.add_child(Item(owner=self,assigned_to=self,title=day,description="Tickler for %s" % day))

    def INBOX(self):
        """ return the item corresponding to this user's INBOX """
        # TODO: should probably memoize this
        return self.get_named_item("INBOX")

    def get_named_item(self,title):
        """ return a named item belonging to the user. for INBOX, ticklers, etc. """
        # TODO: create if doesn't exist?
        return Item.select(AND(Item.q.ownerID == self.id, Item.q.title == title))[0]

    def top_level_items(self):
        """ return a list of all the items assigned to this user without any parents """
        # TODO: should probably be cached/memoized. At least optimized.
        # this is the simplest way to do this but is very inefficient.
        all_items = self.assigned_items
        top_level = []
        all_items.sort(lambda x, y: cmp(x.id,y.id))
        for i in all_items:
            if len(i.parents) == 0 and i.status == 'OPEN':
                top_level.append(i)
        return top_level

    def tickle(self):
        """ move items from the appropriate tickler folders
        into the user's INBOX """
        now   = datetime.now()
        inbox = self.INBOX()
        day   = now.day
        
        def tickle_item(parent,inbox):
            for child in parent.get_open_children():
                parent.remove_child(child)
                inbox.add_child(child)

        tickle_item(self.get_named_item("Tomorrow"),inbox)
        if day == 1:
            # first of the month, so we bring in the month items
            month = ["January","February","March","April","May","June","July",
                     "August","September","October","November","December"][now.month - 1]
            mi = self.get_named_item(month)
            tickle_item(mi,inbox)
            tickle_item(self.get_named_item("next month"),inbox)
            
            # check for edge cases
            one_day = timedelta(1)
            yesterday = now - one_day
            for d in range(yesterday.day + 1, 32):
                # move stuff from the 29th, 30th, and/or 31st since last month didn't have it
                tickle_item(self.get_named_item(str(d)),inbox)
            if month == "January":
                tickle_item(self.get_named_item("Next Year"),inbox)

        dow = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"][now.isoweekday() - 1]
        dowi = self.get_named_item(dow)
        tickle_item(dowi,inbox)
        if dow == "Monday":
            tickle_item(self.get_named_item("Next Week"),inbox)
        tickle_item(self.get_named_item(str(day)),inbox)

class Permission(SQLObject):
    permission_name = UnicodeCol(length=16, alternateID=True,
                                 alternateMethodName="by_permission_name")
    description = UnicodeCol(length=255)

    groups = RelatedJoin("Group",
                        intermediateTable="group_permission",
                         joinColumn="permission_id", 
                         otherColumn="group_id")

class Item(SQLObject):
    title       = UnicodeCol(default=u"")
    description = UnicodeCol(default=u"")
    owner       = ForeignKey('User',cascade=True,dbName='owner_user_id')
    assigned_to = ForeignKey('User',cascade=True,dbName='assigned_to_user_id')
    status      = UnicodeCol(default=u"OPEN")
    parents     = MultipleJoin('ListItem',joinColumn='child_item_id')
    children    = MultipleJoin('ListItem',joinColumn='parent_item_id',
                               orderBy='cardinality')
    added       = DateTimeCol(default=datetime.now)
    modified    = DateTimeCol(default=datetime.now)

    def as_dict(self):
        return dict(id=self.id,title=self.title,description=self.description,status=self.status,
                    added=self.added,modified=self.modified,children=[i.as_dict() for i in self.get_open_children()])


    def add_child(self,item):
        self.normalize_childrens_cardinality()
        li = ListItem(parent=self,child=item,cardinality=len(self.children) + 1)
        self.touch()

    def normalize_childrens_cardinality(self):
        """ go through the children and make the cardinalitys increase by 1"""
        card = 1
        for c in self.children:
            c.cardinality = card
            card += 1

    def get_children(self):
        """ get the actual Item's for the children list """
        return [li.child for li in list(self.children)]


    def get_open_children(self):
        return [li.child for li in list(self.children) if li.child.status == 'OPEN']

    def get_closed_children(self):
        return [li.child for li in list(self.children) if li.child.status == 'CLOSED']


    def get_parents(self):
        """ get the actual Item's for the parents list """
        return [li.parent for li in list(self.parents)]

    def remove_child(self,child):
        li = ListItem.select(AND(ListItem.q.parentID == self.id,
                                 ListItem.q.childID == child.id))[0]
        li.destroySelf()
        self.normalize_childrens_cardinality()
        self.touch()

    def close(self):
        children = self.get_children()
        if len(children) == 0:
            self.status = 'CLOSED'
            self.touch()
            return True
        else:
            for child in children:
                if child.close() == False:
                    return False
            self.status = 'CLOSED'
            self.touch()
            return True

    def touch(self):
        self.modified = datetime.now()
        for p in self.parents:
            p.parent.touch()


    def set_parent(self,parent):
        # first, remove all parent relationships
        for li in list(ListItem.select(ListItem.q.childID == self.id)):
            p = li.parent
            li.destroySelf()
            p.normalize_childrens_cardinality()
        # then add the new one
        parent.add_child(self)
        self.touch()

    def parent_trail(self):
        return self._parent_trail([])
        
    def _parent_trail(self,trail=[]):
        if len(self.parents) == 0:
        # base case
            return trail
        else:
            parent = self.parents[0].parent
            if parent not in trail:
                trail.insert(0,parent)
                return self.parents[0].parent._parent_trail(trail)
            else:
                # there's a loop, so just return what we've got
                return trail





class ListItem(SQLObject):
    parent = ForeignKey('Item',dbName='parent_item_id',cascade=True)
    child  = ForeignKey('Item',dbName='child_item_id',cascade=True)
    cardinality = IntCol(default=1)

    
	  

