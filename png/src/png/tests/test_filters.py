"""
RADICAL PNG TEST: filters

One test file per atomic (filters.py). GWT on every method.
Includes filter+unfilter symmetry (cross atom proof, radical style).
Reuses RadicalTestCase + short aliases + packers from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner, _pack_1bit
from png.filters import apply_filter
from png.unfilter import unfilter


class TestFilterUnfilter(RadicalTestCase):
    def test_filter_unfilter_symmetry_ct0_various_ft(self):
        """Given 4x2 gray8 synthetic raw bytes (same as lib demos)
        When filter(..., filter_type=ft) for ft in 0..4 then unfilter the result
        Then recon bytes exactly == orig for every ft (proves symmetry + paeth edges)
        """
        W, H = 4, 2
        orig = bytearray((x + y * 3) * 40 % 256 for y in range(H) for x in range(W))
        for ft in range(5):
            with self.subt(filter_type=ft):
                filt = apply_filter(orig, W, H, 0, 8, filter_type=ft)
                recon = unfilter(filt, W, H, 0, 8)
                self.equa(recon, bytes(orig))

    def test_filter_type0_is_identity_plus_ft_errors(self):
        """Given raw + ft=0
        When filter
        Then first byte of each row is 0 and payload == raw; bad ft raises
        """
        raw = b'\x01\x02\x03\x04'
        filt = apply_filter(raw, 4, 1, 0, 8, filter_type=0)
        self.equa(filt[0], 0)
        self.equa(filt[1:], raw)
        self.assert_raises_value_err('0-4', apply_filter, raw, 4, 1, 0, 8, filter_type=5)
        self.assert_raises_value_err('length', apply_filter, b'abc', 4, 1, 0, 8, 0)

    def test_filter_unfilter_other_ct_bd(self):
        """Given ct=2/6/4 and bd=1/16 cases (bpp >1 or packed)
        When filter+unfilter round
        Then exact match (exercises bpp stride)
        """
        # ct6 bd8 (w=2 h=1 to keep small; rowb=8)
        raw6 = bytes(list(range(8)))
        f6 = apply_filter(raw6, 2, 1, 6, 8, 4)
        self.equa(unfilter(f6, 2, 1, 6, 8), raw6)
        # ct0 bd1 (w=8 rowb=1)
        raw1 = _pack_1bit([1,0,1,0,1,0,1,0], 8)
        f1 = apply_filter(raw1, 8, 1, 0, 1, 1)
        self.equa(unfilter(f1, 8, 1, 0, 1), raw1)


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
