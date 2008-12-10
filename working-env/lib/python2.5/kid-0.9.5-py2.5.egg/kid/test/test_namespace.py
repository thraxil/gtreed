"""kid.namespace tests."""

__revision__ = "$Rev: 421 $"
__date__ = "$Date: 2006-10-22 07:02:46 -0400 (Sun, 22 Oct 2006) $"
__author__ = "Ryan Tomayko (rtomayko@gmail.com)"
__copyright__ = "Copyright 2004-2005, Ryan Tomayko"
__license__ = "MIT <http://www.opensource.org/licenses/mit-license.php>"

from kid.namespace import Namespace
from kid.serialization import NamespaceStack

def test_namespace_module():
    ns = Namespace(uri='urn:test', prefix='test')
    assert ns.name == '{urn:test}name'
    assert ns['name'] == '{urn:test}name'
    assert ns.qname('name') == 'test:name'
    ns = Namespace(uri=None)
    assert ns.name == 'name'
    assert ns['name'] == 'name'
    assert ns.qname('name') == 'name'

def test_namespace_stack():
    stack = NamespaceStack()
    namespaces = [
        {'': 'urn:default/namespace'},
        {'test0': 'urn:test_namespace_0', 'test1': 'urn:test_namespace_1',},
        {'test3': 'urn:test_namespace_3', },
        {'': 'urn:new/default/namespace',},
        {'test0': 'urn:inner/test0',},
        {'inner_test3': 'urn:test_namespace_3',},
    ]
    for ns in namespaces:
        stack.push(ns)
    
    ru = stack.resolve_uri
    assert ru('inner_test3') == 'urn:test_namespace_3'
    assert ru('test0') == 'urn:inner/test0'

    rp = stack.resolve_prefix
    assert rp('urn:default/namespace', default=True) == None
    assert rp('urn:default/namespace', default=False) == None
    assert rp('urn:new/default/namespace', default=True) == ''
    assert rp('urn:new/default/namespace', default=False) == None
    assert rp('urn:test_namespace_3', default=True) == 'test3'
    assert rp('urn:test_namespace_3', default=False) == 'test3'

    for x in range(len(namespaces)-1, -1, -1):
        ns = stack.pop()
        print ns, namespaces[x]
        assert ns == namespaces[x]
