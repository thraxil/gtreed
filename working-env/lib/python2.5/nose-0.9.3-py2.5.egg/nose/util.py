"""Utility functions and classes used by nose internally.
"""
import inspect
import logging
import os
import re
import sys
import types
import unittest
from compiler.consts import CO_GENERATOR

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from nose.config import Config

log = logging.getLogger('nose')

def absdir(path):
    """Return absolute, normalized path to directory, if it exists; None
    otherwise.
    """
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.abspath(os.path.join(os.getcwd(),
                                                             path)))
    if path is None or not os.path.isdir(path):
        return None
    return path


def absfile(path, where=None):
    """Return absolute, normalized path to file (optionally in directory
    where), or None if the file can't be found either in where or the current
    working directory.
    """
    orig = path
    if where is None:
        where = os.getcwd()
    if isinstance(where, list) or isinstance(where, tuple):
        for maybe_path in where:
            maybe_abs = absfile(path, maybe_path)
            if maybe_abs is not None:
                return maybe_abs
        return None
    if not os.path.isabs(path):
        path = os.path.normpath(os.path.abspath(os.path.join(where, path)))
    if path is None or not os.path.exists(path):
        if where != os.getcwd():
            # try the cwd instead
            path = os.path.normpath(os.path.abspath(os.path.join(os.getcwd(),
                                                                 orig)))
    if path is None or not os.path.exists(path):
        return None
    if os.path.isdir(path):
        # might want an __init__.py from pacakge
        init = os.path.join(path,'__init__.py')
        if os.path.isfile(init):
            return init
    elif os.path.isfile(path):
        return path
    return None


def anyp(predicate, iterable):
    for item in iterable:
        if predicate(item):
            return True
    return False


def file_like(name):
    return os.path.dirname(name) or name.endswith('.py')


def func_lineno(func):
    """Get the line number of a function. First looks for
    compat_co_firstlineno, then func_code.co_first_lineno.
    """
    try:
        return func.compat_co_firstlineno
    except AttributeError:
        return func.func_code.co_firstlineno


def is_generator(func):
    try:
        return func.func_code.co_flags & CO_GENERATOR != 0
    except AttributeError:
        return False

    
def split_test_name(test):
    """Split a test name into a 3-tuple containing file, module, and callable
    names, any of which (but not all) may be blank.

    Test names are in the form:

    file_or_module:callable

    Either side of the : may be dotted. To change the splitting behavior, you
    can alter nose.util.split_test_re.
    """
    parts = test.split(':')
    num = len(parts)
    if num == 1:
        # only a file or mod part
        if file_like(test):
            return (test, None, None)
        else:
            return (None, test, None)
    elif num >= 3:
        # definitely popped off a windows driveletter
        file_or_mod = ':'.join(parts[0:-1])
        fn = parts[-1]
    else:
        # only a file or mod part, or a test part, or
        # we mistakenly split off a windows driveletter
        file_or_mod, fn = parts
        if len(file_or_mod) == 1:
            # windows drive letter: must be a file
            if not file_like(fn):
                raise ValueError("Test name '%s' is ambiguous; can't tell "
                                 "if ':%s' refers to a module or callable"
                                 % (test, fn))
            return (test, None, None)        
    if file_or_mod:
        if file_like(file_or_mod):
            return (file_or_mod, None, fn)
        else:
            return (None, file_or_mod, fn)
    else:
        return (None, None, fn)

    
def test_address(test):
    """Find the test address for a test, which may be a module, filename,
    class, method or function.
    """
    # type-based polymorphism sucks in general, but I believe is
    # appropriate here
    t = type(test)
    if t == types.ModuleType:
        return (os.path.abspath(test.__file__), test.__name__)
    if t == types.FunctionType:
        m = sys.modules[test.__module__]
        return (os.path.abspath(m.__file__), test.__module__, test.__name__)
    if t in (type, types.ClassType):
        m = sys.modules[test.__module__]
        return (os.path.abspath(m.__file__), test.__module__, test.__name__)
    if t == types.InstanceType:
        return test_address(test.__class__)
    if t == types.MethodType:
        cls_adr = test_address(test.im_class)
        return (cls_adr[0], cls_adr[1],
                "%s.%s" % (cls_adr[2], test.__name__))
    # handle unittest.TestCase instances
    if isinstance(test, unittest.TestCase):
        if hasattr(test, 'testFunc'):
            # nose FunctionTestCase
            return test_address(test.testFunc)
        if hasattr(test, '_FunctionTestCase__testFunc'):
            # unittest FunctionTestCase
            return test_address(test._FunctionTestCase__testFunc)
        if hasattr(test, 'testCase'):
            # nose MethodTestCase
            return test_address(test.testCase)
        # regular unittest.TestCase
        cls_adr = test_address(test.__class__)
        # 2.5 compat: __testMethodName changed to _testMethodName
        try:
            method_name = test._TestCase__testMethodName
        except AttributeError:
            method_name = test._testMethodName
        return (cls_adr[0], cls_adr[1],
                "%s.%s" % (cls_adr[2], method_name))
    raise TypeError("I don't know what %s is (%s)" % (test, t))


def try_run(obj, names):
    """Given a list of possible method names, try to run them with the
    provided object. Keep going until something works. Used to run
    setup/teardown methods for module, package, and function tests.
    """
    for name in names:
        func = getattr(obj, name, None)
        if func is not None:
            if type(obj) == types.ModuleType:
                # py.test compatibility
                try:
                    args, varargs, varkw, defaults = inspect.getargspec(func)
                except TypeError:
                    # Not a function. If it's callable, call it anyway
                    if hasattr(func, '__call__'):
                        func = func.__call__
                    try:
                        args, varargs, varkw, defaults = \
                            inspect.getargspec(func)
                        args.pop(0) # pop the self off
                    except TypeError:
                        raise TypeError("Attribute %s of %r is not a python "
                                        "function. Only functions or callables"
                                        " may be used as fixtures." %
                                        (name, obj))                    
                if len(args):
                    log.debug("call fixture %s.%s(%s)", obj, name, obj)    
                    return func(obj)
            log.debug("call fixture %s.%s", obj, name)
            return func()

        
def tolist(val):
    """Convert a value that may be a list or a (possibly comma-separated)
    string into a list. The exception: None is returned as None, not [None].
    """
    if val is None:
        return None
    try:
        # might already be a list
        val.extend([])
        return val
    except AttributeError:
        pass
    # might be a string
    try:
        return re.split(r'\s*,\s*', val)
    except TypeError:
        # who knows... 
        return list(val)
