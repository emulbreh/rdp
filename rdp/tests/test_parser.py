from unittest import TestCase

from rdp.grammar import Grammar, Terminal, Repeat, Regexp, flatten, drop, epsilon
from rdp.parser import Parser


class ParserTestCase(TestCase):
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

        class TestGrammar(Grammar):
            ab = Terminal('A') | Terminal('B')
            START = Repeat(ab, separator=',')

        self.grammar = TestGrammar()

    def test_one_item(self):
        self.assert_tree_eq(Parser(self.grammar, 'A').run(), (
            'START', [('ab', ['A'])]
        ))

    def test_several_items(self):
        self.assert_tree_eq(Parser(self.grammar, 'A,A,B,B').run(), (
            'START', [
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

        class JsonGrammar(Grammar):
            number_literal = Regexp(r'-?(?:[1-9]\d*|0)(?:\.\d*)?(?:[eE][+-]?\d+)?')
            string_literal = Regexp(r'"(?:[^"]|\\(?:["\\nbfrt]|u[0-9a-fA-F]{4}))*"')
            expr = flatten(number_literal | string_literal)
            array = drop('[') + flatten(Repeat(expr, separator=drop(','))) + drop(']')
            object_ = drop('{') + flatten(Repeat(flatten(string_literal + drop(':') + expr), separator=',')) + drop('}')
            expr |= flatten(array | object_)
            START = expr | Terminal('__symbol_copy_bug__')

        self.grammar = JsonGrammar()

    def test_object(self):
        self.assert_tree_eq(Parser(self.grammar, '{"foo":"bar"}').run(), (
            'START', [
                ('object_', ['"foo"', '"bar"']),
            ]
        ))

    def test_array(self):
        self.assert_tree_eq(Parser(self.grammar, '["foo","bar"]').run(), (
            'START', [
                ('array', ['"foo"', '"bar"']),
            ]
        ))

        self.assert_tree_eq(Parser(self.grammar, '["foo","bar"]').run(), (
            'START', [
                ('array', ['"foo"', '"bar"']),
            ]
        ))

    def test_numbers(self):
        self.assert_tree_eq(Parser(self.grammar, '[0,1,42,3.14,-1,-23.,0.001,1e10,13.5e-12]').run(), (
            'START', [
                ('array', ['0', '1', '42', '3.14', '-1', '-23.', '0.001', '1e10', '13.5e-12']),
            ]
        ))

