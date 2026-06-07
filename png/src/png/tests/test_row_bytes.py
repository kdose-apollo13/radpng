"""
RADICAL PNG TEST: row_bytes

One test file per atomic (row_bytes.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.row_bytes import get_row_bytes


class TestRowBytes(RadicalTestCase):
    def test_row_bytes_matrix_and_edges(self):
        """Given the ct/bd matrix from spec + ihdr
        When calling get_row_bytes for valid + invalid
        Then correct byte counts (incl bit-packed) + ValueError on bad ct
        """
        self.equa(get_row_bytes(1, 0, 8), 1)
        self.equa(get_row_bytes(200, 0, 8), 200)
        self.equa(get_row_bytes(1, 2, 8), 3)
        self.equa(get_row_bytes(1, 6, 8), 4)
        self.equa(get_row_bytes(9, 0, 1), 2)  # 9 bits -> 2 bytes
        self.equa(get_row_bytes(1, 0, 1), 1)
        self.equa(get_row_bytes(1, 6, 16), 8)
        with self.rais(ValueError):
            get_row_bytes(10, 99, 8)


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
