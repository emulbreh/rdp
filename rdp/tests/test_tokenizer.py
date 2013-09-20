import unittest
import textwrap
import re

from rdp import GrammarBuilder, flatten, drop, epsilon, Repeat, Terminal, Regexp, Parser, epsilon, Optional, ignore
from rdp.formatter import GrammarFormatter
from rdp import builtins
from rdp.tokenizer import Token


INDENT = Terminal('x', name='INDENT')
DEDENT = Terminal('x', name='DEDENT')


_space_re = re.compile(r'^[ \t]*')

def get_indention(s, tabsize=4):
    space = _space_re.match(s).group(0)
    return space.count(' ') + space.count('\t') * tabsize


class TokenizerTest(unittest.TestCase):
    def test_indention_tokenizer(self):

        def tokenize(tokens):
            indention = []
            last_token = None
            for token in tokens:
                newline_index = token.lexeme.find('\n')
                if newline_index == -1:
                    yield token
                    continue

                before_newline, after_newline = token.split(newline_index + 1)
                indent = get_indention(after_newline.lexeme)
                if indention and indent == indention[-1]:
                    yield token
                    continue

                yield before_newline
                if not indention or indent > indention[-1]:
                    indention.append(indent)
                    yield Token(INDENT, "", after_newline.start)
                else:
                    while indention[-1] > indent:
                        yield Token(DEDENT, "", after_newline.start)
                        indention.pop()
                    if indention[-1] != indent:
                        raise TokenizeError("unexpected indention level")
                yield after_newline
                last_token = token

            pos = last_token.end
            while indention:
                yield Token(DEDENT, "", pos)
                indention.pop()

        g = GrammarBuilder()
        g.whitespace = Regexp(r'\s+')
        g.block = INDENT + Repeat(g.expr) + DEDENT
        g.label = Regexp(r'\w+')
        g.expr = g.label + Optional(g.block)
        grammar = g(start=g.expr, tokenize=[tokenize, ignore(g.whitespace)])

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

