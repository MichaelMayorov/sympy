"""
Finite Discrete Random Variables Module

See Also
========
sympy.stats.frv_types
sympy.stats.rv
sympy.stats.crv
"""

from sympy import (And, Eq, Basic, S, Expr, Symbol, cacheit, sympify, Mul, Add,
        And, Or, Tuple)
from sympy.core.sets import FiniteSet
from rv import (RandomDomain, ProductDomain, ConditionalDomain, PSpace,
        ProductPSpace, random_symbols, sumsets, rv_subs)
import itertools
from sympy.core.containers import Dict
import random

class FiniteDomain(RandomDomain):
    """
    A domain with discrete finite support.
    Represented using a FiniteSet

    """
    is_Finite = True
    def __new__(cls, elements):
        elements = FiniteSet(*elements)
        symbols = FiniteSet(sym for sym, val in elements)
        return RandomDomain.__new__(cls, symbols, elements)

    @property
    def elements(self):
        return self.args[1]

    @property
    def dict(self):
        return FiniteSet(Dict(dict(el)) for el in self.elements)

    def __contains__(self, other):
        return other in self.elements

    def __iter__(self):
        return self.elements.__iter__()

    def as_boolean(self):
        return Or(*[And(*[Eq(sym, val) for sym, val in item]) for item in self])

class SingleFiniteDomain(FiniteDomain):
    """
    A FiniteDomain over a single symbol/set

    Example: The possibilities of a *single* die roll.
    """

    def __new__(cls, symbol, set):
        return RandomDomain.__new__(cls, (symbol, ), FiniteSet(*set))

    @property
    def symbol(self):
        return tuple(self.symbols)[0]
    @property
    def elements(self):
        return FiniteSet(frozenset(((self.symbol, elem), )) for elem in self.set)
    @property
    def set(self):
        return self.args[1]

    def __iter__(self):
        return (frozenset(((self.symbol, elem),)) for elem in self.set)

    def __contains__(self, other):
        sym, val = tuple(other)[0]
        return sym == self.symbol and val in self.set

class ProductFiniteDomain(ProductDomain, FiniteDomain):
    """
    A Finite domain consisting of several other FiniteDomains.

    Example: The possibilities of the rolls of three independent dice
    """

    def __iter__(self):
        proditer = itertools.product(*self.domains)
        return (sumsets(items) for items in proditer)

    @property
    def elements(self):
        return FiniteSet(iter(self))

class ConditionalFiniteDomain(ConditionalDomain, ProductFiniteDomain):
    """
    A FiniteDomain that has been restricted by a condition

    Example: The possibilities of a die roll under the condition that the
    roll is even.
    """

    def __init__(self, domain, condition):
        cond = rv_subs(condition)
        if not cond.free_symbols.issubset(domain.free_symbols):
            raise ValueError('Condition "%s" contains foreign symbols \n%s.\n'%(
                condition, tuple(cond.free_symbols-domain.free_symbols))+
                    "Will be unable to iterate using this condition")
        return ConditionalDomain(domain, condition)

    def _test(self, elem):
        val = self.condition.subs(dict(elem))
        if val in [True, False]:
            return val
        elif val.is_Equality:
            return val.lhs == val.rhs
        raise ValueError("Undeciable if %s"%str(val))

    def __contains__(self, other):
        return other in self.fulldomain and self._test(other)

    def __iter__(self):
        return (elem for elem in self.fulldomain if self._test(elem))

    @property
    def set(self):
        if self.fulldomain.__class__ is SingleFiniteDomain:
            return FiniteSet(elem for elem in self.fulldomain.set
                    if frozenset(((self.fulldomain.symbol, elem),)) in self)
        else:
            raise NotImplementedError(
                    "Not implemented on multi-dimensional conditional domain")
        #return FiniteSet(elem for elem in self.fulldomain if elem in self)

    def as_boolean(self):
        return FiniteDomain.as_boolean(self)

#=============================================
#=========  Probability Space  ===============
#=============================================

