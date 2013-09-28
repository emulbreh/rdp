import re

from rdp.exceptions import TokenizeError


class Token:
    def __init__(self, symbol, lexeme, start):
        self.symbol = symbol
        self.lexeme = lexeme
        self.start = start

    @property
    def end(self):
        return self.start + len(self.lexeme)

    def __len__(self):
        return len(self.lexeme)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.lexeme == other
        return super().__eq__(other)

    def __contains__(self, s):
        return s in self.lexeme

    def __bool__(self):
        return bool(self.lexeme)

    def __repr__(self):
        return '<Token {0} {1} pos={2}>'.format(self.symbol.name or '', repr(self.lexeme), self.start)

    def split(self, offset):
        a, b = self.lexeme[:offset], self.lexeme[offset:]
        yield self.__class__(self.symbol, a, self.start)
        yield self.__class__(self.symbol, b, self.start + offset)


class Tokenizer(object):
    def __init__(self, terminals):
        self.terminals = {}
        patterns = []
        for index, terminal in enumerate(terminals):
            if terminal.pattern is None:
                continue
            group = '_t{0}'.format(index)
            self.terminals[group] = terminal
            patterns.append('(?P<{0}>{1})'.format(group, terminal.pattern))

        if not patterns:
            raise TypeError("tokenizer needs at least one terminal symbol")

        self._re = re.compile('|'.join(patterns), re.MULTILINE)

    def tokenize(self, source):
        source_len = len(source)
        pos = 0
        while pos < source_len:
            match = self._re.match(source, pos)
            if match is None:
                raise TokenizeError('unexpected junk: {0}'.format(
                    repr(source[pos:pos + 10]),
                ))
            symbol = self.terminals[match.lastgroup]
            lexeme = match.group(0)
            start, end = match.span()
            yield Token(
                symbol=symbol,
                lexeme=lexeme,
                start=pos,
            )
            pos += len(lexeme)
