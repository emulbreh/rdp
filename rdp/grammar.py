from operator import attrgetter

from rdp.tokenizer import Tokenizer
from rdp.exceptions import InvalidGrammar
from rdp.symbols import to_symbol, Symbol, SymbolProxy, Alias, Terminal, epsilon
from rdp.parser import Parser


class GrammarBuilder(object):
    def __init__(self):
        self._symbols = {}
        self._start = None
        self._forward_declarations = {}

    def __getattr__(self, name):
        try:
            return self._symbols[name]
        except KeyError:
            symbol = SymbolProxy(None)
            self._symbols[name] = symbol
            self._forward_declarations[name] = symbol
            return symbol

    def __setattr__(self, name, symbol):
        if name.startswith('_'):
            return super().__setattr__(name, symbol)
        symbol = to_symbol(symbol)
        try:
            self._forward_declarations.pop(name).symbol = symbol
        except KeyError:
            pass
        symbol = symbol.named(name)
        symbol.position = len(self._symbols)
        self._symbols[name] = symbol

    def __call__(self, start=None, terminals=None, tokenize=(), drop_terminals=False):
        if any(self._forward_declarations):
            undeclared_symbols = self._forward_declarations.keys()
            raise InvalidGrammar('undefined symbols: {0}'.format(', '.join(undeclared_symbols)))
        return Grammar(start,
            symbols=self._symbols.values(),
            tokenize=tokenize,
            drop_terminals=drop_terminals,
        )


def ignore(*symbols):
    def ignore_symbols(tokens):
        for token in tokens:
            if token.symbol not in symbols:
                yield token
    return ignore_symbols


class Grammar(Symbol):
    def __init__(self, start, terminals=None, symbols=None, tokenize=(), drop_terminals=False):
        self.start = start
        self.terminals = terminals if terminals is not None else []
        self.symbols = set(symbols) if symbols else {start}
        self.drop_terminals = drop_terminals

        for symbol in self.symbols.copy():
            for s in symbol.iter():
                self.symbols.add(s)
                if isinstance(s, Terminal):
                    if s.__class__ == Terminal and s.drop is None:
                        s.drop = self.drop_terminals
                    if s not in self.terminals and s is not epsilon:
                        self.terminals.append(s)

        self.token_transforms = tokenize
        self.tokenizer = Tokenizer(self.terminals)

    def tokenize(self, source):
        tokens = self.tokenizer.tokenize(source)
        for t in self.token_transforms:
            tokens = t(tokens)
        return tokens

    def rules(self):
        for symbol in sorted(self.symbols, key=attrgetter('position')):
            if symbol.is_rule():
                yield symbol

    def __iter__(self):
        yield from self.start

    def __call__(self, parser):
        yield from self.start(parser)

    def pre_transform(self, node):
        return [child.transform() for child in node]

    def parse(self, source, transform=False):
        parser = Parser(self, source)
        return parser.run()

