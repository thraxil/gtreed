"""Basic test setups"""

__all__ = [
    'TestBase', 'ImplementationChecks', 'ProviderChecks',
    'InstanceImplementationChecks', 'makeClassTests', 'ClassProvidesChecks',
    'AdaptiveChecks', 'SimpleAdaptiveChecks', 'makeMetaClassProvidesTests',
    'BasicClassProvidesChecks',
]

from unittest import TestCase, makeSuite, TestSuite
from protocols import *


# Dummy interfaces and adapters used in tests

def a1(ob):
    return 'a1',ob

def a2(ob):
    return 'a2',ob





















class TestBase(TestCase):

    """Non-adapter instance tests"""

    a1 = staticmethod(a1)
    a2 = staticmethod(a2)

    def assertObProvidesOnlyA(self):
        assert self.IA(self.ob, None) is self.ob
        assert self.IB(self.ob, None) is None
        assert self.IA(None, None) is None
        assert adapt(self.IB, None, None) is None
        assert adapt(self.ob, None, None) is None

    def assertObProvidesAandB(self):
        assert self.IA(self.ob, None) is self.ob
        assert self.IB(self.ob, None) is self.ob
        assert adapt(self.IA, None, None) is None
        assert adapt(self.IB, None, None) is None
        assert adapt(self.ob, None, None) is None

    def assertAmbiguous(self, a1, a2, d1, d2, ifaces):
        try:
            self.declareObAdapts(a2,ifaces)
        except TypeError,v:
            assert v.args == ("Ambiguous adapter choice", a1, a2, d1, d2)

    def make(self,klass):
        # This is overridden by tests where 'klass' is a metaclass
        return klass()

    def assertObProvidesSubsetOfA(self):
        # Assert that self.ob provides a new subset of self.IA
        # (Caller must ensure that self.ob provides self.IA)
        class IC(self.Interface):
            advise(protocolIsSubsetOf=[self.IA])
            if 'self' in locals():
                del locals()['self']  # how the heck???
        assert IC(self.ob, None) is self.ob


    def setupBases(self,base):
        class M1(base): pass
        class M2(base): pass
        return M1, M2


    def assertM1ProvidesOnlyAandM2ProvidesB(self,M1,M2):
        assert self.IA(M1,None) is M1
        assert self.IB(M1,None) is None
        assert self.IB(M2,None) is M2


    def assertChangingBasesChangesInterface(self,M1,M2,m1,m2):
        try:
            M1.__bases__ = M2,
        except TypeError:   # XXX 2.2 doesn't let newstyle __bases__ change
            pass
        else:
            assert self.IA(m1,None) is m1
            assert self.IB(m1,None) is m1

    def assertObProvidesABCD(self,IC,ID):
        assert self.IA(self.ob, None) is self.ob
        assert self.IB(self.ob, None) is self.ob
        assert IC(self.ob, None) is self.ob
        assert ID(self.ob, None) is self.ob

    def assertObProvidesCandDnotAorB(self,IC,ID):
        assert self.IA(self.ob, None) is None
        assert self.IB(self.ob, None) is None
        assert IC(self.ob, None) is self.ob
        assert ID(self.ob, None) is self.ob









class ProviderChecks(TestBase):

    """Non-adapter specific-object-provides checks"""

    def declareObImplements(self,ifaces):
        adviseObject(self.ob, provides=ifaces)

    def declareObAdapts(self,factory,ifaces):
        declareAdapter(factory,provides=ifaces,forObjects=[self.ob])

    def checkSimpleRegister(self):
        self.declareObImplements([self.IA])
        self.assertObProvidesOnlyA()

    def checkImpliedRegister(self):
        self.declareObImplements([self.IB])
        self.assertObProvidesAandB()
























