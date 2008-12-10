
"""
Generic widget to present and manipulate data in a grid (tabular) form.

See also: http://trac.turbogears.org/turbogears/wiki/DataGridWidget
"""

from turbogears.widgets import Widget, CSSLink, static
from turbogears.widgets.base import CoreWD

NoDefault = object()

__all__ = ["DataGrid", "PaginateDataGrid"]

class DataGrid(Widget):

    """Generic widget to present and manipulate data in a grid (tabular) form.

    The columns to build the grid from are specified with fields ctor argument
    which is a list.  Currently an element can be either a two-element tuple or
    instance of DataGrid.Column class. If tuple is used it a Column is then
    build out of it, first element is assumed to be a title and second element -
    field accessor.

    You can specify columns' data statically, via fields ctor parameter, or
    dynamically, by via 'fields' key.
    """

    css=[CSSLink(static, "grid.css")]
    template = "turbogears.widgets.templates.datagrid"
    fields = None

    class Column:
        """Simple struct that describes single DataGrid column.

        Column has:
          - a name, which allows to uniquely identify column in a DataGrid
          - getter, which is used to extract field's value
          - title, which is displayed in the table's header
          - options, which is a way to carry arbitrary user-defined data

        """
        def __init__(self, name, getter=None, title=None, options=None):
            if not name:
                raise ValueError, 'name is required'
            if getter:
                if callable(getter):
                    self.getter = getter
                else: # assume it's an attribute name
                    self.getter = DataGrid.attrwrapper(getter)
            else:
                self.getter = DataGrid.attrwrapper(name)
            self.name = name
            self.title = title or name.capitalize()
            self.options = options or {}
        def get_option(self, name, default=NoDefault):
            if name in self.options:
                return self.options[name]
            if default is NoDefault: # no such key and no default is given
                raise KeyError(name)
            return default
        def get_field(self, row):
            return self.getter(row)
        def __str__(self):
            return "<DataGrid.Column %s>" % self.name

    class attrwrapper:
        """Helper class that returns an object's attribute when called.

        This allows to access 'dynamic' attributes (properties) as well as
        simple static ones.
        """
        def __init__(self, name):
            assert isinstance(name, str)
            self.name = name
        def __call__(self, obj):
            return getattr(obj, self.name)

    def __init__(self, fields=None, **kw):
        super(DataGrid, self).__init__(**kw)
        if fields:
            self.fields = fields
        if self.fields is None:
            self.fields = []
        self.columns = self._parse(self.fields)
    def get_column(self, name):
        """Returns DataGrid.Column with specified name.
        Raises KeyError if no such column exists.
        """
        for col in self.columns:
            if col.name == name:
                return col
        raise KeyError(name)
    def __getitem__(self, name):
        """Shortcut to get_column."""
        return self.get_column(name)
    def get_field_getter(columns):
        """ Returns a function to access the fields of table by row, col """
        idx = {} # index columns by name
        for col in columns:
            idx[col.name] = col
        def _get_field(row, col):
            return idx[col].get_field(row)
        return _get_field
    get_field_getter = staticmethod(get_field_getter)
    def update_params(self, d):
        super(DataGrid, self).update_params(d)
        if d.get('fields'):
            fields = d.pop('fields')
            columns = self._parse(fields)
        else:
            columns = self.columns[:]
        d['columns'] = columns
        d['get_field'] = self.get_field_getter(columns)
        # this is for backward compatibility
        d['headers'] = [col.title for col in columns]
        d['collist'] = [col.name for col in columns]
    def _parse(self, fields):
        "Parses fields specification into a list of L{Columns}s."
        columns = []
        names = {} # keep track of names to ensure there are no dups
        for n,col in enumerate(fields):
            if not isinstance(col, self.Column):
                title, name_or_f = col
                # construct name using column index
                name = 'column-' + str(n)
                col = self.Column(name, name_or_f, title)
            if col.name in names:
                raise ValueError('duplicate column name: %s' % name)
            columns.append(col)
            names[col.name] = 1
        return columns

class DataGridDesc(CoreWD):
    name = "DataGrid"
    for_widget = DataGrid(fields=[('Name', lambda row: row[1]),
                                  ('Country', lambda row: row[2]),
                                  ('Age', lambda row: row[0])],
                          default=[(33, "Anton Bykov", "Bulgaria"),
                                   (23, "Joe Doe", "Great Britain"),
                                   (44, "Pablo Martelli", "Brazil")])

class PaginateDataGrid(DataGrid):
    template = "turbogears.widgets.templates.paginate_datagrid"

#TODO: Create PaginateDataGridDesc
#class PaginateDataGridDesc(CoreWD):
