"""
RADICAL PNG TEST: bpp

One test file per atomic (bpp.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.bpp import get_bpp
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestBpp(PngTestCase):
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


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
