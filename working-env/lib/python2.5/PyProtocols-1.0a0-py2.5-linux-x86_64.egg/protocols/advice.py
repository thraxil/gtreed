from __future__ import generators
from new import instancemethod
from types import ClassType, FunctionType, InstanceType
import sys

__all__ = [
    'addClassAdvisor', 'isClassAdvisor', 'metamethod', 'supermeta',
    'minimalBases', 'determineMetaclass', 'getFrameInfo', 'getMRO',
    'classicMRO', 'mkRef', 'StrongRef', 'add_assignment_advisor',
]


def metamethod(func):
    """Wrapper for metaclass method that might be confused w/instance method"""
    return property(lambda ob: func.__get__(ob,ob.__class__))


try:
    from ExtensionClass import ExtensionClass
except ImportError:
    ClassicTypes = ClassType
else:
    ClassicTypes = ClassType, ExtensionClass


















def classicMRO(ob, extendedClassic=False):
    stack = []
    push = stack.insert
    pop = stack.pop
    push(0,ob)
    while stack:
        cls = pop()
        yield cls
        p = len(stack)
        for b in cls.__bases__: push(p,b)
    if extendedClassic:
        yield InstanceType
        yield object


def getMRO(ob, extendedClassic=False):

    if isinstance(ob,ClassicTypes):
        return classicMRO(ob,extendedClassic)

    elif isinstance(ob,type):
        return ob.__mro__

    return ob,

try:
    from _speedups import metamethod, getMRO, classicMRO
except ImportError:
    pass












# property-safe 'super()' for Python 2.2; 2.3 can use super() instead

def supermeta(typ,ob):

    starttype = type(ob)
    mro = starttype.__mro__
    if typ not in mro:
        starttype = ob
        mro = starttype.__mro__

    mro = iter(mro)
    for cls in mro:
        if cls is typ:
            mro = [cls.__dict__ for cls in mro]
            break
    else:
        raise TypeError("Not sub/supertypes:", starttype, typ)

    typ = type(ob)

    class theSuper(object):

        def __getattribute__(self,name):
            for d in mro:
                if name in d:
                    descr = d[name]
                    try:
                        descr = descr.__get__
                    except AttributeError:
                        return descr
                    else:
                        return descr(ob,typ)
            return object.__getattribute__(self,name)

    return theSuper()






def getFrameInfo(frame):
    """Return (kind,module,locals,globals) for a frame

    'kind' is one of "exec", "module", "class", "function call", or "unknown".
    """

    f_locals = frame.f_locals
    f_globals = frame.f_globals

    sameNamespace = f_locals is f_globals
    hasModule = '__module__' in f_locals
    hasName = '__name__' in f_globals

    sameName = hasModule and hasName
    sameName = sameName and f_globals['__name__']==f_locals['__module__']

    module = hasName and sys.modules.get(f_globals['__name__']) or None

    namespaceIsModule = module and module.__dict__ is f_globals

    if not namespaceIsModule:
        # some kind of funky exec
        kind = "exec"
        if hasModule and not sameNamespace:
            kind="class"
    elif sameNamespace and not hasModule:
        kind = "module"
    elif sameName and not sameNamespace:
        kind = "class"
    elif not sameNamespace:
        kind = "function call"
    else:
        # How can you have f_locals is f_globals, and have '__module__' set?
        # This is probably module-level code, but with a '__module__' variable.
        kind = "unknown"

    return kind,module,f_locals,f_globals




def addClassAdvisor(callback, depth=2,frame=None):

    """Set up 'callback' to be passed the containing class upon creation

    This function is designed to be called by an "advising" function executed
    in a class suite.  The "advising" function supplies a callback that it
    wishes to have executed when the containing class is created.  The
    callback will be given one argument: the newly created containing class.
    The return value of the callback will be used in place of the class, so
    the callback should return the input if it does not wish to replace the
    class.

    The optional 'depth' argument to this function determines the number of
    frames between this function and the targeted class suite.  'depth'
    defaults to 2, since this skips this function's frame and one calling
    function frame.  If you use this function from a function called directly
    in the class suite, the default will be correct, otherwise you will need
    to determine the correct depth yourself.

    This function works by installing a special class factory function in
    place of the '__metaclass__' of the containing class.  Therefore, only
    callbacks *after* the last '__metaclass__' assignment in the containing
    class will be executed.  Be sure that classes using "advising" functions
    declare any '__metaclass__' *first*, to ensure all callbacks are run."""

    frame = frame or sys._getframe(depth)
    kind, module, caller_locals, caller_globals = getFrameInfo(frame)

    if kind != "class":
        raise SyntaxError(
            "Advice must be in the body of a class statement"
        )

    previousMetaclass = caller_locals.get('__metaclass__')
    defaultMetaclass  = caller_globals.get('__metaclass__', ClassType)






    def advise(name,bases,cdict):

        if '__metaclass__' in cdict:
            del cdict['__metaclass__']

        if previousMetaclass is None:
             if bases:
                 # find best metaclass or use global __metaclass__ if no bases
                 meta = determineMetaclass(bases)
             else:
                 meta = defaultMetaclass

        elif isClassAdvisor(previousMetaclass):
            # special case: we can't compute the "true" metaclass here,
            # so we need to invoke the previous metaclass and let it
            # figure it out for us (and apply its own advice in the process)
            meta = previousMetaclass

        else:
            meta = determineMetaclass(bases, previousMetaclass)

        newClass = meta(name,bases,cdict)

        # this lets the callback replace the class completely, if it wants to
        return callback(newClass)

    # introspection data only, not used by inner function
    advise.previousMetaclass = previousMetaclass
    advise.callback = callback

    # install the advisor
    caller_locals['__metaclass__'] = advise


