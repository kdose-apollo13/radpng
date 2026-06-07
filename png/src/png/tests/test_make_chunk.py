"""
RADICAL PNG TEST: make_chunk

One test file per atomic (make_chunk.py). GWT on every method.
Pure stdlib only.
"""
import struct
import sys
import zlib

from png.make_chunk import make_chunk
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestMakeChunk(PngTestCase):
    def test_make_chunk_basic_and_crc(self):
        """Given typ+data
        When make_chunk
        Then length correct + crc32(typ+data) matches the trailer
        """
        ch = make_chunk(b'IHDR', b'\0' * 13)
        self.equa(len(ch), 4 + 4 + 13 + 4)
        self.equa(ch[4:8], b'IHDR')
        crc = struct.unpack('>I', ch[-4:])[0]
        expected = zlib.crc32(b'IHDR' + b'\0' * 13) & 0xffffffff
        self.equa(crc, expected)
        self.assert_raises_value_err('4 bytes', make_chunk, b'ABC', b'')

    def test_make_chunk_empty_iend(self):
        """Given empty IEND chunk data
        When make_chunk
        Then length field is zero and type is IEND
        """
        iend = make_chunk(b'IEND', b'')
        self.equa(iend[:4], b'\x00\x00\x00\x00')
        self.equa(iend[4:8], b'IEND')
        self.equa(len(iend), 12)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
