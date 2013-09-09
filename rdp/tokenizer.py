import re
from collections import namedtuple


class TokenizeError(Exception):
    pass


class Tokenizer(object):
    Token = namedtuple('Token', ['symbol', 'offset', 'lexeme'])

    def __init__(self, terminals):
        self.terminals = {}
        patterns = []
        for index, terminal in enumerate(terminals):
            group = '_t{0}'.format(index)
            self.terminals[group] = terminal
            patterns.append('(?P<{0}>{1})'.format(group, terminal.pattern))
        
        if not patterns:
            raise TypeError("tokenizer needs at least one terminal symbol")
        
        self._re = re.compile('|'.join(patterns))
        print("pattern:", self._re.pattern)
        print(self.terminals)
    
    def tokenize(self, source):
        offset = 0
        for match in self._re.finditer(source):
            start, end = match.span()
            if start != offset:
                raise TokenizeError('unexpected junk: {0}'.format(source[offset:start]))
            yield self.Token(
                symbol=self.terminals[match.lastgroup],
                offset=start,
                lexeme=match.group(0),
            )
            offset = end
        if offset != len(source):
            raise TokenizeError('unexpected junk: {0}'.format(source[offset:]))
