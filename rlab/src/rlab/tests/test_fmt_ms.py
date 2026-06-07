"""
RADICAL TEST: fmt_ms
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.fmt_ms import fmt_ms


class TestFmtMs(RadicalTestCase):
    def test_formats_to_milliseconds_fixed_width(self):
        """Given seconds
        When fmt_ms
        Then 8-char wide millisecond string with 3 decimals
        """
        self.equa(fmt_ms(0.01234), '  12.340')
        self.equa(fmt_ms(1.0), '1000.000')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
