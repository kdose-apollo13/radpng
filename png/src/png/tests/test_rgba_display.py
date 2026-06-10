"""
RADICAL PNG TEST: rgba_display
"""
import sys

from png.rgba_display import bilinear_resize_rgba, rgba_rows_to_ppm
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestRgbaDisplay(RadicalTestCase):
    def test_ppm_header_and_resize(self):
        """Given a 2x1 RGBA row
        When converting to ppm and resizing 2x
        Then PPM header matches and resize doubles width
        """
        rows = [[(255, 0, 0, 255), (0, 255, 0, 255)]]
        ppm = rgba_rows_to_ppm(rows)
        self.isin(b'P6\n2 1\n255\n', ppm)
        out = bilinear_resize_rgba(rows, 2, 1, 4, 1)
        self.equa(len(out), 1)
        self.equa(len(out[0]), 4)
        self.equa(out[0][0][3], 255)

    def test_resize_identity(self):
        rows = [[(10, 20, 30, 255)]]
        same = bilinear_resize_rgba(rows, 1, 1, 1, 1)
        self.equa(same, rows)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)