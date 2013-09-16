import unittest

from rdp import (GrammarBuilder, flatten, drop, epsilon, Repeat, Terminal, Regexp, Parser)
from rdp import builtins


class Builtins(unittest.TestCase):
    def assert_lexemes_equal(self, grammar, source, lexemes):
        tokens = grammar.tokenize(source)
        self.assertEqual([t.lexeme for t in tokens], list(lexemes))
        
    def assert_lexeme(self, grammar, source):
        self.assert_lexemes_equal(grammar, source, [source])
    
    def test_double_quoted_strings(self):
        g = GrammarBuilder()
        g.string = builtins.double_quoted_string
        grammar = g(start=g.string)
        
        self.assert_lexeme(grammar, '"foo"')
        self.assert_lexeme(grammar, '"say:\\"foo\\""')
        self.assert_lexeme(grammar, '"say\\\":\\"foo\\""')

    def test_single_quoted_strings(self):
        g = GrammarBuilder()
        g.string = builtins.single_quoted_string
        grammar = g(start=g.string)

        self.assert_lexeme(grammar, "'foo'")
        self.assert_lexeme(grammar, "'say:\\'foo\\''")
        self.assert_lexeme(grammar, "'say\\\\':\\'foo\\''")
        self.assert_lexeme(grammar, "'say\\\\':\\'foo\\''")

