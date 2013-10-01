import re
import abc
from collections import deque
from copy import copy

from rdp.ast import Node
from rdp.exceptions import ParseError, UnexpectedToken
from rdp.utils import chain


def to_symbol(str_or_symbol, copy_if_not_created=False):
    if isinstance(str_or_symbol, Symbol):
        if copy_if_not_created:
            return copy(str_or_symbol)
        return str_or_symbol
    if isinstance(str_or_symbol, str):
        return Terminal(str_or_symbol)
    raise TypeError("str or Symbol expected")


def flatten(symbol):
    symbol = to_symbol(symbol, True)
    symbol.flatten = True
    return symbol


def drop(symbol):
    symbol = to_symbol(symbol, True)
    symbol.drop = True
    return symbol


def keep(symbol):
    symbol = to_symbol(symbol, True)
    symbol.drop = False
    return symbol


def group(symbol):
    if isinstance(symbol, CompoundSymbol):
        symbol.grouped = True
    return symbol


class Symbol(metaclass=abc.ABCMeta):
    def __init__(self, name=None):
        self.flatten = False
        self.transform = lambda x: x
        self.drop = None
        self.position = -1
        self._name = name

    def named(self, name):
        if self._name:
            return Alias(self, name)
        self._name = name
        return self

    @property
    def name(self):
        return self._name

    @abc.abstractmethod
    def __call__(self, parser):
        assert False

    def __iter__(self):
        yield from ()

    def __str__(self):
        return '<{0}>'.format(self.name)

    def __add__(self, other):
        return Sequence([self, to_symbol(other)])

    def __radd__(self, other):
        return to_symbol(other) + self

    def __or__(self, other):
        return OneOf([self, to_symbol(other)])

    def __ror__(self, other):
        return to_symbol(other) | self

    def __ge__(self, func):
        clone = copy(self)
        clone.transform = chain(func, self.transform)
        return clone

    def __pos__(self):
        return NonEmpty(self)

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

    def apply_transform(self, node):
        return self.transform(node)

    def is_rule(self):
        return bool(self.name)


class Terminal(Symbol):
    def __init__(self, lexeme, name=''):
        super(Terminal, self).__init__(name=name)
        self.lexeme = lexeme
        self.priority = -1

    @property
    def pattern(self):
        return re.escape(self.lexeme)

    def apply_transform(self, node):
        return self.transform(node.token.lexeme)

    def __call__(self, parser):
        token = parser.read()
        if token.symbol != self:
            raise UnexpectedToken(token, self)
        yield parser.node(self, token, -1)

    def __pos__(self):
        return self

    def __repr__(self):
        name = '{0}='.format(self.name) if self.name else ''
        return '<{0} {1}{2}>'.format(
            self.__class__.__name__,
            name,
            repr(self.lexeme)
        )

    def __str__(self):
        if self.name:
            return '<{0}>'.format(self.name)
        return repr(self.lexeme)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.lexeme == other.lexeme

    def __hash__(self):
        return hash(self.lexeme)


class Marker(Terminal):
    def __init__(self, name):
        super().__init__('', name=name)

    @property
    def pattern(self):
        return None

    def __pos__(self):
        raise InvalidGrammar('Marker symbols cannot be non-empty')



class Epsilon(Marker):
    def __call__(self, parser):
        yield parser.node(self)

epsilon = Epsilon('')
empty_match = Node(None, None)


class Regexp(Terminal):
    def __init__(self, pattern):
        if re.match(pattern, ''):
            raise ValueError('Regexp terminals may not match the empty string, use rdp.epsilon instead')
        super().__init__(pattern)

    @property
    def pattern(self):
        return self.lexeme

    def __pos__(self):
        return self


class CompoundSymbol(Symbol):
    repr_sep = ', '

    def __init__(self, symbols):
        super().__init__()
        self.symbols = symbols
        self.grouped = False

    def __iter__(self):
        yield from self.symbols

    def __repr__(self):
        name = '{0} = '.format(self.name) if self.name else ''
        return '<{0} {1}{2}>'.format(
            self.__class__.__name__,
            name,
            self.repr_sep.join(repr(symbol) for symbol in self.symbols),
        )

    def apply_transform(self, node):
        return self.transform([child.transform() for child in node])


