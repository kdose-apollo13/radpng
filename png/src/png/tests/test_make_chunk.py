"""
RADICAL PNG TEST: make_chunk

One test file per atomic (make_chunk.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import struct
import zlib
import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.make_chunk import make_chunk


class TestMakeChunk(RadicalTestCase):
    def test_make_chunk_basic_and_crc(self):
        """Given typ+data
        When make_chunk
        Then length correct + crc32(typ+data) matches the trailer
        """
        ch = make_chunk(b'IHDR', b'\0'*13)
        self.equa(len(ch), 4+4+13+4)
        self.equa(ch[4:8], b'IHDR')
        crc = struct.unpack('>I', ch[-4:])[0]
        expected = zlib.crc32(b'IHDR' + b'\0'*13) & 0xffffffff
        self.equa(crc, expected)

        self.assert_raises_value_err('4 bytes', make_chunk, b'ABC', b'')


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
