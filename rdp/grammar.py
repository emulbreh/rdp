import re

from rdp.ast import Node
from rdp.tokenizer import Tokenizer
from rdp.parser import ParseError


def to_symbol(str_or_symbol):
    if isinstance(str_or_symbol, Symbol):
        return str_or_symbol
    if isinstance(str_or_symbol, str):
        return Terminal(str_or_symbol)
    raise TypeError("str or Symbol expected")


def flatten(symbol):
    symbol.flatten = True
    return symbol


def drop(symbol):
    symbol = to_symbol(symbol)
    symbol.drop = True
    return symbol


class Symbol(object):
    def __init__(self):
        self.name = ''
        self.flatten = False
        self.transform = None
        self.drop = False

    def __call__(self, parser):
        assert False
        
    def __iter__(self):
        yield self

    def __str__(self):
        name = self.name if self.name else 'anonymous'
        return '{0}: {1}'.format(self.__class__.__name__, name)

    def __add__(self, other):
        return Sequence([self, to_symbol(other)])

    def __radd__(self, other):
        return to_symbol(other) + self
        
    def __or__(self, other):
        return OneOf([self, to_symbol(other)])
        
    def __ror__(self, other):
        return to_symbol(other) | self
        
    def __rshift__(self, func):
        self.transform = func


class Terminal(Symbol):
    def __init__(self, lexeme):
        super(Terminal, self).__init__()
        self.lexeme = lexeme
        self.priority = -1
    
    @property
    def pattern(self):
        return re.escape(self.lexeme)

    def __call__(self, parser):
        token = parser.read()
        if token.symbol != self:
            raise parser.error('expected {0}, found {1}', self, token.symbol)
        yield Node(self, token)

    def __repr__(self):
        name = '{0}='.format(self.name) if self.name else ''
        return '<{0} {1}{2}>'.format(self.__class__.__name__, name, repr(self.lexeme))

    def __str__(self):
        name = '{0}='.format(self.name) if self.name else ''
        return '{0}: {1}{2}'.format(self.__class__.__name__, name, repr(self.lexeme))

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.lexeme == other.lexeme

    def __hash__(self):
        return hash(self.lexeme)


class Epsilon(Terminal):
    def __call__(self, parser):
        yield Node(self)

epsilon = Epsilon('')


class Regexp(Terminal):
    def __init__(self, pattern):
        super().__init__(pattern)

    @property
    def pattern(self):
        return self.lexeme


class NonTerminal(Symbol):
    repr_sep = ', '

    def __init__(self, symbols):
        super(NonTerminal, self).__init__()
        self.symbols = symbols
        
    def __iter__(self):
        yield from super().__iter__()
        for symbol in self.symbols:
            yield from iter(symbol)

    def __repr__(self):
        name = '{0} = '.format(self.name) if self.name else ''
        return '<{0} {1}{2}>'.format(
            self.__class__.__name__, 
            name, 
            self.repr_sep.join(repr(symbol) for symbol in self.symbols),
        )


class OneOf(NonTerminal):
    repr_sep = ' | '

    def __call__(self, parser):
        node = Node(self)
        #print("TRYING all of:", self.symbols)
        for symbol in self.symbols:
            try:
                child = yield symbol
                node.append(child)
                yield node
            except ParseError as e:
                continue
        raise parser.error('expected one of: {0}', ', '.join(repr(symbol) for symbol in self.symbols))
        
    def __or__(self, other):
        return self.__class__(self.symbols + [to_symbol(other)])


class Sequence(NonTerminal):
    repr_sep = ' + '

    def __call__(self, parser):
        node = Node(self)
        for symbol in self.symbols:
            value = yield symbol
            node.append(value)
        yield node

    def __add__(self, other):
        return self.__class__(self.symbols + [to_symbol(other)])


class Repeat(NonTerminal):
    def __init__(self, symbol, separator=None):
        symbols = [to_symbol(symbol)]
        separator = to_symbol(separator)
        if separator:
            symbols.append(separator)
        super().__init__(symbols)
        self.symbol = symbol
        self.separator = separator

    def __call__(self, parser):
        node = Node(self)
        last_sep = None
        while True:
            try:
                child = yield self.symbol
                if last_sep:
                    node.append(last_sep)
                node.append(child)
            except ParseError:
                if self.separator and node:
                    raise
                else:
                    break
            if self.separator:
                try:
                    last_sep = yield self.separator
                except ParseError:
                    break
        yield node


class GrammarMeta(type):
    def __new__(cls, name, bases, attrs):
        TERMINALS = attrs.setdefault('TERMINALS', [])
        SYMBOLS = attrs.setdefault('SYMBOLS', set())

        for priority, terminal in enumerate(reversed(TERMINALS)):
            terminal.priority = priority

        for attr, value in attrs.copy().items():
            if not isinstance(value, Symbol):
                continue
            value.name = attr
            for symbol in value:
                SYMBOLS.add(symbol)
                if isinstance(symbol, Terminal) and symbol not in TERMINALS and not symbol == epsilon:
                    TERMINALS.append(symbol)

        cls = super(GrammarMeta, cls).__new__(cls, name, bases, attrs)
        if cls.__module__ != __name__ and not hasattr(cls, 'TOKENIZER'):
            setattr(cls, 'TOKENIZER', Tokenizer(TERMINALS))
        return cls


class Grammar(Symbol, metaclass=GrammarMeta):
    def __iter__(self):
        yield self
        yield from iter(self.START)

    def __call__(self, parser):
        node = yield self.START
        yield node

