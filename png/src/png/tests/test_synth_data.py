"""
RADICAL PNG TEST: synth_data

One test file per png_test atom. GWT on every method.
"""
import sys

from png.row_bytes import get_row_bytes
from png.synth_data import make_synthetic_image_data
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestSynthData(PngTestCase):
    def test_synth_data_length_matrix(self):
        """Given valid ct/bd combinations across the spec matrix
        When make_synthetic_image_data
        Then byte length matches height * get_row_bytes for each case
        """
        cases = [
            (4, 2, 0, 8), (4, 2, 2, 8), (4, 2, 3, 4), (4, 2, 4, 8), (4, 2, 6, 8),
            (8, 1, 0, 1), (8, 1, 0, 2), (8, 1, 0, 4), (2, 1, 6, 16),
        ]
        for w, h, ct, bd in cases:
            with self.subt(w=w, h=h, ct=ct, bd=bd):
                data = make_synthetic_image_data(w, h, ct, bd)
                expected = h * get_row_bytes(w, ct, bd)
                self.equa(len(data), expected)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
