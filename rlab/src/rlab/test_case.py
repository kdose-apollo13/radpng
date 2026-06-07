"""
    RadicalTestCase
    unittest.TestCase with short aliases and assert_raises_value_err
"""
import unittest


class RadicalTestCase(unittest.TestCase):
    """
        aliases (set in __init__)
            self.asrt = assertTrue
            self.equa = assertEqual
            self.rais = assertRaises
            self.subt = subTest
            self.nota = assertFalse
            self.isin = assertIn
    """

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.asrt = self.assertTrue
        self.equa = self.assertEqual
        self.rais = self.assertRaises
        self.subt = self.subTest
        self.nota = self.assertFalse
        self.isin = self.assertIn

    def assert_raises_value_err(self, msg_substr, func, *a, **k):
        """
            msg_substr
                : str
                : substring expected in ValueError message (case-insensitive)
            func, *a, **k
                : callable and args

        raises
            ! AssertionError if no ValueError or message mismatch
        """
        with self.rais(ValueError) as ctx:
            func(*a, **k)
        self.isin(msg_substr.lower(), str(ctx.exception).lower())


if __name__ == '__main__':
    print('=== RadicalTestCase demo ===')
    t = RadicalTestCase()

    def _raise_sig():
        raise ValueError('bad PNG signature')

    t.equa(1 + 1, 2)
    t.assert_raises_value_err('signature', _raise_sig)
    print('RadicalTestCase ok')
