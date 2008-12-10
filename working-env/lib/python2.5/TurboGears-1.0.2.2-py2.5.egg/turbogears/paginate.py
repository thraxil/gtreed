import re
import types
from math import ceil
import logging

import cherrypy
try:
    import sqlobject
    from sqlobject.main import SelectResults
except ImportError:
    SelectResults = None
    sqlobject = None

try:
    # Can't depend on sqlalchemy being available.
    import sqlalchemy
    from sqlalchemy.ext.selectresults import SelectResults as SASelectResults
except ImportError:
    SASelectResults = None
    sqlalchemy = None
 
import turbogears
from turbogears.decorator import weak_signature_decorator
from turbogears.view import variable_providers
from formencode.variabledecode import variable_encode, variable_decode

log = logging.getLogger("turbogears.paginate")

def paginate(var_name, default_order='', default_reversed=False, limit=10,
            allow_limit_override=False, max_pages=5):
    def entangle(func):
        def decorated(func, *args, **kw):
            page = int(kw.pop('tg_paginate_no', 1))
            limit_ = int(kw.pop('tg_paginate_limit', limit))
            order = kw.pop('tg_paginate_order', None)
            ordering = kw.pop('tg_paginate_ordering', {})

            # Convert ordering str to a dict.
            if ordering:
                ordering = convert_ordering(ordering)

            if not allow_limit_override:
                limit_ = limit

            log.debug("Pagination params: page=%s, limit=%s, order=%s "
                      "", page, limit_, order)
            
            # get the output from the decorated function    
            output = func(*args, **kw)
            if not isinstance(output, dict):
                return output
            try:
                var_data = output[var_name]
            except KeyError:
                raise "Didn't get expected variable"
            
            if order and not default_order:
                raise "If you want to enable ordering you need " \
                      "to provide a default_order" 
            elif default_order and not ordering:
                ordering = {default_order:[0, not default_reversed]}
            elif ordering and order:
                sort_ordering(ordering, order)
            log.debug('ordering %s' % ordering)

            row_count = 0
            if (SelectResults and isinstance(var_data, SelectResults)) or \
               (SASelectResults and isinstance(var_data, SASelectResults)):
                row_count = var_data.count()
                if ordering:
                    # Build order_by list.
                    order_cols = range(len(ordering))
                    for (colname, order_opts) in ordering.items():
                        col = sql_get_column(colname, var_data)
                        if not col:
                            raise StandardError, "The order column (%s) doesn't exist" % colname
                        order_by_expr = sql_order_col(col, order_opts[1])
                        order_cols[order_opts[0]] = order_by_expr
                    # May need to address potential of ordering already
                    # existing in var_data.
                    # SO and SA differ on this method name.
                    if hasattr(var_data, 'orderBy'):
                        var_data = var_data.orderBy(order_cols)
                    else:
                        var_data = var_data.order_by(order_cols)
            elif isinstance(var_data, list):
                row_count = len(var_data)
            else:
                raise 'Variable is not a list or SelectResults'

            offset = (page-1) * limit_
            page_count = int(ceil(float(row_count)/limit_))

            # if it's possible display every page
            if page_count <= max_pages:
                pages_to_show = range(1,page_count+1)
            else:
                pages_to_show = _select_pages_to_show(page_count=page_count,
                                              current_page=page,
                                              max_pages=max_pages)
                
            # which one should we use? cherrypy.request.input_values or kw?
            #input_values = cherrypy.request.input_values.copy()
            ##input_values = kw.copy()
            input_values =  variable_encode(cherrypy.request.params.copy())
            input_values.pop('self', None)
            for input_key in input_values.keys():
                if input_key.startswith('tg_paginate'):
                    del input_values[input_key]

            cherrypy.request.paginate = Paginate(current_page=page,
                                             limit=limit_, 
                                             pages=pages_to_show, 
                                             page_count=page_count, 
                                             input_values=input_values, 
                                             order=order,
                                             ordering=ordering,
                                             row_count=row_count)
                                             
            # we replace the var with the sliced one
            endpoint = offset + limit_
            log.debug("slicing data between %d and %d", offset, endpoint)
            output[var_name] = var_data[offset:endpoint]

            return output
        return decorated
    return weak_signature_decorator(entangle)

def _paginate_var_provider(d): 
    # replaced cherrypy.thread_data for cherrypy.request
    # thanks alberto!
    paginate = getattr(cherrypy.request, 'paginate', None)
    if paginate:
        d.update(dict(paginate=paginate))
variable_providers.append(_paginate_var_provider)

