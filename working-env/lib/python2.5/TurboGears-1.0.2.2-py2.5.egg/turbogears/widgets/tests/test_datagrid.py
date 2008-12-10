
from turbogears.widgets.datagrid import DataGrid

class Foo:
    def __init__(self, name, subtype, text):
        self.name = name
        self.subtype = subtype
        self.text = text
    def _get_excerpt(self):
        return self.text + '...'
    excerpt = property(fget=_get_excerpt)

class User:
    def __init__(self, ID, name, emailAddress):
        self.userId = ID
        self.name = name
        self.emailAddress = emailAddress
    displayName = property(fget=lambda self: self.name.capitalize())

class TestDataGrid:
    def test_declaration_styles(self):
        grid = DataGrid(name='grid', fields=[
                    DataGrid.Column('name', options=dict(foobar=123)), 
                    ('Subtype', 'subtype'),
                    DataGrid.Column('text', 'excerpt', 'TEXT'),
                ])
        d = dict(value='value')
        grid.update_params(d)
        get_field = d['get_field']
        assert ['Name', 'Subtype', 'TEXT'] == d['headers']
        assert ['name', 'column-1', 'text'] == d['collist']
        assert d['columns'][0].get_option('foobar') == 123
        assert grid.get_column('name').options['foobar'] == 123
        row = Foo('spa1', 'fact', 'thetext')
        assert 'spa1' == get_field(row, 'name')
        assert 'fact' == get_field(row, 'column-1')
        assert 'thetext...' == get_field(row, 'text')
    def test_template_overridal(self):
        grid = DataGrid(fields=[
                    ('Name', 'name'), 
                    ('Subtype', 'subtype'),
                    ('TEXT', Foo._get_excerpt),
                ], template = "turbogears.fastdata.templates.datagrid")
        d = dict(value='value')
        grid.update_params(d)
    def test_wiki_samples(self):
        #Test that sample code posted on DataGridWidget wiki page actually works.
        grid = DataGrid(fields=[
            ('ID', 'userId'),
            ('Name', 'displayName'),
            ('E-mail', 'emailAddress'),
        ])
        users = [User(1, 'john', 'john@foo.net'), User(2, 'fred', 'fred@foo.net')]
        print grid.display(users)
        grid = DataGrid(fields=[
            ('Name', lambda row: row[1]),
            ('Country', lambda row: row[2]),
            ('Age', lambda row: row[0]),
        ])
        data = [(33, "Anton Bykov", "Bulgaria"), 
            (23, "Joe Doe", "Great Britain"), (44, "Pablo Martelli", "Brazil")]
        print grid.display(data)


