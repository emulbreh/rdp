import unittest

from rdp.symbols import to_symbol, Symbol, Terminal


class SymbolsTest(unittest.TestCase):
    def test_to_symbol(self):
        self.assertTrue(isinstance(to_symbol(','), Symbol))
        self.assertTrue(isinstance(to_symbol(Terminal(',')), Symbol))

        self.assertRaises(TypeError, to_symbol, 42)

