
class InvalidGrammar(Exception):
    pass


class ParseError(Exception):
    def __init__(self, msg, pos):
        msg = '{0} at line {1}[{2}]'.format(msg, pos.line, pos.line_offset)
        super().__init__(msg)
        self.pos = pos

    def __lt__(self, other):
        return self.pos < other.pos

    def __le__(self, other):
        return self.pos <= other.pos


class UnexpectedToken(ParseError):
    def __init__(self, token, expected):
        super().__init__('expected {0}, found {1}'.format(expected, token), token.start)
        self.token = token
        self.expected = expected


class TokenizeError(Exception):
    pass


class LeftRecursion(InvalidGrammar):
    pass
