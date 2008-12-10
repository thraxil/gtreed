import turbogears
import sqlobject
from sqlobject.sqlbuilder import *
import cherrypy

class Browse(object):
    def __getattr__(self,attrib):
        """Delegate basic methods to CatWalk"""
        return getattr(self.catwalk,attrib)


    def list_view(sql_class_name,page_size=10,offset=10,fields=[],filters=[],sort_by=None):
        pass 

    def index(self,object_name,start=0,page_size=10,context='',filters=''):
        total = 0
        headers = []
        rows = []
        start = int(start)
        page_size = int(page_size)
        if not context: context = object_name
        headers = self.column_headers(object_name,context)
        headers = [header for header in headers if header['visible']]
        total,rows = self.rows_for_model(object_name,start,page_size,filters)

        return dict(object_name=object_name,
                    start=start,
                    page_size=page_size,
                    total=total,
                    headers= headers,
                    rows = rows 
                   )
    index = turbogears.expose(template='turbogears.toolbox.catwalk.browse_grid',
                              allow_json=True)(index)

    def columns(self,object_name,context=''):
        if not context:context = object_name
        return dict(object_name=object_name,
                    context = context,
                    columns=self.extended_column_headers(object_name,context))
    columns = turbogears.expose(template='turbogears.toolbox.catwalk.columns',
                                allow_json=True)(columns)

    def save_columns(self,object_name,context,order,hidden_columns,updated_fk_labels):
        self.save_column_order(context,order)
        self.hide_columns(context,hidden_columns)
        if updated_fk_labels:
            for updated_fk_label in updated_fk_labels.split('|'):
                object,column_name = updated_fk_label.split(':')
                self.column_label_for_object(object,column_name)
        return "<script>parent.cat_browse.columns_saved('%s','%s');</script>"% (object_name,context)
    save_columns= turbogears.expose(allow_json=True)(save_columns)
        
    def extended_column_headers(self,object_name,context):
        cols = [{'name':'id','title':'#','type':'SOInteger'}]
        cols.extend(self.column_labels(object_name,extended=True))
        cols.extend(self.join_labels(object_name,extended=True))
        cols = self.arrange_columns(cols,context)
        return cols

    def column_headers(self,object_name,context):
        cols = [{'name':'id','title':'#'}]
        cols.extend(self.column_labels(object_name))
        cols.extend(self.join_labels(object_name))
        cols = self.arrange_columns(cols,object_name)
        return cols

    def arrange_columns(self,headers,context):
        #arrange order and visibility 
        hidden_columns = self.load_columns_visibility_state(context)
        order = self.load_column_order(context)
        for col in headers:
            col['visible'] = True
            if col['name'] in hidden_columns: col['visible'] = False

        if not order:return headers
        c={}
        for col in headers:
            c[col['name']] = col
            if col['name'] not in order:order.append(col['name'])
        rearrenged = []
        for name in order:
            if name not in c.keys():continue
            rearrenged.append(c[name])
        return rearrenged

    def prepare_filter(self,obj,filter):
        for column in obj.sqlmeta.columns.values():
            if column.origName == filter[0]:
                return getattr(obj.q,column.name) == filter[1]

        #if we got so far we couldn't find the column, bark at the moon
        msg='filter_column_error. Could not find the column for filter:%s'% filter[0] 
        raise cherrypy.HTTPRedirect(turbogears.url('/error', msg=msg))

    def filtered_query(self,obj,filters):
        if not ':' in filters: #there should at least be a semicolon
            msg='filter_format_error. The format is column_name:value, not %s'% filters 
            raise cherrypy.HTTPRedirect(turbogears.url('/error', msg=msg))

        filters = [filter.split(':') for filter in filters.split(',')]
        conditions =  tuple([self.prepare_filter(obj,filter) for filter in filters])
        return obj.select(AND(* conditions ))
            
    def rows_for_model(self,object_name,start,page_size,filters):
        ids = []
        rows = {} 
        obj = self.load_object(object_name)

        if filters:
            query = self.filtered_query(obj,filters) 
        else:
            query = obj.select()

        total = query.count()
        if page_size:
            results = query[start:start+page_size]
        else:
            results = query[start:]

        for result in results:
            rows[result.id] = self.fields(object_name,result)
        
        relations = self.relation_values(object_name,rows)
        rows = self.merge_relation_values(rows,relations)
        rows = self.foreign_key_alias_value(object_name,rows)
        return total,rows

    def relation_values(self,object_name,rows):
        joins = {}
        ids = rows.keys()
        if not ids: return joins

        obj = self.load_object(object_name)
        conn = obj._connection
        for column in obj.sqlmeta.joins:
            query = None
            coltype = self.get_column_type(column)
            if coltype in ('SOMultipleJoin', 'SOSQLMultipleJoin'):
                query = conn.sqlrepr( Select( [
                                         column.soClass.q.id,
                                         func.Count(column.otherClass.q.id)
                                         ],
                                         where=AND( 
                                                    column.soClass.q.id==self.join_foreign_key(column),
                                                    IN(column.soClass.q.id,ids)
                                                ), groupBy=column.soClass.q.id))

            elif coltype in ('SORelatedJoin', 'SOSQLRelatedJoin'):
                d = (column.intermediateTable,
                     column.joinColumn,
                     column.intermediateTable,
                     column.otherColumn,
                     column.intermediateTable,
                     column.intermediateTable,
                     column.joinColumn,
                    ','.join(['%s'%x for x in ids]),
                     column.intermediateTable,
                     column.joinColumn)
                     
                query = "SELECT %s.%s, Count(%s.%s) FROM %s WHERE %s.%s IN(%s) GROUP BY %s.%s" % d

                
            elif coltype == 'SOSingleJoin':
                alias = self.load_label_column_for_object(column.otherClassName)
                query = conn.sqlrepr( Select( [ column.soClass.q.id,getattr(column.otherClass.q,alias)],
                                                where=AND( 
                                                    column.soClass.q.id==self.join_foreign_key(column),
                                                    IN(column.soClass.q.id,ids)
                                                )))

            if not query: continue
            joins[column.joinMethodName] = conn.queryAll(query)
        return joins

    def foreign_key_alias_value(self,object_name,rows):
        for column in self.foreign_key_columns(object_name): 
            alias = self.load_label_column_for_object(column.foreignKey)
            if alias == 'id':continue
            column_name = column.name.replace('ID','')
            fk_values = self.foreign_key_query(column,alias,[x[column_name] for x in rows])
            for row in rows: row[column_name] = fk_values.get(row[column_name],'')
        return rows

    def foreign_key_query(self,column,alias,ids):
        if not ids: return {}
        sql_object = self.load_object(column.foreignKey)
        conn = sql_object._connection
        query = conn.sqlrepr( Select( [ sql_object.q.id,getattr(sql_object.q,alias) ], 
                                      where=IN(sql_object.q.id,ids) ) )
        fk_values = {}
        for id,alias in conn.queryAll(query): fk_values[str(id)] = self.encode_label( alias )
        return fk_values

    def join_foreign_key(self,column):
        foreign_key = '%sID'% column.joinColumn.split('_')[0]
        return getattr(column.otherClass.q,foreign_key)

    def column_label_options(self,column):
        foreign_key_labels = [{'name':'id','title':'#'}]
        foreign_key_labels.extend(self.column_labels(column.foreignKey))
        return foreign_key_labels

    def column_labels(self,object_name,extended=False):
        cols = []
        sql_object = self.load_object(object_name)
        for column_name in sql_object.sqlmeta.columns:
            column = sql_object.sqlmeta.columns[column_name]
            if sql_object._inheritable and column_name == 'childName':continue
            cols.append({'name':column.name, 'title':self.column_title(column)})
            if isinstance(column, sqlobject.col.SOForeignKey):
                cols[-1]['name'] = cols[-1]['name'].replace('ID','')
            if extended:
                cols[-1]['type']=self.get_column_type(column)
                if isinstance(column, sqlobject.col.SOForeignKey):
                    cols[-1]['column_label'] = self.load_label_column_for_object(column.foreignKey)
                    cols[-1]['label_options']=self.column_label_options(column)
                    cols[-1]['other_class_name'] = column.foreignKey
        return cols

    def join_labels(self,object_name,extended=False):
        cols = []
        sql_object = self.load_object(object_name)
        for col in sql_object.sqlmeta.joins:
            cols.append({'name':col.joinMethodName,'title':''})
            if extended:
                cols[-1]['type']=self.get_column_type(col)
                cols[-1]['other_class_name'] = col.otherClassName
        return cols

    def merge_relation_values(self,rows,relations):
        for field_name in relations:
            for id,value in relations[field_name]:
                if not rows.has_key(id):continue
                rows[id][field_name] = self.encode_label(value)
        keys = rows.keys()
        keys.sort()
        return [rows[x] for x in keys]

    def foreign_key_columns(self,object_name):
        fk = []
        sql_object = self.load_object(object_name)
        for column_name in sql_object.sqlmeta.columns:
            column = sql_object.sqlmeta.columns[column_name]
            if sql_object._inheritable and column_name == 'childName':continue
            if isinstance(column, sqlobject.col.SOForeignKey):fk.append(column)
        return fk

    def field_value(self,result,column):
        value = getattr(result,column.name)
        return self.encode_label(value)

    def fields(self,object_name,result):
        object = self.load_object(object_name)
        props = {}
        props['id'] = result.id
        for column_name in object.sqlmeta.columns:
            column = object.sqlmeta.columns[column_name]
            if object._inheritable and column_name == 'childName':continue
            column_name = column.name
            if isinstance(column, sqlobject.col.SOForeignKey): column_name = column_name.replace('ID','')
            props[column_name] = self.field_value(result, column)
        return props.copy()
