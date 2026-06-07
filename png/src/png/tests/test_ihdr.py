"""
RADICAL PNG TEST: ihdr

One test file per atomic (ihdr.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.ihdr import parse_ihdr, make_ihdr


class TestIHDR(RadicalTestCase):
    def test_ihdr_make_parse_roundtrip_valid(self):
        """Given valid ihdr dicts for several ct/bd (incl defaults)
        When make_ihdr then parse_ihdr
        Then roundtrips exactly (methods defaulted to 0)
        """
        d = {
            'width': 4, 'height': 2,
            'bit_depth': 8, 'color_type': 0,
            'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
        }
        self.equa(parse_ihdr(make_ihdr(d)), d)

        d2 = {'width': 1, 'height': 1, 'bit_depth': 1, 'color_type': 3}
        made = make_ihdr(d2)
        p = parse_ihdr(made)
        self.equa(p['width'], 1)
        self.equa(p['bit_depth'], 1)
        self.equa(p['color_type'], 3)

    def test_ihdr_parse_errors(self):
        """Given bad ihdr bytes (len, zero dim, bad methods, bad ct/bd combo)
        When parse_ihdr
        Then ValueError with informative message
        """
        self.assert_raises_value_err('13 bytes', parse_ihdr, b'abc')
        self.assert_raises_value_err('> 0', parse_ihdr, make_ihdr({'width': 0, 'height': 1, 'bit_depth': 8, 'color_type': 0}))
        self.assert_raises_value_err('> 0', parse_ihdr, make_ihdr({'width': 1, 'height': 0, 'bit_depth': 8, 'color_type': 0}))
        # w=1 h=1 bd=8 ct=0 comp=1 -> hits comp check (before ct/bd matrix)
        self.assert_raises_value_err('compression', parse_ihdr, b'\0\0\0\1\0\0\0\1\x08\x00\x01\x00\x00')
        self.assert_raises_value_err('color_type', parse_ihdr, make_ihdr({'width':1,'height':1,'bit_depth':8,'color_type':1}))
        self.assert_raises_value_err('bit_depth', parse_ihdr, make_ihdr({'width':1,'height':1,'bit_depth':2,'color_type':2}))


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
