from collections import namedtuple

from rdp.ast import Node
from rdp.exceptions import ParseError, LeftRecursion


class RandomAccessIterator(object):
    def __init__(self, iterator):
        self.iterator = iterator
        self.buffer = []
        self.offset = 0
        self.last = None

    @property
    def position(self):
        return self.last.end if self.last else 0

    def __next__(self):
        if self.offset == len(self.buffer):
            item = next(self.iterator)
            self.buffer.append(item)
        else:
            item = self.buffer[self.offset]
        self.offset += 1
        self.last = None
        return item

    def tell(self):
        return self.offset

    def seek(self, offset):
        if offset < len(self.buffer):
            self.offset = offset
            self.last = self.buffer[offset - 1] if offset > 0 else None
        else:
            while self.offset != offset:
                self.last = next(self)


class Parser(object):
    StackEntry = namedtuple('StackEntry', ['symbol', 'generator', 'offset'])

    def __init__(self, grammar, source, detect_left_recursion=False):
        self.grammar = grammar
        self.source = source
        self.stack = []
        self.tokens = RandomAccessIterator(grammar.tokenize(source))
        self._cache = {}
        self.detect_left_recursion = detect_left_recursion

    def read(self):
        try:
            return next(self.tokens)
        except StopIteration:
            raise ParseError('unexpected end of file', self.tokens.offset)

    def backtrack(self, node):
        self.tokens.seek(node.offset)

    @property
    def offset(self):
        return self.tokens.offset

    def node(self, symbol, token=None, offset_diff=0):
        return Node(symbol, self.tokens.offset + offset_diff, token=token)

    def push(self, symbol):
        if self.stack and self.detect_left_recursion:
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
        #print('stack =\n  -', '\n  - '.join(str(e.symbol) for e in self.stack))
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
        raise ParseError('unparsed junk: {0}'.format(junk), junk.start)

