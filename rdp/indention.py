import re

from rdp.symbols import to_symbol
from rdp.tokenizer import Token
from rdp.symbols import Marker


INDENT = Marker('INDENT')
INDENT.num = +1
DEDENT = Marker('DEDENT')
DEDENT.num = -1


_space_re = re.compile(r'^[ \t]*')

def get_indention(s, tabsize=4):
    space = _space_re.match(s).group(0)
    return space.count(' ') + space.count('\t') * tabsize


def indent(opening=(), closing=(), tabsize=4):
    nesting_map = {}
    for symbol in opening:
        nesting_map[to_symbol(symbol)] = +1
    for symbol in closing:
        nesting_map[to_symbol(symbol)] = -1

    def tokenize(tokens):
        indention = []
        last_token = None
        depth = 0
        for token in tokens:
            depth += nesting_map.get(token.symbol, 0)
            if not depth:
                newline_index = token.lexeme.find('\n')
                if newline_index != -1:
                    before, after = token.split(newline_index + 1)
                    indent = get_indention(after.lexeme, tabsize=tabsize)
                    if not indention or indent != indention[-1]:
                        yield before
                        if not indention or indent > indention[-1]:
                            indention.append(indent)
                            yield Token(INDENT, "", after.start)
                        else:
                            while indention[-1] > indent:
                                yield Token(DEDENT, "", after.start)
                                indention.pop()
                            if indention[-1] != indent:
                                raise TokenizeError("unexpected indention level")
                        token = after
            last_token = token
            yield token

        pos = last_token.end
        while indention:
            yield Token(DEDENT, "", pos)
            indention.pop()
    return tokenize
