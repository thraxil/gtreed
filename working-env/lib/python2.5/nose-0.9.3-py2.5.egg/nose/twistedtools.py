"""
Twisted integration
-------------------

This module provides a very simple way to integrate your tests with the
Twisted event loop.

You must import this module *before* importing anything from Twisted itself!

Example:
    from nose.twistedtools import reactor, deferred

    @deferred()
    def test_resolve():
        return reactor.resolve("nose.python-hosting.com")

Or, more realistically:

    @deferred(timeout=5.0)
    def test_resolve():
        d = reactor.resolve("nose.python-hosting.com")
        def check_ip(ip):
            assert ip == "67.15.36.43"
        d.addCallback(check_ip)
        return d

"""

import sys
from Queue import Queue, Empty

from nose.tools import make_decorator, TimeExpired

__all__ = [
    'threaded_reactor', 'reactor', 'deferred', 'TimeExpired',
]

_twisted_thread = None

def threaded_reactor():
    """
    Start the Twisted reactor in a separate thread, if not already done.
    Returns the reactor.
    The thread will automatically be destroyed when all the tests are done.
    """
    global _twisted_thread
    from twisted.internet import reactor
    if not _twisted_thread:
        from twisted.python import threadable
        from threading import Thread
        _twisted_thread = Thread(target=lambda: reactor.run( \
                installSignalHandlers=False))
        _twisted_thread.setDaemon(True)
        _twisted_thread.start()
    return reactor

# Export global reactor variable, as Twisted does
reactor = threaded_reactor()


def deferred(timeout=None):
    """
    By wrapping a test function with this decorator, you can return a
    twisted Deferred and the test will wait for the deferred to be triggered.
    The whole test function will run inside the Twisted event loop.

    The optional timeout parameter specifies the maximum duration of the test.
    The difference with timed() is that timed() will still wait for the test
    to end, while deferred() will stop the test when its timeout has expired.
    The latter is more desireable when dealing with network tests, because
    the result may actually never arrive.

    If the callback is triggered, the test has passed.
    If the errback is triggered or the timeout expires, the test has failed.

    Example:
        @deferred(timeout=5.0)
        def test_resolve():
            return reactor.resolve("nose.python-hosting.com")

    Attention! If you combine this decorator with other decorators (like
    "raises"), deferred() must be called *first*!

    In other words, this is good:
        @raises(DNSLookupError)
        @deferred()
        def test_error():
            return reactor.resolve("xxxjhjhj.biz")

    and this is bad:
        @deferred()
        @raises(DNSLookupError)
        def test_error():
            return reactor.resolve("xxxjhjhj.biz")
    """
    reactor = threaded_reactor()

    # Check for common syntax mistake
    # (otherwise, tests can be silently ignored
    # if one writes "@deferred" instead of "@deferred()")
    try:
        timeout is None or timeout + 0
    except TypeError:
        raise TypeError("'timeout' argument must be a number or None")

    def decorate(func):
        def wrapper(*args, **kargs):
            q = Queue()
            def callback(value):
                q.put(None)
            def errback(failure):
                # Retrieve and save full exception info
                try:
                    failure.raiseException()
                except:
                    q.put(sys.exc_info())
            def g():
                try:
                    d = func(*args, **kargs)
                    try:
                        d.addCallbacks(callback, errback)
                    # Check for a common mistake and display a nice error
                    # message
                    except AttributeError:
                        raise TypeError("you must return a twisted Deferred "
                                        "from your test case!")
                # Catch exceptions raised in the test body (from the
                # Twisted thread)
                except:
                    q.put(sys.exc_info())
            reactor.callFromThread(g)
            try:
                error = q.get(timeout=timeout)
            except Empty:
                raise TimeExpired("timeout expired before end of test (%f s.)"
                                  % timeout)
            # Re-raise all exceptions
            if error is not None:
                exc_type, exc_value, tb = error
                raise exc_type, exc_value, tb
        wrapper = make_decorator(func)(wrapper)
        return wrapper
    return decorate

