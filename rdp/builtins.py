import re

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

horizontal_whitespace = Regexp(r'[ \t]+')
whitespace = Regexp(r'[ \t\n\r]+')

py_decimalinteger = Regexp(r'[1-9]\d*') | '0'
py_hexinteger = Regexp(r'0[xX][0-9a-fA-F]+')
py_octinteger = Regexp(r'0[oO][0-7]+') | Regexp(r'0[0-7]+')
py_bininteger = Regexp(r'0[bB][01]+')
float_literal = Regexp(r'(?:[1-9]\d*|0)?\.\d*(?:[eE][+-]?\d+)?')
py_integer = py_decimalinteger | py_hexinteger | py_octinteger | py_bininteger


def quoted_string(quote_char, escape_char='\\'):
    assert len(quote_char) == 1
    return Regexp(r'{q}(?:{e}{q}|[^{q}])*{q}'.format(
        q=quote_char,
        e=re.escape(escape_char),
    ))


double_quoted_string = quoted_string('"')
single_quoted_string = quoted_string("'")

