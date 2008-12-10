# Using RuleDispatch:

import datetime

import dispatch
from simplejson import JSONEncoder

try:
    import decimal
except ImportError:
    # Python 2.3
    decimal = None

def jsonify(obj):
    """
    Return an object that can be serialized with JSON, i.e., it
    is made up of only lists, dictionaries (with string keys),
    and strings, ints, and floats.
    """
    raise NotImplementedError
jsonify = dispatch.generic()(jsonify)

def jsonify_datetime(obj):
	return str(obj)
jsonify_datetime = jsonify.when(
        'isinstance(obj, datetime.datetime) or '
        'isinstance(obj, datetime.date)')(jsonify_datetime)

def jsonify_decimal(obj): 
    return float(obj) 
if decimal is not None: 
    jsonify_decimal = jsonify.when('isinstance(obj, decimal.Decimal)')( 
        jsonify_decimal) 

def jsonify_explicit(obj):
    return obj.__json__()
jsonify_explicit = jsonify.when('hasattr(obj, "__json__")')(jsonify_explicit)

# SQLObject support
try:
    import sqlobject
    
    def jsonify_sqlobject(obj):
        result = {}
        result['id'] = obj.id
        cls = obj.sqlmeta.soClass
        for name in cls.sqlmeta.columns.keys():
            if name != 'childName':
                result[name] = getattr(obj, name)
        while cls.sqlmeta.parentClass:
            cls = cls.sqlmeta.parentClass
            for name in cls.sqlmeta.columns.keys():
                if name != 'childName':
                    result[name] = getattr(obj, name)
        return result
    jsonify_sqlobject = jsonify.when(
            'isinstance(obj, sqlobject.SQLObject)')(jsonify_sqlobject)
            
    def jsonify_select_results(obj):
        return list(obj)
    jsonify_select_results = jsonify.when(
            'isinstance(obj, sqlobject.SQLObject.SelectResultsClass)')(
                    jsonify_select_results)
except ImportError:
    pass


class GenericJSON(JSONEncoder):

    def default(self, obj):
        return jsonify(obj)

_instance = GenericJSON()

def encode_iter(obj):
    return _instance.iterencode(obj)

def encode(obj):
    return _instance.encode(obj)
