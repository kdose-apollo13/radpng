"""
RADICAL PNG TEST: bpp

One test file per atomic (bpp.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.bpp import get_bpp


class TestBpp(RadicalTestCase):
    def test_bpp_matrix_and_edges(self):
        """Given the ct/bd matrix from spec + ihdr
        When calling get_bpp for valid + invalid
        Then correct byte counts (incl bit-packed) + ValueError on bad ct
        """
        self.equa(get_bpp(0, 8), 1)
        self.equa(get_bpp(0, 1), 1)
        self.equa(get_bpp(2, 8), 3)
        self.equa(get_bpp(6, 8), 4)
        self.equa(get_bpp(2, 16), 6)
        self.equa(get_bpp(0, 16), 2)
        self.equa(get_bpp(3, 4), 1)
        with self.rais(ValueError):
            get_bpp(99, 8)


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