class FinitePSpace(PSpace):
    """
    A Finite Probability Space

    Represents the probabilities of a finite number of events
    """

    is_Finite = True
    def __new__(cls, domain, density):
        density = dict((sympify(key), sympify(val))
                for key, val in density.items())
        public_density = Dict(density)

        obj = PSpace.__new__(cls, domain, public_density)
        obj._density = density
        return obj

    def prob_of(self, elem):
        return self._density.get(elem,0)

    def where(self, condition):
        assert all(r.symbol in self.symbols for r in random_symbols(condition))
        return ConditionalFiniteDomain(self.domain, condition)

    def compute_density(self, expr):
        expr = expr.subs(dict(((rs, rs.symbol) for rs in self.values)))
        d = {}
        for elem in self.domain:
            val = expr.subs(dict(elem))
            prob = self.prob_of(elem)
            d[val] = d.get(val, 0) + prob
        return d

    @cacheit
    def compute_cdf(self, expr):
        d = self.compute_density(expr)
        cum_prob = 0
        cdf = []
        for key, prob in sorted(d.items()):
            cum_prob += prob
            cdf.append((key, cum_prob))

        return dict(cdf)

    @cacheit
    def sorted_cdf(self, expr, python_float=False):
        cdf = sorted(self.compute_cdf(expr).items(), key=lambda x: x[1])
        if python_float:
            cdf = [(v, float(cum_prob)) for v, cum_prob in cdf]
        return cdf

    def integrate(self, expr, rvs=None):
        rvs = rvs or self.values
        expr = expr.subs(dict((rs, rs.symbol) for rs in rvs))
        return sum(expr.subs(dict(elem)) * self.prob_of(elem)
                for elem in self.domain)

    def P(self, condition):
        cond_symbols = frozenset(rs.symbol for rs in random_symbols(condition))
        assert cond_symbols.issubset(self.symbols)
        return sum(self.prob_of(elem) for elem in self.where(condition))

    def conditional_space(self, condition):
        domain = self.where(condition)
        prob = self.P(condition)
        density = dict((key, val / prob)
                for key, val in self._density.items() if key in domain)
        return FinitePSpace(domain, density)

    def sample(self):
        """
        Internal sample method.
        Returns dictionary mapping RandomSymbol to realization value
        """
        expr = Tuple(*self.values)
        cdf = self.sorted_cdf(expr, python_float=True)

        x = random.uniform(0,1)
        # Find first occurence with cumulative probability less than x
        # This should be replaced with binary search
        for value, cum_prob in cdf:
            if x < cum_prob:
                # return dictionary mapping RandomSymbols to values
                return dict(zip(expr, value))

        assert False, "We should never have gotten to this point"

class SingleFinitePSpace(FinitePSpace):
    """
    A single finite probability space

    Represents the probabilities of a set of random events that can be
    attributed to a single variable/symbol.

    This class is implemented by many of the standard FiniteRV types such as
    Die, Bernoulli, Coin, etc....
    """
    _count = 0
    _name = 'fx'

    @property
    def value(self):
        return tuple(self.values)[0]

def create_SingleFinitePSpace(density, symbol=None, cls = SingleFinitePSpace):
    symbol = symbol or cls.create_symbol()
    domain = SingleFiniteDomain(symbol, frozenset(density.keys()))
    density = dict((frozenset(((symbol, val),)) , prob)
            for val, prob in density.items())
    density = Dict(density)
    return FinitePSpace.__new__(cls, domain, density)

class ProductFinitePSpace(ProductPSpace, FinitePSpace):
    """
    A collection of several independent finite probability spaces
    """
    @property
    def domain(self):
        return ProductFiniteDomain(*[space.domain for space in self.spaces])
    @property
    @cacheit
    def _density(self):
        proditer = itertools.product(*[space._density.iteritems()
            for space in self.spaces])
        d = {}
        for items in proditer:
            elems, probs = zip(*items)
            elem = sumsets(elems)
            prob = Mul(*probs)
            d[elem] = d.get(elem, 0) + prob
        return Dict(d)

    @property
    @cacheit
    def density(self):
        return Dict(self._density)
