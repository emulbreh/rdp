
class InvalidGrammar(Exception):
    pass


class ParseError(Exception):
    def __init__(self, msg, offset=None, pos=None):
        if pos:
            msg = '{0} at line {1}[{1}]'.format(msg, *pos)
        elif offset:
            msg = '{0} at offset {1}'.format(msg, offset)
        super().__init__(msg)
        self.offset = offset
        self.pos = pos


class UnexpectedToken(ParseError):
    def __init__(self, token, expected):
        super().__init__('expected {0}, found {1}'.format(expected, token))
        self.token = token
        self.expected = expected


class TokenizeError(Exception):
    pass


class LeftRecursion(InvalidGrammar):
    pass
