from collections import namedtuple

from rdp.ast import Node
from rdp.exceptions import ParseError, LeftRecursion, UnexpectedToken


class RandomAccessGenerator(object):
    def __init__(self, generator):
        self.generator = generator
        self.buffer = []
        self.offset = 0

    def next(self):
        if self.offset == len(self.buffer):
            item = next(self.generator)
            self.buffer.append(item)
        else:
            item = self.buffer[self.offset]
        self.offset += 1
        return item

    def tell(self):
        return self.offset

    def seek(self, offset):
        if offset < len(self.buffer):
            self.offset = offset
        else:
            while self.offset != offset:
                self.next()


class Parser(object):
    StackEntry = namedtuple('StackEntry', ['symbol', 'generator', 'offset'])

    def __init__(self, grammar, source):
        self.grammar = grammar
        self.source = source
        self.stack = []
        self.tokens = RandomAccessGenerator(grammar.tokenize(source))
        self._cache = {}

    def read(self):
        try:
            return self.tokens.next()
        except StopIteration:
            raise ParseError('unexpected end of file', len(self.source))

    def backtrack(self, node):
        self.tokens.seek(node.offset)

    def push(self, symbol):
        if self.stack:
            top = self.stack[-1]
            for entry in self.stack:
                if entry.offset == self.tokens.tell() and entry.symbol == symbol:
                    raise LeftRecursion()

        #print("push", symbol)
        entry = self.StackEntry(
            symbol=symbol,
            generator=symbol(self),
            offset=self.tokens.tell(),
        )
        self.stack.append(entry)
        #print('stack =', '\n- '.join(repr(e.symbol) for e in self.stack))
        return next(entry.generator)

    def run(self, limit=None):
        func, arg = self.push, self.grammar.start
        n = 0
        while limit is None or n < limit:
            n += 1
            try:
                arg, offset = func(arg), self.tokens.tell()
            except ParseError as error:
                self.tokens.seek(self.stack[-1].offset)
                self.stack.pop()
                if not self.stack:
                    raise
                func, arg = self.stack[-1].generator.throw, error
                continue

            if isinstance(arg, Node):
                top = self.stack[-1]
                self._cache[top.symbol, top.offset] = arg, offset
                self.stack.pop()
                if not self.stack:
                    break
            else:
                try:
                    arg, offset = self._cache[arg, offset]
                except KeyError:
                    func = self.push
                    continue
                self.tokens.seek(offset)
            func = self.stack[-1].generator.send

        try:
            junk = self.read()
        except ParseError:
            return arg
        raise ParseError('unparsed junk: {0}'.format(junk), offset=junk.offset, pos=junk.start)