def isClassAdvisor(ob):
    """True if 'ob' is a class advisor function"""
    return isinstance(ob,FunctionType) and hasattr(ob,'previousMetaclass')




def add_assignment_advisor(callback,depth=2,frame=None):
    """Invoke 'callback(frame,name,value,old_locals)' on next assign in 'frame'

    The frame monitored is determined by the 'depth' argument, which gets
    passed to 'sys._getframe()'.  When 'callback' is invoked, 'old_locals'
    contains a copy of the frame's local variables as they were before the
    assignment took place, allowing the callback to access the previous value
    of the assigned variable, if any.  The callback's return value will become
    the new value of the variable.  'name' is the name of the variable being
    created or modified, and 'value' is its value (the same as
    'frame.f_locals[name]').

    This function also returns a decorator function for forward-compatibility
    with Python 2.4 '@' syntax.  Note, however, that if the returned decorator
    is used with Python 2.4 '@' syntax, the callback 'name' argument may be
    'None' or incorrect, if the 'value' is not the original function (e.g.
    when multiple decorators are used).
    """
    frame = frame or sys._getframe(depth)
    oldtrace = [frame.f_trace]
    old_locals = frame.f_locals.copy()

    def tracer(frm,event,arg):
        if event=='call':
            # We don't want to trace into any calls
            if oldtrace[0]:
                # ...but give the previous tracer a chance to, if it wants
                return oldtrace[0](frm,event,arg)
            else:
                return None

        try:
            if frm is frame and event !='exception':
                # Aha, time to check for an assignment...
                for k,v in frm.f_locals.items():
                    if k not in old_locals or old_locals[k] is not v:
                        break
                else:
                    # No luck, keep tracing
                    return tracer

                # Got it, fire the callback, then get the heck outta here...
                frm.f_locals[k] = callback(frm,k,v,old_locals)

        finally:
            # Give the previous tracer a chance to run before we return
            if oldtrace[0]:
                # And allow it to replace our idea of the "previous" tracer
                oldtrace[0] = oldtrace[0](frm,event,arg)

        uninstall()
        return oldtrace[0]

    def uninstall():
        # Unlink ourselves from the trace chain.
        frame.f_trace = oldtrace[0]
        sys.settrace(oldtrace[0])
        
    # Install the trace function
    frame.f_trace = tracer
    sys.settrace(tracer)

    def do_decorate(f):
        # Python 2.4 '@' compatibility; call the callback 
        uninstall()
        frame = sys._getframe(1)
        return callback(
            frame, getattr(f,'__name__',None), f, frame.f_locals
        )

    return do_decorate











def determineMetaclass(bases, explicit_mc=None):

    """Determine metaclass from 1+ bases and optional explicit __metaclass__"""

    meta = [getattr(b,'__class__',type(b)) for b in bases]

    if explicit_mc is not None:
        # The explicit metaclass needs to be verified for compatibility
        # as well, and allowed to resolve the incompatible bases, if any
        meta.append(explicit_mc)

    if len(meta)==1:
        # easy case
        return meta[0]

    candidates = minimalBases(meta) # minimal set of metaclasses

    if not candidates:
        # they're all "classic" classes
        return ClassType

    elif len(candidates)>1:
        # We could auto-combine, but for now we won't...
        raise TypeError("Incompatible metatypes",bases)

    # Just one, return it
    return candidates[0]














def minimalBases(classes):
    """Reduce a list of base classes to its ordered minimum equivalent"""

    classes = [c for c in classes if c is not ClassType]
    candidates = []

    for m in classes:
        for n in classes:
            if issubclass(n,m) and m is not n:
                break
        else:
            # m has no subclasses in 'classes'
            if m in candidates:
                candidates.remove(m)    # ensure that we're later in the list
            candidates.append(m)

    return candidates
























from weakref import ref

class StrongRef(object):

    """Like a weakref, but for non-weakrefable objects"""

    __slots__ = 'referent'

    def __init__(self,referent):
        self.referent = referent

    def __call__(self):
        return self.referent

    def __hash__(self):
        return hash(self.referent)

    def __eq__(self,other):
        return self.referent==other

    def __repr__(self):
        return 'StrongRef(%r)' % self.referent


def mkRef(ob,*args):
    """Return either a weakref or a StrongRef for 'ob'

    Note that extra args are forwarded to weakref.ref() if applicable."""

    try:
        return ref(ob,*args)
    except TypeError:
        return StrongRef(ob)