class OneOf(CompoundSymbol):
    repr_sep = ' | '

    def __call__(self, parser):
        node = parser.node(self)
        longest_match_error = None
        for symbol in self.symbols:
            try:
                child = yield symbol
                node.append(child)
                yield node
            except ParseError as e:
                if not longest_match_error or longest_match_error < e:
                    longest_match_error = e
                continue
        raise longest_match_error

    def __or__(self, other):
        if self.grouped:
            return super().__or__(other)
        return self.__class__(self.symbols + [to_symbol(other)])

    def apply_transform(self, node):
        return self.transform(node.children[0].transform())


class Sequence(CompoundSymbol):
    repr_sep = ' + '

    def __call__(self, parser):
        node = parser.node(self)
        for symbol in self.symbols:
            value = yield symbol
            node.append(value)
        yield node

    def __add__(self, other):
        if self.grouped:
            return super().__add__(other)
        return self.__class__(self.symbols + [to_symbol(other)])


class Repeat(Symbol):
    def __init__(self, symbol, min_matches=0):
        super().__init__()
        self.symbol = to_symbol(symbol)
        self.min_matches = min_matches

    def __iter__(self):
        yield self.symbol

    def __pos__(self):
        if self.min_matches > 0:
            return self
        clone = copy(self)
        clone.min_matches = 1
        return clone

    def __call__(self, parser):
        node = parser.node(self)
        n = 0
        while True:
            try:
                child = yield self.symbol
                n += 1
                node.append(child)
            except ParseError:
                break
        if n < self.min_matches:
            raise ParseError("too few {0}".format(self.symbol))
        yield node

    def apply_transform(self, node):
        return self.transform([child.transform() for child in node])


def repeat(symbol, separator=None, leading=False, trailing=False, min_matches=0):
    if not separator:
        return Repeat(symbol)
    separator = to_symbol(separator)
    tail = Repeat(flatten(separator + symbol), min_matches=max(min_matches - 1, 0))
    r = group(symbol) + flatten(tail)
    if leading:
        r = Optional(separator) + flatten(r)
    if trailing:
        r = flatten(r) + Optional(separator)
    if min_matches > 0:
        return r
    return flatten(r) | drop(epsilon)


class SymbolWrapper(Symbol):
    def __init__(self, symbol, name=''):
        super().__init__(name=name)
        self.symbol = None if symbol is None else to_symbol(symbol)

    def __iter__(self):
        yield self.symbol

    def apply_transform(self, node):
        return self.transform(self.symbol.transform())


class SymbolProxy(SymbolWrapper):
    def __init__(self, symbol=None, name=None):
        super().__init__(symbol=symbol, name=name)

    def __call__(self, parser):
        node = yield self.symbol
        yield node

    def __str__(self):
        return '<SymbolProxy {0}>'.format(self.symbol)

    def __eq__(self, other):
        return isinstance(other, SymbolProxy) and self.symbol == other.symbol

    def __hash__(self):
        return hash(self.symbol)

    @property
    def name(self):
        return self.symbol.name

    def is_rule(self):
        return False


class Alias(SymbolProxy):
    def __init__(self, symbol, name):
        super().__init__(symbol)
        self.alias = name

    @property
    def name(self):
        return self.alias

    def named(self, name):
        return Alias(self.symbol, name)

    def __call__(self, parser):
        node = yield self.symbol
        if node.symbol == self.symbol:
            node.symbol = self
        yield node


class Optional(SymbolWrapper):
    def __call__(self, parser):
        try:
            node = yield self.symbol
        except ParseError:
            node = empty_match
        yield node


class Lookahead(SymbolWrapper):
    def __call__(self, parser):
        node = yield self.symbol
        parser.backtrack(node)
        yield empty_match

    def __pos__(self):
        raise InvalidGrammar('Lookahead cannot be non-empty')


class NonEmpty(SymbolWrapper):
    def __call__(self, parser):
        node = yield self.symbol
        if not node:
            raise ParseError('non-empty match expected')
        yield node
