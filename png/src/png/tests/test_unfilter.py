"""
RADICAL PNG TEST: unfilter

One test file per atomic (unfilter.py). GWT on every method.
Symmetry covered in test_filters; here direct + error paths.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.filters import apply_filter
from png.unfilter import unfilter


class TestUnfilter(RadicalTestCase):
    def test_unfilter_known_and_errors(self):
        """Given filtered bytes (from apply_filter) + bad lengths / types
        When unfilter
        Then recovers original or raises ValueError as documented
        """
        # basic round via apply (already proven in filters test; explicit here too)
        raw = b'\x10\x20\x30\x40'
        filt = apply_filter(raw, 4, 1, 0, 8, filter_type=2)
        self.equa(unfilter(filt, 4, 1, 0, 8), raw)

        # length error
        self.assert_raises_value_err('length', unfilter, b'\0\0\0', 4, 1, 0, 8)
        # bad filter type byte inside
        bad_ft = bytearray(filt)
        bad_ft[0] = 99
        self.assert_raises_value_err('invalid filter type', unfilter, bytes(bad_ft), 4, 1, 0, 8)


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
