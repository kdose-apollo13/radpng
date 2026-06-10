"""
RADICAL PNG TEST: ihdr

One test file per atomic (ihdr.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.ihdr import parse_ihdr, make_ihdr
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestIhdr(PngTestCase):
    def test_ihdr_make_parse_roundtrip_valid(self):
        """Given valid ihdr dicts for several ct/bd (incl defaults)
        When make_ihdr then parse_ihdr
        Then roundtrips exactly (methods defaulted to 0)
        """
        cases = [
            {'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 0},
            {'width': 200, 'height': 100, 'bit_depth': 8, 'color_type': 2},
            {'width': 4, 'height': 4, 'bit_depth': 4, 'color_type': 3},
        ]
        for d in cases:
            with self.subt(ct=d['color_type'], bd=d['bit_depth']):
                full = {**d, 'compression_method': 0, 'filter_method': 0, 'interlace_method': 0}
                self.equa(parse_ihdr(make_ihdr(d)), full)

    def test_ihdr_parse_errors(self):
        """Given bad ihdr bytes (len, zero dim, bad methods, bad ct/bd combo)
        When parse_ihdr
        Then ValueError with informative message
        """
        with self.rais(ValueError):
            parse_ihdr(b'abc')
        with self.rais(ValueError):
            parse_ihdr(make_ihdr({'width': 0, 'height': 1, 'bit_depth': 8, 'color_type': 0}))
        with self.rais(ValueError):
            parse_ihdr(make_ihdr({'width': 1, 'height': 0, 'bit_depth': 8, 'color_type': 0}))
        with self.rais(ValueError):
            parse_ihdr(b'\0\0\0\1\0\0\0\1\x08\x00\x01\x00\x00')
        with self.rais(ValueError):
            parse_ihdr(make_ihdr({'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 1}))
        with self.rais(ValueError):
            parse_ihdr(make_ihdr({'width': 1, 'height': 1, 'bit_depth': 2, 'color_type': 2}))


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
