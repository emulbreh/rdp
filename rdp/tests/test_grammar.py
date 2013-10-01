import unittest
from operator import itemgetter

from rdp import (GrammarBuilder, Grammar, flatten, drop, epsilon, repeat, Terminal,
    Regexp, Parser, LeftRecursion, ParseError, Optional, Lookahead, ignore, keep)
from rdp.formatter import GrammarFormatter
from rdp import builtins
from rdp.utils import product, uncurry


class GrammarBuilderTest(unittest.TestCase):
    def test_alias(self):
        g = GrammarBuilder()
        g.foo = "foo"
        g.bar = "bar"
        g.foo2 = g.foo
        g.bar2 = g.bar
        g.whitespace = builtins.whitespace
        g.start = g.foo | g.bar
        g.start2 = g.foo2 | g.bar2
        
        grammar = g(start=g.start, tokenize=[ignore(g.whitespace)])
        self.assertEqual(grammar.parse("foo").tuple_tree(), ('start', [('foo', 'foo')]))
        
        grammar = g(start=g.start2, tokenize=[ignore(g.whitespace)])
        self.assertEqual(grammar.parse("foo").tuple_tree(), ('start2', [('foo2', 'foo')]))
