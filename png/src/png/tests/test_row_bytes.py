"""
RADICAL PNG TEST: row_bytes

One test file per atomic (row_bytes.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.row_bytes import get_row_bytes
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


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
        self.equa(get_row_bytes(9, 0, 1), 2)
        self.equa(get_row_bytes(1, 0, 1), 1)
        self.equa(get_row_bytes(1, 6, 16), 8)
        with self.rais(ValueError):
            get_row_bytes(10, 99, 8)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
