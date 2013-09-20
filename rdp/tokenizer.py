import re
from functools import total_ordering

from rdp.exceptions import TokenizeError


@total_ordering
class SourcePosition:
    def __init__(self, line, line_offset, source_offset):
        self.line = line
        self.line_offset = line_offset
        self.source_offset = source_offset

    def advance(self, lexeme):
        if not lexeme:
            return self
        line = self.line
        length = len(lexeme)
        new_lines = lexeme.count('\n')
        if new_lines:
            line += new_lines
            line_offset = length - lexeme.rfind('\n') - 1
        else:
            line_offset = self.line_offset + length
        return SourcePosition(line, line_offset, self.source_offset + length)

    def __str__(self):
        return "line {0}[{1}]".format(self.line, self.line_offset)

    def __lt__(self, other):
        return self.source_offset < other.source_offset

    def __eq__(self, other):
        return self.source_offset == other.source_offset


START_POSITION = SourcePosition(0, 0, 0)


class Token:
    def __init__(self, symbol, lexeme, start):
        self.symbol = symbol
        self.lexeme = lexeme
        self.start = start

    @property
    def end(self):
        return self.start.advance(self.lexeme)

    def __len__(self):
        return len(self.lexeme)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.lexeme == other
        return super().__eq__(self, other)

    def __contains__(self, s):
        return s in self.lexeme

    def __repr__(self):
        return '<Token {0} at {1}]>'.format(self.lexeme, self.start)

    def split(self, offset):
        a, b = self.lexeme[:offset], self.lexeme[offset:]
        yield self.__class__(self.symbol, a, self.start)
        yield self.__class__(self.symbol, b, self.start.advance(a))


class Tokenizer(object):
    def __init__(self, terminals):
        self.terminals = {}
        patterns = []
        for index, terminal in enumerate(terminals):
            group = '_t{0}'.format(index)
            self.terminals[group] = terminal
            patterns.append('(?P<{0}>{1})'.format(group, terminal.pattern))

        if not patterns:
            raise TypeError("tokenizer needs at least one terminal symbol")

        self._re = re.compile('|'.join(patterns), re.MULTILINE)

    def tokenize(self, source):
        source_len = len(source)
        pos = START_POSITION
        while pos.source_offset < source_len:
            match = self._re.match(source, pos.source_offset)
            if match is None:
                raise TokenizeError('unexpected junk: {0} at line {1}, offset {2}'.format(
                    repr(source[pos.source_offset:pos.source_offset + 10]),
                    pos.line + 1,
                    pos.line_offset
                ))
            symbol = self.terminals[match.lastgroup]
            lexeme = match.group(0)
            start, end = match.span()
            yield Token(
                symbol=symbol,
                lexeme=lexeme,
                start=pos,
            )
            pos = pos.advance(lexeme)
