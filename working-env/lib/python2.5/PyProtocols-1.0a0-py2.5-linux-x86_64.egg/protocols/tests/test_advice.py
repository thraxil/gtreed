"""Tests for advice"""

from unittest import TestCase, makeSuite, TestSuite
from protocols.advice import *
import sys
from types import InstanceType

def ping(log, value):

    def pong(klass):
        log.append((value,klass))
        return [klass]

    addClassAdvisor(pong)

def as_(*decorators):
    """Use Python 2.4 decorators w/Python 2.2+

    Example::

        import dispatch

        class Foo(object):
            [dispatch.as(classmethod)]
            def something(cls,etc):
                \"""This is a classmethod\"""
    """

    if len(decorators)>1:
        decorators = list(decorators)
        decorators.reverse()

    def callback(frame,k,v,old_locals):
        for d in decorators:
            v = d(v)
        return v

    from protocols.advice import add_assignment_advisor
    return add_assignment_advisor(callback)


class SuperTest(TestCase):

    def checkMetaSuper(self):

        class Meta(type):
            def foo(self,arg):
                return arg
            foo = metamethod(foo)

        class Class(object):
            __metaclass__ = Meta

            def foo(self,arg):
                return arg*2

        # Verify that ob.foo() and ob.__class__.foo() are different
        assert Class.foo(1)==1
        assert Class().foo(1)==2


        # Verify that supermeta() works for such methods

        class SubMeta(Meta):
            def foo(self,arg):
                return -supermeta(SubMeta,self).foo(arg)
            foo = metamethod(foo)

        class ClassOfSubMeta(Class):
            __metaclass__ = SubMeta

        assert ClassOfSubMeta.foo(1)==-1
        assert ClassOfSubMeta().foo(1)==2









    def checkPropSuper(self):

        class Base(object):
            __slots__ = 'foo'

        class Sub(Base):

            def getFoo(self):
                return supermeta(Sub,self).foo * 2

            def setFoo(self,val):
                Base.foo.__set__(self,val)

            foo = property(getFoo, setFoo)

        ob = Sub()
        ob.foo = 1
        assert ob.foo == 2


    def checkSuperNotFound(self):
       class Base(object):
           pass

       b = Base()
       try:
           supermeta(Base,b).foo
       except AttributeError:
           pass
       else:
           raise AssertionError("Shouldn't have returned a value")










class DecoratorTests(TestCase):

    def checkAssignAdvice(self):

        log = []
        def track(f,k,v,d):
            log.append((f,k,v))
            if k in f.f_locals:
                del f.f_locals[k]   # simulate old-style advisor

        add_assignment_advisor(track,frame=sys._getframe())
        test_var = 1
        self.assertEqual(log, [(sys._getframe(),'test_var',1)])
        log = []
        add_assignment_advisor(track,1)
        test2 = 42
        self.assertEqual(log, [(sys._getframe(),'test2',42)])

        # Try doing double duty, redefining an existing variable...
        log = []
        add_assignment_advisor(track,1)
        add_assignment_advisor(track,1)

        test2 = 42
        self.assertEqual(log, [(sys._getframe(),'test2',42)]*2)


    def checkAs(self):

        def f(): pass

        [as_(lambda x: [x])]
        f1 = f

        self.assertEqual(f1, [f])

        [as_(list, lambda x: (x,))]
        f1 = f
        self.assertEqual(f1, [f])


    def check24DecoratorMode(self):

        log = []
        def track(f,k,v,d):
            log.append((f,k,v))
            return v

        def foo(x): pass

        add_assignment_advisor(track,1)(foo)
        x = 1

        self.assertEqual(log, [(sys._getframe(),'foo',foo)])




























moduleLevelFrameInfo = getFrameInfo(sys._getframe())

class FrameInfoTest(TestCase):

    classLevelFrameInfo = getFrameInfo(sys._getframe())

    def checkModuleInfo(self):
        kind,module,f_locals,f_globals = moduleLevelFrameInfo
        assert kind=="module"
        for d in module.__dict__, f_locals, f_globals:
            assert d is globals()

    def checkClassInfo(self):
        kind,module,f_locals,f_globals = self.classLevelFrameInfo
        assert kind=="class"
        assert f_locals['classLevelFrameInfo'] is self.classLevelFrameInfo
        for d in module.__dict__, f_globals:
            assert d is globals()


    def checkCallInfo(self):
        kind,module,f_locals,f_globals = getFrameInfo(sys._getframe())
        assert kind=="function call"
        assert f_locals is locals() # ???
        for d in module.__dict__, f_globals:
            assert d is globals()


    def checkClassExec(self):
        d = {'sys':sys, 'getFrameInfo':getFrameInfo}
        exec "class Foo: info=getFrameInfo(sys._getframe())" in d
        kind,module,f_locals,f_globals = d['Foo'].info
        assert kind=="class", kind


        
        




class MROTests(TestCase):

    def checkStdMRO(self):
        class foo(object): pass
        class bar(foo): pass
        class baz(foo): pass
        class spam(bar,baz): pass
        assert getMRO(spam) is spam.__mro__

    def checkClassicMRO(self):
        class foo: pass
        class bar(foo): pass
        class baz(foo): pass
        class spam(bar,baz): pass
        basicMRO = [spam,bar,foo,baz,foo]
        assert list(getMRO(spam)) == basicMRO
        assert list(getMRO(spam,True)) == basicMRO+[InstanceType,object]
























class AdviceTests(TestCase):

    def checkOrder(self):
        log = []
        class Foo:
            ping(log, 1)
            ping(log, 2)
            ping(log, 3)

        # Strip the list nesting
        for i in 1,2,3:
            assert isinstance(Foo,list)
            Foo, = Foo

        assert log == [
            (1, Foo),
            (2, [Foo]),
            (3, [[Foo]]),
        ]

    def checkOutside(self):
        try:
            ping([], 1)
        except SyntaxError:
            pass
        else:
            raise AssertionError(
                "Should have detected advice outside class body"
            )

    def checkDoubleType(self):
        if sys.hexversion >= 0x02030000:
            return  # you can't duplicate bases in 2.3
        class aType(type,type):
            ping([],1)
        aType, = aType
        assert aType.__class__ is type




    def checkSingleExplicitMeta(self):

        class M(type): pass

        class C(M):
            __metaclass__ = M
            ping([],1)

        C, = C
        assert C.__class__ is M


    def checkMixedMetas(self):

        class M1(type): pass
        class M2(type): pass

        class B1: __metaclass__ = M1
        class B2: __metaclass__ = M2

        try:
            class C(B1,B2):
                ping([],1)
        except TypeError:
            pass
        else:
            raise AssertionError("Should have gotten incompatibility error")

        class M3(M1,M2): pass

        class C(B1,B2):
            __metaclass__ = M3
            ping([],1)

        assert isinstance(C,list)
        C, = C
        assert isinstance(C,M3)




    def checkMetaOfClass(self):

        class metameta(type):
            pass

        class meta(type):
            __metaclass__ = metameta

        assert determineMetaclass((meta,type))==metameta





TestClasses = (
    SuperTest, DecoratorTests, AdviceTests, FrameInfoTest, MROTests,
)

def test_suite():
    return TestSuite([makeSuite(t,'check') for t in TestClasses])





















