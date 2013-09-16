import unittest

from rdp import (GrammarBuilder, Grammar, flatten, drop, epsilon, Repeat, Terminal, 
    Regexp, Parser, LeftRecursion, ParseError, Optional, Lookahead)
from rdp.formatter import GrammarFormatter


class ParserTestCase(unittest.TestCase):
    def assert_tree_eq(self, node, spec):
        if isinstance(node, str):
            node = Parser(self.grammar, node).run()
        if isinstance(spec, str):
            self.assertTrue(node.value is not None, 'expected a terminal, found {0}'.format(node))
            self.assertEqual(node.value.lexeme, spec)
            return
        self.assertEqual(node.symbol.name, spec[0])
        self.assertEqual(len(node.children), len(spec[1]), 'child count of {0} does not match expectation'.format(node))
        for child, child_spec in zip(node.children, spec[1]):
            self.assert_tree_eq(child, child_spec)

    def parse(self, source):
        return Parser(self.grammar, source).run()


class RegexpParserTest(ParserTestCase):
    def test_regexp_empty_match(self):
        with self.assertRaises(ValueError):
            Regexp('a*')


class OneOfParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.ab = Terminal('A') | Terminal('B')
        self.grammar = g(start=g.ab)

    def test_a_or_b(self):
        self.assert_tree_eq('A', ('ab', ['A']))


class SequenceParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.ab = Terminal('A') | Terminal('B')
        g.start = g.ab + g.ab
        self.grammar = g(start=g.start)

    def test_match(self):
        self.assert_tree_eq('AB', ('start', [('ab', ['A']), ('ab', ['B'])]))


class RepeatWithSeparatorParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.ab = Terminal('A') | Terminal('B')
        g.seq = Repeat(g.ab, separator=',')
        self.grammar = g(start=g.seq)
        
    def test_zero_items(self):
        self.assert_tree_eq('', ('seq', []))
        with self.assertRaises(ParseError):
            self.parse(',')

    def test_one_item(self):
        self.assert_tree_eq('A', ('seq', [('ab', ['A'])]))
        with self.assertRaises(ParseError):
            self.parse('A,')
        with self.assertRaises(ParseError):
            self.parse(',A')

    def test_several_items(self):
        self.assert_tree_eq('A,A,B,B', ('seq', [
            ('ab', ['A']),
            ',',
            ('ab', ['A']),
            ',',
            ('ab', ['B']),
            ',',
            ('ab', ['B']),
        ]))
        with self.assertRaises(ParseError):
            self.parse('A,A,B,B,')


class RepeatWithTrailingSeparatorParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.ab = Terminal('A') | Terminal('B')
        g.seq = Repeat(g.ab, separator=',', trailing=True)
        self.grammar = g(start=g.seq)

    def test_zero_items(self):
        self.assert_tree_eq('', ('seq', []))
        with self.assertRaises(ParseError):
            self.parse(',')

    def test_one_item(self):
        self.assert_tree_eq('A', ('seq', [('ab', ['A'])]))
        self.assert_tree_eq('A,', ('seq', [('ab', ['A', ]), ',']))

    def test_several_items(self):
        self.assert_tree_eq('A,A,B,B', ('seq', [
            ('ab', ['A']),
            ',',
            ('ab', ['A']),
            ',',
            ('ab', ['B']),
            ',',
            ('ab', ['B']),
        ]))
        self.assert_tree_eq('A,A,B,B,', ('seq', [
            ('ab', ['A']),
            ',',
            ('ab', ['A']),
            ',',
            ('ab', ['B']),
            ',',
            ('ab', ['B']),
            ',',
        ]))


class RepeatWithoutSeparatorParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.ab = flatten(Terminal('A') | Terminal('B'))
        g.seq = Repeat(g.ab)
        self.grammar = g(start=g.seq)

    def test_zero_items(self):
        self.assert_tree_eq('', ('seq', []))

    def test_one_item(self):
        self.assert_tree_eq('A', ('seq', ['A']))

    def test_several_items(self):
        self.assert_tree_eq('ABAB', ('seq', ['A', 'B', 'A', 'B']))


class OptionalParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.start = 'A' + Optional('A')
        self.grammar = g(start=g.start)

    def test_optional_absent(self):
        self.assert_tree_eq('A', ('start', ['A']))

    def test_optional_present(self):
        self.assert_tree_eq('AA', ('start', ['A', 'A']))


class LookaheadParserTest(ParserTestCase):
    def setUp(self):
        super().setUp()
        g = GrammarBuilder()
        g.xy = Terminal('x') | Terminal('y')
        g.yx = Terminal('x') | Terminal('y')
        g.start = flatten(Lookahead('x') + g.xy) | g.yx
        self.grammar = g(start=g.start)
    
    def test_lookahead(self):
        self.assert_tree_eq('x', ('start', [('xy', ['x'])]))
        self.assert_tree_eq('y', ('start', [('yx', ['y'])]))


class LeftRecursionTest(ParserTestCase):
    def test_direct_left_recursion_raises(self):
        g = GrammarBuilder()
        g.foo = 'a' | g.foo + 'x'
        grammar = g(start=g.foo)

        with self.assertRaises(LeftRecursion):
            Parser(grammar, 'xx').run(100)


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

        self.grammar = g(start=g.expr, ignore=[g.whitespace])

    def test_object(self):
        self.assert_tree_eq(Parser(self.grammar, '{"foo": "bar"}').run(), (
            'expr', [
                ('object_', ['"foo"', '"bar"']),
            ]
        ))

    def test_array(self):
        self.assert_tree_eq(Parser(self.grammar, '["foo", "bar"]').run(), (
            'expr', [
                ('array', ['"foo"', '"bar"']),
            ]
        ))

        self.assert_tree_eq(Parser(self.grammar, '["foo", "bar"]').run(), (
            'expr', [
                ('array', ['"foo"', '"bar"']),
            ]
        ))

    def test_numbers(self):
        self.assert_tree_eq(Parser(self.grammar, '[0, 1, 42, 3.14, -1, -23., 0.001, 1e10, 13.5e-12]').run(), (
            'expr', [
                ('array', ['0', '1', '42', '3.14', '-1', '-23.', '0.001', '1e10', '13.5e-12']),
            ]
        ))


class TestErrorMessages(unittest.TestCase):
    def setUp(self):
        g = GrammarBuilder()
        g.a = Terminal('A')
        g.b = Terminal('B')
        g.c = Terminal('C')
        g.ab = g.a | g.b
        g.start = g.ab + g.ab
        g.whitespace = Regexp(r'\s+')
        self.grammar = g(start=g.start, ignore=[g.whitespace])
        #print(self.grammar.tokenizer._re.pattern)
    
    def test_incomplete_sequence(self):
        source = """
        A 
        """
        with self.assertRaises(ParseError):
            Parser(self.grammar, source).run()
    
    def test_unexpected_terminal(self):
        source = """
        A C
        """
        with self.assertRaises(ParseError):
            Parser(self.grammar, source).run()

    def test_unparsed_junk(self):
        source = """
        A B A B
        """
        with self.assertRaises(ParseError):
            Parser(self.grammar, source).run()
    
