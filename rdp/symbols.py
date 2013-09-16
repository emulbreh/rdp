import re
import abc
from collections import deque

from rdp.ast import Node
from rdp.exceptions import ParseError


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


class Symbol(metaclass=abc.ABCMeta):
    def __init__(self, name=''):
        self.flatten = False
        self.transform = None
        self.drop = False
        self.position = -1
        if name is not None:
            self.name = name

    @abc.abstractmethod
    def __call__(self, parser):
        assert False

    def __iter__(self):
        yield from ()

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

    def iter(self):
        visited = set()
        next_symbols = deque([self])
        while next_symbols:
            next_symbol = next_symbols.popleft()
            if next_symbol in visited:
                continue
            yield next_symbol
            visited.add(next_symbol)
            next_symbols.extend(next_symbol)

    def terminals(self):
        return (symbol for symbol in self.iter() if isinstance(symbol, Terminal))


class Terminal(Symbol):
    def __init__(self, lexeme, name=''):
        super(Terminal, self).__init__(name=name)
        self.lexeme = lexeme
        self.priority = -1

    @property
    def pattern(self):
        return re.escape(self.lexeme)

    def __call__(self, parser):
        token = parser.read()
        if token.symbol != self:
            raise ParseError('expected {0}, found {1}'.format(self, token.symbol), offset=token.offset, pos=token.start)
        yield Node(self, token)

    def __repr__(self):
        name = '{0}='.format(self.name) if self.name else ''
        return '<{0} {1}{2}>'.format(self.__class__.__name__, name, repr(self.lexeme))

    def __str__(self):
        if self.name:
            return self.name
        return repr(self.lexeme)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.lexeme == other.lexeme

    def __hash__(self):
        return hash(self.lexeme)


class Epsilon(Terminal):
    def __call__(self, parser):
        yield Node(self)


epsilon = Epsilon('')
empty_match = Node(epsilon)


class Regexp(Terminal):
    def __init__(self, pattern):
        if re.match(pattern, ''):
            raise ValueError('Regexp terminals may not match the empty string, use rdp.epsilon instead')
        super().__init__(pattern)

    @property
    def pattern(self):
        return self.lexeme


class NonTerminal(Symbol):
    repr_sep = ', '

    def __init__(self, symbols):
        super(NonTerminal, self).__init__()
        self.symbols = symbols
        self.name = ''

    def __iter__(self):
        yield from self.symbols

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
        longest_match_error = None
        for symbol in self.symbols:
            try:
                child = yield symbol
                node.append(child)
                yield node
            except ParseError as e:
                if not longest_match_error or longest_match_error.offset < e.offset:
                    longest_match_error = e
                continue
        raise longest_match_error

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


class Repeat(Symbol):
    def __init__(self, symbol, separator=None, min=0, trailing=False, greedy=True):
        super().__init__()
        self.symbol = to_symbol(symbol)
        self.separator = None if separator is None else to_symbol(separator)
        assert not trailing or separator, "separator symbol required"
        self.trailing = trailing
        self.greedy = greedy
        self.min = min

    def __iter__(self):
        yield self.symbol
        if self.separator:
            yield self.separator

    def __call__(self, parser):
        node = Node(self)
        last_sep = None
        n = 0
        while True:
            try:
                child = yield self.symbol
                if last_sep:
                    node.append(last_sep)
                n += 1
                node.append(child)
            except ParseError:
                if self.separator and node:
                    if self.trailing and last_sep:
                        node.append(last_sep)
                        break
                    if not self.greedy:
                        parser.backtrack(last_sep)
                        break
                    raise
                break
            if self.separator:
                try:
                    last_sep = yield self.separator
                except ParseError:
                    break

        if n < self.min:
            raise ParseError("too few {0}".format(self.symbol))
        yield node


class SymbolWrapper(Symbol):
    def __init__(self, symbol, name=''):
        super().__init__(name=name)
        self.symbol = None if symbol is None else to_symbol(symbol)

    def __iter__(self):
        yield self.symbol


class SymbolProxy(SymbolWrapper):
    def __init__(self, symbol=None, name=None):
        super().__init__(symbol=symbol, name=name)

    def __call__(self, parser):
        node = yield self.symbol
        yield node

    def __str__(self):
        return '<SymbolProxy {0}>'.format(repr(self.symbol))

    def __eq__(self, other):
        return isinstance(other, SymbolProxy) and self.symbol == other.symbol

    def __hash__(self):
        return hash(self.symbol)

    @property
    def name(self):
        return self.symbol.name


class Optional(SymbolWrapper):
    def __call__(self, parser):
        try:
            node = yield self.symbol
        except ParseError:
            node = Node(self)
        yield node


class Lookahead(SymbolWrapper):
    def __call__(self, parser):
        node = yield self.symbol
        parser.backtrack(node)
        yield empty_match
