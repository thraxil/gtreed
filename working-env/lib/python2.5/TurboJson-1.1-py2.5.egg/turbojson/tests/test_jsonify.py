from turbojson import jsonify


class Foo(object):
    def __init__(self, bar):
        self.bar = bar

def jsonify_foo(obj):
    return "foo-%s" % obj.bar
jsonify_foo = jsonify.jsonify.when("isinstance(obj, Foo)")(jsonify_foo)

def test_dictionary():
    d = {'a':1, 'b':2}
    encoded = jsonify.encode(d)
    print encoded
    assert encoded == '{"a": 1, "b": 2}'

def test_specificjson():
    a = Foo("baz")
    encoded = jsonify.encode(a)
    print encoded
    assert encoded == '"foo-baz"'

def test_specific_in_dict():
    a = Foo("baz")
    d = {"a":a}
    encoded = jsonify.encode(d)
    print encoded
    assert encoded == '{"a": "foo-baz"}'
    