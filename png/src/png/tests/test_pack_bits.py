"""
RADICAL PNG TEST: pack_bits

One test file per png_test atom. GWT on every method.
"""
import sys

from png.pack_bits import pack_1bit, pack_2bit, pack_4bit
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestPackBits(PngTestCase):
    def test_pack_1bit_msb_first(self):
        """Given alternating 1/0 bits
        When pack_1bit
        Then MSB-first byte pattern matches PNG layout
        """
        self.equa(pack_1bit([1, 0, 1, 0, 1, 0, 1, 0], 8), b'\xAA')
        self.equa(pack_1bit([1, 0], 2), b'\x80')
        self.equa(pack_1bit([], 8), b'\x00')

    def test_pack_2bit_and_4bit(self):
        """Given low bit-depth sample values
        When pack_2bit / pack_4bit
        Then high nibble/bits first per PNG spec
        """
        self.equa(pack_2bit([3, 0], 2), b'\xC0')
        self.equa(pack_4bit([15, 0], 2), b'\xF0')
        self.equa(pack_4bit([1, 2], 2), b'\x12')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