class SimpleAdaptiveChecks:

    """Simple adapter-oriented checks that Twisted can handle

    (Well, it handles them as long as all the interfaces are Twisted)"""

    def checkDelayedImplication(self):
        self.declareObImplements([self.IA])
        self.assertObProvidesSubsetOfA()


    def checkIndirectImplication(self):

        # Zope fails this because it does not support adding after-the-fact
        # implication.

        # IB->IA + ID->IC + IC->IB = ID->IA

        class IC(self.Interface): pass
        class ID(IC):             pass

        self.declareObImplements([ID])
        self.assertObProvidesCandDnotAorB(IC,ID)

        declareAdapter(
            NO_ADAPTER_NEEDED, provides=[self.IB], forProtocols=[IC]
        )

        self.assertObProvidesABCD(IC,ID)












class AdaptiveChecks(SimpleAdaptiveChecks):

    """General adapter/protocol implication checks

    Twisted can't handle these."""

    def checkAmbiguity(self):
        self.declareObAdapts(self.a1,[self.IA])
        self.assertAmbiguous(self.a1,self.a2,1,1,[self.IA])

    def checkOverrideDepth(self):
        self.declareObAdapts(self.a1,[self.IB])
        assert self.IA(self.ob,None) == ('a1',self.ob)

        self.declareObAdapts(self.a2,[self.IA])
        assert self.IA(self.ob,None) == ('a2',self.ob)


    def checkComposed(self):
        class IC(self.Interface): pass
        declareAdapter(self.a2,provides=[IC],forProtocols=[self.IA])
        self.declareObAdapts(self.a1,[self.IA])
        assert IC(self.ob,None) == ('a2',('a1',self.ob))


    def checkLateDefinition(self):
        # Zope fails this because it has different override semantics

        self.declareObAdapts(DOES_NOT_SUPPORT, [self.IA])
        assert self.IA(self.ob,None) is None

        self.declareObImplements([self.IA])
        assert self.IA(self.ob,None) is self.ob

        # NO_ADAPTER_NEEDED at same depth should override DOES_NOT_SUPPORT
        self.declareObAdapts(DOES_NOT_SUPPORT, [self.IA])
        assert self.IA(self.ob,None) is self.ob




class InstanceImplementationChecks(TestBase):

    """Non-adapter class-instances-provide checks"""

    # Everybody can handle these

    def declareObImplements(self,ifaces):
        declareImplementation(self.klass, ifaces)

    def declareObAdapts(self,factory,ifaces):
        declareAdapter(factory,provides=ifaces,forTypes=[self.klass])

    def checkSimpleRegister(self):
        self.declareObImplements([self.IA])
        self.assertObProvidesOnlyA()

    def checkImpliedRegister(self):
        self.declareObImplements([self.IB])
        self.assertObProvidesAandB()


class ImplementationChecks(InstanceImplementationChecks):

    """Non-adapter class-instances vs. class-provide checks"""

    # Twisted fails these tests because it has no way to distinguish the
    # interfaces an object provides from the interfaces its class provides

    def checkNoClassPassThru(self):
        self.declareObImplements([self.IA])
        assert self.IA(self.klass, None) is None

    def checkInheritedDeclaration(self):
        self.declareObImplements([self.IB])
        class Sub(self.klass): pass
        inst = self.make(Sub)
        assert self.IB(inst,None) is inst
        assert self.IA(inst,None) is inst
        assert self.IA(Sub,None) is None   # check not passed up to class
        assert self.IB(Sub,None) is None

    def checkRejectInheritanceAndReplace(self):
        self.declareObImplements([self.IB])

        class Sub(self.klass): advise(instancesDoNotProvide=[self.IB])
        inst = self.make(Sub)
        assert self.IA(inst,None) is inst
        assert self.IB(inst,None) is None

        declareImplementation(Sub, instancesProvide=[self.IB])
        assert self.IB(inst,None) is inst































class BasicClassProvidesChecks:

    """Object-provides checks for classes and types"""

    # Twisted doesn't support these because it makes no object/type distinction

    def checkNoInstancePassThru(self):
        inst = self.ob()
        adviseObject(self.ob, provides=[self.IA])
        assert self.IA(inst, None) is None

    def checkChangingBases(self):
        M1, M2 = self.setupBases(self.ob)
        adviseObject(M1, provides=[self.IA])
        adviseObject(M2, provides=[self.IB])
        self.assertM1ProvidesOnlyAandM2ProvidesB(M1,M2)
        self.assertChangingBasesChangesInterface(M1,M2,M1,M2)


