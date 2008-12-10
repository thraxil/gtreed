from unittest import TestSuite, TestCase, makeSuite
from protocols import adapt, advise, Interface, Attribute, declareAdapter
from protocols import AbstractBase, AdaptationFailure

class APITests(TestCase):

    def checkAdaptTrapsTypeErrorsOnConform(self):
        class Conformer:
            def __conform__(self,ob):
                return []
        assert adapt(Conformer,list,None) is None
        assert adapt(Conformer(),list,None) == []

    def checkAdaptHandlesIsInstance(self):
        assert adapt([1,2,3],list,None) == [1,2,3]
        assert adapt('foo',str,None) == 'foo'
        assert adapt('foo',list,None) is None


    def checkAdviseFailsInCallContext(self):
        try:
            advise()
        except SyntaxError:
            pass
        else:
            raise AssertionError(
                "Should've got SyntaxError for advise() in function"
            )


    def checkAdviseClassKeywordsValidated(self):
        try:
            class X: advise(moduleProvides=list)
        except TypeError,v:
            assert v.args==(
               "Invalid keyword argument for advising classes: moduleProvides",
            )
        else:
            raise AssertionError("Should've caught invalid keyword")


    def checkAdviseClassKeywordsValidated(self):
        try:
            class X: advise(moduleProvides=list)
        except TypeError,v:
            assert v.args==(
               "Invalid keyword argument for advising classes: moduleProvides",
            )
        else:
            raise AssertionError("Should've caught invalid keyword")


    def checkAdviseModuleKeywordsValidated(self):
        try:
            exec "advise(instancesProvide=[IProtocol1])" in globals(),globals()
        except TypeError,v:
            assert v.args==(
             "Invalid keyword argument for advising modules: instancesProvide",
            )
        else:
            raise AssertionError("Should've caught invalid keyword")

    def checkAdviseInClassExec(self):
        d = {'advise':advise,'IProtocol1':IProtocol1}
        exec "class Foo: advise(instancesProvide=[IProtocol1])" in d

    def checkSimpleAdaptation(self):
        class Conformer:
            def __conform__(self,protocol):
                if protocol==42:
                    return "hitchhiker",self
        class AdaptingProtocol:
            def __adapt__(klass,ob):
                return "adapted", ob
            __adapt__ = classmethod(__adapt__)

        c = Conformer()
        assert adapt(c,42,None) == ("hitchhiker",c)
        assert adapt(c,AdaptingProtocol,None) == ("adapted",c)
        assert adapt(42,AdaptingProtocol,None) == ("adapted",42)
        assert adapt(42,42,None) is None

    def checkAdaptFiltersTypeErrors(self):

        class Nonconformist:
            def __conform__(self,ob):
                raise TypeError("You got me!")

        class Unadaptive:
            def __adapt__(self,ob):
                raise TypeError("You got me!")

        # These will get a type errors calling __conform__/__adapt__
        # but should be ignored since the error is at calling level
        assert adapt(None, Unadaptive, None) is None
        assert adapt(Nonconformist, None, None) is None

        # These will get type errors internally, and the error should
        # bleed through to the caller
        self.assertTypeErrorPassed(None, Unadaptive(), None)
        self.assertTypeErrorPassed(Nonconformist(), None, None)

        self.assertRaises(AdaptationFailure, adapt, None, None)

    def assertTypeErrorPassed(self, *args):
        try:
            # This should raise TypeError internally, and be caught
            adapt(*args)
        except TypeError,v:
            assert v.args==("You got me!",)
        else:
            raise AssertionError("Should've passed TypeError through")

    def checkImplicationBug(self):
        class I1(Interface): pass
        class I2(I1): pass
        declareAdapter(lambda o: o, provides=[I1],forProtocols=[I2])






    def checkAttribute(self):

        for i in range(10)+[None]:

            class Abstract(AbstractBase):
                value = Attribute("testing", "value", i)

            ob = Abstract()
            assert ob.value == i

            for j in range(10):
                ob.value = j
                assert ob.value==j


    def checkStickyAdapter(self):
        class T: pass
        t = T()
        class I(Interface): pass
        from protocols.adapters import StickyAdapter
        class A(StickyAdapter):
            attachForProtocols = I,
            advise(instancesProvide=[I], asAdapterForTypes=[T])

        a = I(t)
        assert adapt(t, I) is a
        assert a.subject is t

        n = T()
        a2 = I(n)
        assert a2 is not a
        assert a2.subject is n
        assert adapt(n, I) is a2








from protocols import protocolForType, protocolForURI, sequenceOf, advise
from protocols import declareImplementation, Variation
from UserDict import UserDict

IGetSetMapping  = protocolForType(dict,['__getitem__','__setitem__'])
IGetMapping     = protocolForType(dict,['__getitem__'])

ISimpleReadFile = protocolForType(file,['read'])
IImplicitRead   = protocolForType(file,['read'], implicit=True)

IProtocol1 = protocolForURI("http://peak.telecommunity.com/PyProtocols")

multimap = sequenceOf(IGetMapping)

declareImplementation(UserDict,[IGetSetMapping])

IMyUnusualMapping = Variation(IGetSetMapping)

class MyUserMapping(object):
    pass

declareImplementation(MyUserMapping,[IMyUnusualMapping])



















class GenerationTests(TestCase):
    def checkTypeSubset(self):
        d = {}
        assert IGetSetMapping(d,None) is d
        assert IGetMapping(d,None) is d

    def checkImplications(self):
        d = UserDict()
        assert IGetMapping(d,None) is d
        assert IImplicitRead(d,None) is None

    def checkWeak(self):
        from cStringIO import StringIO
        s = StringIO("foo")
        assert ISimpleReadFile(s,None) is None
        assert IImplicitRead(s,None) is s

    def checkURI(self):
        p = protocolForURI("http://www.python.org/")
        assert p is not IProtocol1
        p = protocolForURI("http://peak.telecommunity.com/PyProtocols")
        assert p is IProtocol1

    def checkSequence(self):
        d1,d2 = {},{}
        seq = multimap([d1,d2])
        assert seq == [d1,d2]
        assert seq[0] is d1 and seq[1] is d2
        class ISequenceLike(Interface): advise(protocolIsSubsetOf=[multimap])
        ISequenceLike([d1,d2])

    def checkVariation(self):
        d = {}
        assert IMyUnusualMapping(d,None) is d # GetSet implies variation
        d = MyUserMapping(); assert IMyUnusualMapping(d,None) is d
        assert IGetSetMapping(d,None) is None # but not the other way
        self.assertEqual(repr(IMyUnusualMapping),
          "Variation(TypeSubset(<type 'dict'>,('__getitem__', '__setitem__')))")
        self.assertEqual(repr(Variation(Interface,42)),
          "Variation(<class 'protocols.interfaces.Interface'>,42)")

def test_suite():

    from protocols.tests import test_advice, test_direct, test_classes

    tests = [
        test_advice.test_suite(),
        test_classes.test_suite(),
        test_direct.test_suite(),
        makeSuite(APITests,'check'),
        makeSuite(GenerationTests,'check'),
    ]

    try:
        import zope.interface
    except ImportError:
        pass
    else:
        from protocols.tests import test_zope
        tests.append( test_zope.test_suite() )

    try:
        import twisted.python.components
    except ImportError:
        pass
    else:
        from protocols.tests import test_twisted
        tests.append( test_twisted.test_suite() )

    return TestSuite(
        tests
    )










