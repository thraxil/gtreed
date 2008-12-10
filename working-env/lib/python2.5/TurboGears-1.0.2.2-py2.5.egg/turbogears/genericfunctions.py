import sys
from itertools import izip, repeat, chain as ichain

from dispatch import strategy, functions


class MultiorderGenericFunction(functions.GenericFunction):

    """Generic function allowing a priori method ordering."""

    def __init__(self, func):
        functions.GenericFunction.__init__(self, func)
        self.order_when = []
        self.order_around = []

    def when(self, cond, order=0):
        if order not in self.order_when:
            self.order_when.append(order)
            self.order_when.sort()
        return self._decorate(cond, "primary%d" % order)

    def around(self, cond, order=0):
        if order not in self.order_around:
            self.order_around.append(order)
            self.order_around.sort()
        return self._decorate(cond, "around%d" % order)

    # Based on dispatch.functions.GenericFunction.combine
    def combine(self, cases):
        strict = [strategy.ordered_signatures,strategy.safe_methods]
        loose  = [strategy.ordered_signatures,strategy.all_methods]

        primary_names = ['primary%d' % order for order in self.order_when]
        around_names = ['around%d' % order for order in self.order_around]

        cases = strategy.separate_qualifiers(
            cases,
            before = loose, after =loose,
            **dict(izip(ichain(primary_names, around_names), repeat(strict)))
        )

        primary = strategy.method_chain(ichain(
                    *[cases.get(primary, []) for primary in primary_names]))

        if cases.get('after') or cases.get('before'):

            befores = strategy.method_list(cases.get('before',[]))
            afters = strategy.method_list(list(cases.get('after',[]))[::-1])

            def chain(*args,**kw):
                for tmp in befores(*args,**kw): pass  # toss return values
                result = primary(*args,**kw)
                for tmp in afters(*args,**kw): pass  # toss return values
                return result

        else:
            chain = primary

        if (self.order_around):
            chain = strategy.method_chain(ichain(*([cases.get(around, [])
                                    for around in around_names] + [[chain]])))

        return chain


def getter(var):
    """Create an accessor for given variable."""
    frame = sys._getframe(1)
    return lambda: var in frame.f_locals and frame.f_locals[var] or \
                                             frame.f_globals[var]

__all__ = ["MultiorderGenericFunction", "getter", ]
