import re
from collections import namedtuple
from rdp.exceptions import TokenizeError


class Token(object):
    def __init__(self, symbol, offset, lexeme, start, end):
        self.symbol = symbol
        self.offset = offset
        self.lexeme = lexeme
        self.start = start
        self.end = end

    def __repr__(self):
        return '<Token {0} at line {1}[{2}]>'.format(
            self.lexeme,
            self.start[0] + 1,
            self.start[1]
        )


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
        offset = 0
        line = 0
        line_offset = 0
        source_len = len(source)
        while offset < source_len:
            match = self._re.match(source, offset)
            if match is None:
                raise TokenizeError('unexpected junk: {0} at line {1}, offset {2}'.format(repr(source[offset:offset + 10]), line + 1, line_offset))
            start, end = match.span()
            symbol = self.terminals[match.lastgroup]
            lexeme = match.group(0)
            start_pos = (line, start - line_offset)
            new_lines = lexeme.count('\n')
            if new_lines:
                line += new_lines
                line_offset = start + lexeme.rfind('\n')
            yield Token(
                symbol=symbol,
                offset=start,
                lexeme=lexeme,
                start=start_pos,
                end=(line, end - line_offset),
            )
            offset = end
        if offset != len(source):
            raise TokenizeError('unexpected junk: {0}'.format(source[offset:]))
