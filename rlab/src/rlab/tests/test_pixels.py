"""
RADICAL TEST: pixels
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.pixels import pixels_from_size


class TestPixels(RadicalTestCase):
    def test_bare_int_is_its_own_pixels(self):
        """Given a bare integer size
        When pixels_from_size
        Then the integer itself is returned (treated as n units/pixels)
        """
        self.equa(pixels_from_size(42), 42)
        self.equa(pixels_from_size(0), 0)

    def test_w_h_tuple_or_list_yields_product(self):
        """Given (w, h) or [w, h]
        When pixels_from_size
        Then width * height
        """
        self.equa(pixels_from_size((4, 2)), 8)
        self.equa(pixels_from_size([8, 4]), 32)

    def test_other_shapes_yield_none(self):
        """Given strings, wrong-length tuples, etc.
        When pixels_from_size
        Then None (best-effort, no derivation)
        """
        self.equa(pixels_from_size("not a size"), None)
        self.equa(pixels_from_size((1, 2, 3)), None)
        self.equa(pixels_from_size(None), None)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
