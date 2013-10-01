import unittest
import textwrap

from rdp import GrammarBuilder, flatten, drop, epsilon, repeat, Terminal, Regexp, Parser, epsilon
from rdp.formatter import GrammarFormatter
from rdp import builtins


class FormatterTest(unittest.TestCase):
    def test_default_format(self):
        g = GrammarBuilder()
        g.string = builtins.double_quoted_string
        g.sequence = builtins.py_integer + Terminal('x')
        g.start = g.string | g.sequence | epsilon
        grammar = g(start=g.start)

        format = GrammarFormatter()

        self.assertEqual(format(grammar), textwrap.dedent(r"""
            string    ::=  r'"(?:\\\\"|[^"])*"'
            sequence  ::=  r'[1-9]\\d*' / '0' / r'0[xX][0-9a-fA-F]+' / r'0[oO][0-7]+' / r'0[0-7]+' / r'0[bB][01]+', 'x'
            start     ::=  string / sequence / ɛ
        """).strip())

