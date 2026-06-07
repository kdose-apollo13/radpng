"""
RADICAL TEST: test_case

One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestRadicalTestCase(RadicalTestCase):
    def test_short_aliases(self):
        """Given a RadicalTestCase instance
        When using short aliases
        Then they delegate to standard assert methods
        """
        self.asrt(True)
        self.nota(False)
        self.equa(2, 1 + 1)
        self.isin('a', 'abc')

    def test_assert_raises_value_err_match(self):
        """Given a callable that raises ValueError
        When assert_raises_value_err with matching substring
        Then passes silently
        """
        def bad():
            raise ValueError('bad PNG signature: got xx')
        self.assert_raises_value_err('signature', bad)

    def test_assert_raises_value_err_mismatch(self):
        """Given a callable that raises ValueError with wrong message
        When assert_raises_value_err expects different substring
        Then AssertionError
        """
        def bad():
            raise ValueError('other problem')
        with self.rais(AssertionError):
            self.assert_raises_value_err('signature', bad)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
