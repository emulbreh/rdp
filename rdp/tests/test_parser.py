import unittest

from rdp.grammar import Grammar, GrammarBuilder, Terminal, Repeat, Regexp, flatten, drop, epsilon
from rdp.parser import Parser


class ParserTestCase(unittest.TestCase):
    def assert_tree_eq(self, node, spec):
        if isinstance(spec, str):
            self.assertEqual(node.value.lexeme, spec)
            return
        self.assertEqual(node.symbol.name, spec[0])
        self.assertEqual(len(node.children), len(spec[1]), 'child count of %s does not match expectation' % node)
        for child, child_spec in zip(node.children, spec[1]):
            self.assert_tree_eq(child, child_spec)


class RepeatParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        
        g = GrammarBuilder()
        g.ab = Terminal('A') | Terminal('B')
        g.seq = Repeat(g.ab, separator=',')
        self.grammar = g(start=g.seq)

    def test_one_item(self):
        self.assert_tree_eq(Parser(self.grammar, 'A').run(), (
            'seq', [
                ('ab', ['A']),
            ]
        ))

    def test_several_items(self):
        self.assert_tree_eq(Parser(self.grammar, 'A,A,B,B').run(), (
            'seq', [
                ('ab', ['A']),
                ',',
                ('ab', ['A']),
                ',',
                ('ab', ['B']),
                ',',
                ('ab', ['B']),
            ]
        ))


class JsonParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()

        g = GrammarBuilder()
        g.number_literal = Regexp(r'-?(?:[1-9]\d*|0)(?:\.\d*)?(?:[eE][+-]?\d+)?')
        g.string_literal = Regexp(r'"(?:[^"]|\\(?:["\\nbfrt]|u[0-9a-fA-F]{4}))*"')
        g.array = drop('[') + flatten(Repeat(g.expr, separator=drop(','))) + drop(']')
        g.object_ = drop('{') + flatten(Repeat(flatten(g.string_literal + drop(':') + g.expr), separator=',')) + drop('}')
        g.expr = flatten(g.number_literal | g.string_literal | g.array | g.object_)
        g.whitespace = Regexp('\\s+')

        self.grammar = g(start=g.expr, ignore=g.whitespace)

    def test_object(self):
        self.assert_tree_eq(Parser(self.grammar, '{"foo":"bar"}').run(), (
            'expr', [
                ('object_', ['"foo"', '"bar"']),
            ]
        ))

    def test_array(self):
        self.assert_tree_eq(Parser(self.grammar, '["foo","bar"]').run(), (
            'expr', [
                ('array', ['"foo"', '"bar"']),
            ]
        ))

        self.assert_tree_eq(Parser(self.grammar, '["foo","bar"]').run(), (
            'expr', [
                ('array', ['"foo"', '"bar"']),
            ]
        ))

    def test_numbers(self):
        self.assert_tree_eq(Parser(self.grammar, '[0,1,42,3.14,-1,-23.,0.001,1e10,13.5e-12]').run(), (
            'expr', [
                ('array', ['0', '1', '42', '3.14', '-1', '-23.', '0.001', '1e10', '13.5e-12']),
            ]
        ))