class Paginate:
    """class for variable provider"""
    def __init__(self, current_page, pages, page_count, input_values, 
                 limit, order, ordering, row_count):
                 
        self.pages = pages
        self.limit = limit
        self.page_count = page_count
        self.current_page = current_page
        self.input_values = input_values
        self.order = order
        self.ordering = ordering
        self.row_count = row_count
        self.first_item = (current_page - 1) * limit + 1
        self.last_item = min(current_page * limit, row_count)
        self.reversed = False

        # Should reversed be true?
        for (field_name, ordering_values) in ordering.items():
            if ordering_values[0] == 0 and not ordering_values[1]:
                self.reversed = True

        # If ordering is empty, don't add it.
        input_values = dict(tg_paginate_limit=limit)
        if ordering:
            input_values['tg_paginate_ordering'] = ordering
        self.input_values.update(input_values)

        if current_page < page_count:
            self.input_values.update(dict(
                                tg_paginate_no=current_page+1,
                                tg_paginate_limit=limit))
            self.href_next = turbogears.url(cherrypy.request.path, input_values)
            self.input_values.update(dict(
                                tg_paginate_no=page_count,
                                tg_paginate_limit=limit))
            self.href_last = turbogears.url(cherrypy.request.path, input_values)
        else:
            self.href_next = None
            self.href_last = None
            
        if current_page > 1:
            self.input_values.update(dict(
                                tg_paginate_no=current_page-1,
                                tg_paginate_limit=limit))
            self.href_prev = turbogears.url(cherrypy.request.path, input_values)
            self.input_values.update(dict(
                                tg_paginate_no=1,
                                tg_paginate_limit=limit))
            self.href_first = turbogears.url(cherrypy.request.path, input_values)
        else:
            self.href_prev = None
            self.href_first = None
            
    def get_href(self, page, order=None, reverse_order=None):
        # Note that reverse_order is not used.  It should be cleaned up here
        # and in the template.  I'm not removing it now because I don't want
        # to break the API.
        order = order or None
        self.input_values['tg_paginate_no'] = page
        if order:
            self.input_values['tg_paginate_order'] = order

        return turbogears.url('', self.input_values)

def _select_pages_to_show(current_page, page_count, max_pages):
    pages_to_show = []
    
    if max_pages < 3:
        raise "The minimun value for max_pages on this algorithm is 3"

    if page_count <= max_pages:
        pages_to_show = range(1,page_count+1)
    
    pad = 0
    if not max_pages % 2:
        pad = 1
        
    start = current_page - (max_pages / 2) + pad
    end = current_page + (max_pages / 2)
    
    if start < 1:
        end = end + (start * -1) + 1
        start = 1

    if end > page_count:
        start = start - (end - page_count)
        end = page_count
        
    return range(start, end+1)

def sort_ordering(ordering, sort_name):
    """Rearrange ordering based on sort_name."""
    log.debug('sort called with %s and %s' % (ordering, sort_name))
    if sort_name not in ordering:
        ordering[sort_name] = [-1, True] 
    if ordering[sort_name][0] == 0:
        # Flip
        ordering[sort_name][1] = not ordering[sort_name][1]
    else:
        ordering[sort_name][0] = 0
        for key in ordering.keys():
            if key != sort_name and ordering[key][0] < len(ordering) - 1:
                ordering[key][0] += 1
    log.debug('sort results is %s and %s' % (ordering, sort_name))

def sql_get_column(colname, var_data):
    """Return a column from var_data based on colname."""
    if isinstance(var_data, SelectResults):
        col = getattr(var_data.sourceClass.q, colname, None)

    elif isinstance(var_data, SASelectResults):
        col = getattr(
                var_data._query.mapper.c,
                colname[len(var_data._query.mapper.column_prefix or ''):],
                None)

    else:
        raise StandardError, 'expected SelectResults'

    return col

def sql_order_col(col, ascending=True):
    """Return an ordered col for col."""
    if sqlalchemy and isinstance(col, sqlalchemy.schema.Column):
        if ascending:
            order_col = sqlalchemy.sql.asc(col)
        else:
            order_col = sqlalchemy.sql.desc(col)
    elif sqlobject and isinstance(col, types.InstanceType):
        # I don't like using InstanceType, but that's what sqlobject col type
        # is.
        if ascending:
            order_col = col
        else:
            order_col = sqlobject.DESC(col)
    else:
        raise StandardError, 'expected Column, but got %s' % str(type(col))
    return order_col
   
# Ordering re:
ordering_expr = re.compile(r"('\w+'): ?\[(\d+), ?(True|False)\]")

def convert_ordering(ordering):
    """Covert ordering unicode string to dict."""

    log.debug('ordering received %s' % str(ordering))

    # eval would be simple, but insecure.
    if not isinstance(ordering, (str, unicode)):
        raise ValueError, "ordering should be string or unicode."
    new_ordering = {}
    if ordering == u"{}":
        pass
    else:
        try:
            ordering_info_find = ordering_expr.findall(ordering)
            emsg = "Didn't match ordering for %s." % str(ordering)
            assert len(ordering_info_find) > 0, emsg
            for ordering_info in ordering_info_find:
                ordering_key = str(ordering_info[0]).strip("'")
                ordering_order = int(ordering_info[1])
                ordering_reverse = bool(ordering_info[2] == 'True')
                new_ordering[ordering_key] = [ordering_order,
                                              ordering_reverse]
        except StandardError, e:
            log.debug('FAILED to convert ordering.')
            new_ordering = {}
    log.debug('ordering converted to %s' % str(new_ordering))
    return new_ordering
