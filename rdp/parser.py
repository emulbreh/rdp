from collections import namedtuple

from rdp.ast import Node


class ParseError(Exception):
    pass


class LeftRecursion(Exception):
    pass


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
        self.tokens = RandomAccessGenerator(grammar.tokenizer.tokenize(source))
        self._cache = {}
        
    def error(self, msg, *args, **kwargs):
        raise ParseError(msg.format(*args, **kwargs))
        
    def read(self):
        try:
            return self.tokens.next()
        except StopIteration:
            raise ParseError('EOF')
    
    def push(self, symbol):
        if self.stack:
            top = self.stack[-1]
            if self.tokens.tell() == top.offset and symbol == top.symbol:
                raise LeftRecursion()
        entry = self.StackEntry(
            symbol=symbol, 
            generator=symbol(self),
            offset=self.tokens.tell(),
        )
        self.stack.append(entry)
        #print('stack =', '\n- '.join(repr(e.symbol) for e in self.stack))
        return next(entry.generator)
        
    def run(self):
        func, arg = self.push, self.grammar.start
        while True:
            try:
                arg = func(arg)
                if not isinstance(arg, Node):
                    try:
                        arg = self._cache[arg, self.tokens.tell()]
                    except KeyError:
                        func = self.push
                        continue
                top = self.stack[-1]
                self._cache[top.symbol, top.offset] = arg
                self.stack.pop()
                if not self.stack:
                    break
                func = self.stack[-1].generator.send
            except ParseError as error:
                self.tokens.seek(self.stack[-1].offset)
                self.stack.pop()
                if not self.stack:
                    raise
                func, arg = self.stack[-1].generator.throw, error
        try:
            junk = self.read()
        except ParseError:
            return arg
        raise ParseError('unparsed junk: {0}'.format(junk))

