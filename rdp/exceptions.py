
class InvalidGrammar(Exception):
    pass


class ParseError(Exception):
    def __init__(self, msg, offset):
        msg = '{0} at offset {1}'.format(msg, offset)
        super().__init__(msg)
        self.offset = offset

    def __lt__(self, other):
        return self.offset < other.offset

    def __le__(self, other):
        return self.offset <= other.offset


class UnexpectedToken(ParseError):
    def __init__(self, token, expected):
        super().__init__('expected {0}, found {1}'.format(expected, token), token.start)
        self.token = token
        self.expected = expected


class TokenizeError(Exception):
    pass


class LeftRecursion(InvalidGrammar):
    pass
