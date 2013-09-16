import unittest
import textwrap

from rdp import GrammarBuilder, flatten, drop, epsilon, Repeat, Terminal, Regexp, Parser, epsilon
from rdp.formatter import GrammarFormatter
from rdp import builtins


class FormatterTest(unittest.TestCase):
    def test_default_format(self):
        g = GrammarBuilder()
        g.string = builtins.double_quoted_string
        g.sequence = builtins.integer + Terminal('x')
        g.start = g.string | g.sequence | epsilon
        grammar = g(start=g.start)

        format = GrammarFormatter()

        self.assertEqual(format(grammar), textwrap.dedent(r"""
            string    ::=  r'"(?:\\\\"|[^"])*"'
            sequence  ::=  r'[1-9]\\d+' / r'0x\\d+' / r'0o\\d+', 'x'
            start     ::=  string / sequence / ɛ
        """).strip())