class ClassProvidesChecks(BasicClassProvidesChecks):

    # Twisted doesn't support these because it makes no object/type distinction

    def checkInheritedDeclaration(self):
        class Sub(self.ob): pass
        adviseObject(self.ob, provides=[self.IB])
        assert self.IB(Sub, None) is Sub
        assert self.IA(Sub, None) is Sub


    def checkRejectInheritanceAndReplace(self):
        adviseObject(self.ob, provides=[self.IB])

        class Sub(self.ob): advise(classDoesNotProvide=[self.IB])

        assert self.IA(Sub,None) is Sub
        assert self.IB(Sub,None) is None

        adviseObject(Sub,provides=[self.IB])
        assert self.IB(Sub,None) is Sub

def makeInstanceTests(base,Picklable,NewStyle):

    """Generate a set of instance-oriented test classes using 'base'"""

    class AdviseFunction(base):
        def setUp(self):
            def aFunc(foo,bar):
                pass
            self.ob = aFunc

    class AdviseModule(base):
        def setUp(self):
            from types import ModuleType
            self.ob = ModuleType('x')

    class AdviseInstance(base):
        def setUp(self):
            self.ob = Picklable()

        def checkPickling(self):
            from cPickle import loads,dumps     # pickle has a bug!
            adviseObject(self.ob, provides=[self.IPure])
            newOb = loads(dumps(self.ob))
            assert self.IPure(newOb,None) is newOb

    class AdviseNewInstance(AdviseInstance):
        def setUp(self):
            self.ob = NewStyle()

    return AdviseFunction, AdviseModule, AdviseInstance, AdviseNewInstance











def makeClassProvidesTests(base):
    """Generate a set of class-provides-oriented test classes using 'base'"""

    class AdviseClass(base):
        def setUp(self):
            class Classic:
                pass
            self.ob = Classic

    class AdviseType(AdviseClass):
        def setUp(self):
            class Class(object):
                pass
            self.ob = Class

    return AdviseClass, AdviseType


def makeMetaClassProvidesTests(base):
    """Generate a set of class-provides-oriented test classes using 'base'"""

    # Notice that we don't test the *metaclass* of the next two configurations;
    # it would fail because the metaclass itself can't be adapted to an open
    # provider, because it has a __conform__ method (from ProviderMixin).  For
    # that to work, there'd have to be *another* metalevel.

    class AdviseMixinClass(base):
        def setUp(self):
            class Meta(ProviderMixin, type): pass
            class Test(object): __metaclass__ = Meta
            self.ob = Test

    class AdviseMixinMultiMeta2(base):
        def setUp(self):
            class Meta(ProviderMixin, type): pass
            class Test(ProviderMixin,object): __metaclass__ = Meta
            self.ob = Test

    return AdviseMixinClass, AdviseMixinMultiMeta2


def makeClassTests(base):

    """Generate a set of class-oriented test classes using 'base'"""

    class TestClassic(base):

        def setUp(self):
            class Classic: pass
            self.klass = Classic
            self.ob = Classic()

    class TestBuiltin(base):

        def setUp(self):
            # Note: We need a type with a no-arguments constructor
            class Newstyle(list): __slots__ = ()
            self.klass = Newstyle
            self.ob = Newstyle()

    class TestMetaclass(base):

        def setUp(self):
            class Meta(type): pass
            self.klass = Meta
            class Base(object): __metaclass__ = Meta
            self.ob = Base

        def make(self,klass):
            return klass('Dummy',(object,),{})

    class TestMetaInstance(base):

        def setUp(self):
            class Meta(type): pass
            class Base(object): __metaclass__ = Meta
            self.klass = Base
            self.ob = Base()

    return TestClassic, TestBuiltin, TestMetaclass, TestMetaInstance


