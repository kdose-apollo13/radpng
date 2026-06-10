"""
    RadicalTestCase
    unittest.TestCase with short aliases (self.rais, self.equa, etc.)
"""
import unittest

# Radical hook: make `python -m unittest -v` (and plain discovery from the tests dir)
# emit the speclike GWT output. Because every test module imports RadicalTestCase
# during loading, this swap happens before TestProgram instantiates its runner.
import unittest as _unittest
from rlab.test_runner import RadicalTextTestRunner as _RadicalTextTestRunner
_unittest.TextTestRunner = _RadicalTextTestRunner


class RadicalTestCase(unittest.TestCase):
    """
        aliases (set in __init__)
            self.asrt = assertTrue
            self.equa = assertEqual
            self.rais = assertRaises
            self.subt = subTest
            self.nota = assertFalse
            self.isin = assertIn

        Use self.rais(Exc) uniformly for exception tests (any Exc, including ValueError).
        Capture ctx when you need to inspect the message.
    """

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.asrt = self.assertTrue
        self.equa = self.assertEqual
        self.rais = self.assertRaises
        self.subt = self.subTest
        self.nota = self.assertFalse
        self.isin = self.assertIn

if __name__ == '__main__':
    print('=== RadicalTestCase demo ===')
    t = RadicalTestCase()

    def _raise_sig():
        raise ValueError('bad PNG signature')

    t.equa(1 + 1, 2)
    # Uniform style: self.rais(Exc) for any exception type (ValueError included).
    # When you care about the message, capture the context and use isin.
    with t.rais(ValueError) as ctx:
        _raise_sig()
    t.isin('signature', str(ctx.exception).lower())
    print('RadicalTestCase ok')
