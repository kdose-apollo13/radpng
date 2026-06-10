"""
RADICAL PNG TEST: unfilter

One test file per atomic (unfilter.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.filters import apply_filter
from png.unfilter import unfilter
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestUnfilter(PngTestCase):
    def test_unfilter_known_and_errors(self):
        """Given filtered bytes (from apply_filter) + bad lengths / types
        When unfilter
        Then recovers original or raises ValueError as documented
        """
        raw = b'\x10\x20\x30\x40'
        filt = apply_filter(raw, 4, 1, 0, 8, filter_type=2)
        self.equa(unfilter(filt, 4, 1, 0, 8), raw)
        with self.rais(ValueError):
            unfilter(b'\0\0\0', 4, 1, 0, 8)
        bad_ft = bytearray(filt)
        bad_ft[0] = 99
        with self.rais(ValueError):
            unfilter(bytes(bad_ft), 4, 1, 0, 8)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
