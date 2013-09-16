import unittest
import textwrap
import re

from rdp import GrammarBuilder, flatten, drop, epsilon, Repeat, Terminal, Regexp, Parser, epsilon, Optional
from rdp.formatter import GrammarFormatter
from rdp import builtins
from rdp.tokenizer import Token


INDENT = Terminal('x', name='INDENT')
DEDENT = Terminal('x', name='DEDENT')


class TokenizerTest(unittest.TestCase):
    def test_default_format(self):

        def tokenize(tokens):
            indention = [0]
            for token in tokens:
                if '\n' not in token.lexeme:
                    yield token
                else:
                    pre, post = token.lexeme.rsplit('\n')
                    pos = (token.end[1], 0)
                    space = len(re.match(r'^[ ]*', post).group(0))
                    if indention and space == indention[-1]:
                        yield token
                    else:
                        yield Token(token.symbol, token.offset, pre + '\n', token.start, pos)
                        if not indention or space > indention[-1]:
                            indention.append(space)
                            yield Token(INDENT, token.offset + len(pre) + 1, "", pos, pos)
                        else:
                            while indention[-1] > space:
                                yield Token(DEDENT, token.offset + len(pre) + 1, "", pos, pos)
                                indention.pop()
                            assert indention[-1] == space, "unexpected indention level"
                        yield Token(token.symbol, token.offset + len(pre) + 1, post, pos, token.end)
            while indention:
                yield Token(DEDENT, 0, "", (0, 0), (0, 0))
                indention.pop()

        g = GrammarBuilder()
        g.whitespace = Regexp(r'\s+')
        g.block = INDENT + Repeat(g.expr) + DEDENT
        g.label = Regexp(r'\w+')
        g.expr = g.label + Optional(g.block)
        grammar = g(start=g.expr, ignore=[g.whitespace], tokenize=tokenize)

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
            ['foo', 'INDENT', 'bar', 'baz', 'INDENT', 'boo', 'DEDENT', 'x', 'y', 'DEDENT', 'DEDENT']
        )

