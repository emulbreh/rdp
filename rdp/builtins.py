import re
import string

from rdp.symbols import Regexp, flatten


letters = Regexp(r'[a-zA-Z]+')
digits = Regexp(r'[0-9]+')
hexdigits = Regexp(r'[0-9a-fA-F]+')
octdigits = Regexp(r'[0-7]+')
whitespace = Regexp(r'\s+')
word = Regexp(r'[a-zA-Z0-9_]+')
hyphen_word = Regexp(r'[a-zA-Z0-9_-]+')
identifier = Regexp(r'[a-zA-Z_][a-zA-Z0-9_]*')
hyphen_identifier = Regexp(r'[a-zA-Z_-][a-zA-Z0-9_-]*')

decimal_integer = Regexp(r'[1-9]\d+')
hexadecimal_integer = Regexp(r'0x\d+')
octal_integer = Regexp(r'0o\d+')
integer = flatten(decimal_integer | hexadecimal_integer | octal_integer)


def quoted_string(quote_char, escape_char='\\'):
    assert len(quote_char) == 1
    return Regexp(r'{q}(?:{e}{q}|[^{q}])*{q}'.format(
        q=quote_char,
        e=re.escape(escape_char),
    ))


double_quoted_string = quoted_string('"')
single_quoted_string = quoted_string("'")


def comma_separated(symbol, **kwargs):
    return Repeat(symbol, separator=',', **kwargs)