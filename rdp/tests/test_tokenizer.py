import unittest
import textwrap
import re

from rdp import GrammarBuilder, flatten, drop, epsilon, repeat, Terminal, Regexp, Parser, epsilon, Optional, ignore
from rdp.formatter import GrammarFormatter
from rdp import builtins
from rdp.indention import indent, INDENT, DEDENT


class TokenizerTest(unittest.TestCase):
    def test_indention_tokenizer(self):
        g = GrammarBuilder()
        g.whitespace = Regexp(r'\s+')
        g.block = INDENT + repeat(g.expr) + DEDENT
        g.label = Regexp(r'\w+')
        g.expr = g.label + Optional(g.block) | g.label + '(' + g.expr + ')'
        grammar = g(
            start=g.expr, 
            tokenize=[
                indent('(', ')'),
                ignore(g.whitespace),
            ]
        )

        format = GrammarFormatter()

        source = textwrap.dedent("""
        foo
            bar
            baz
                boo
            x
            y
        """).strip()

        self.assertEqual(
            [t.lexeme or t.symbol.name for t in grammar.tokenize(source)],
            ['foo', 'INDENT', 'bar', 'baz', 'INDENT', 'boo', 'DEDENT', 'x', 'y', 'DEDENT']
        )
        
        source = textwrap.dedent("""
        foo
        foo
            baz(arg)
            boo
                baz(
                    arg
                )
            boo
                baz(aaa
                    bbb)
                xxx
        """).strip()

        self.assertEqual(
            [t.lexeme or t.symbol.name for t in grammar.tokenize(source)],
            [
                'foo', 'foo', 'INDENT', 
                'baz', '(', 'arg', ')', 
                'boo', 'INDENT', 
                'baz', '(', 'arg', ')', 'DEDENT', 
                'boo', 'INDENT',
                'baz', '(', 'aaa', 'bbb', ')', 'xxx', 'DEDENT',
                'DEDENT'
            ]
        )

