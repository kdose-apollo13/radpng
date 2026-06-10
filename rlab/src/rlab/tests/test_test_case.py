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

if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
