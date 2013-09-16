from rdp.grammar import SymbolProxy


class GrammarFormatter:
    rule_separator = '  ::=  '

    def __call__(self, grammar):
        self.depth = 0
        rules = [(symbol.name, symbol) for symbol in grammar.rules()]
        maxlen = max(len(name) for name, symbol in rules)
        rule_format = '{{0:{0}}}{1}{{1}}'.format(maxlen, self.rule_separator)
        return '\n'.join(rule_format.format(name, self.format_symbol(symbol)) for name, symbol in rules)

    def format_symbol(self, symbol):
        if symbol.name and self.depth > 0:
            return symbol.name
        func_name = 'format_{0}'.format(type(symbol).__name__.lower())
        try:
            func = getattr(self, func_name)
        except AttributeError:
            raise TypeError('cannot format symbol of type {0}'.format(type(symbol)))
        self.depth += 1
        formatted_symbol = func(symbol)
        self.depth -= 1
        return formatted_symbol

    def format_sequence(self, sequence):
        return ', '.join(self.format_symbol(s) for s in sequence.symbols)

    def format_optional(self, optional):
        return '({0})?'.format(self.format_symbol(optional.symbol))

    def format_repeat(self, repeat):
        if repeat.separator:
            return '[{0} *({0} {1})]'.format(
                self.format_symbol(repeat.symbol), 
                self.format_symbol(repeat.separator),
            )
        else:
            return '*({0})'.format(self.format_symbol(repeat.symbol))

    def format_oneof(self, oneof):
        return ' / '.join(self.format_symbol(s) for s in oneof.symbols)

    def format_terminal(self, terminal):
        return repr(terminal.lexeme)

    def format_epsilon(self, epsilon):
        return 'ɛ'

    def format_regexp(self, regexp):
        return 'r' + self.format_terminal(regexp)

    def format_grammar(self, grammar):
        return '<grammar {0}>'.format(grammar)
        
    def format_lookahead(self, lookahead):
        return '(?>{0})'.format(self.format_symbol(lookahead.symbol))
