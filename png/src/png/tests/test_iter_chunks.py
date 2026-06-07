"""
RADICAL PNG TEST: iter_chunks

One test file per atomic (iter_chunks.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import io
import zlib
import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.signature import PNG_SIGNATURE
from png.make_chunk import make_chunk
from png.ihdr import make_ihdr
from png.check_signature import check_signature
from png.iter_chunks import iter_chunks


class TestIterChunks(RadicalTestCase):
    def test_iter_chunks_good_and_bad_crc_trunc(self):
        """Given minimal good png bytes + corrupted/truncated variants
        When iter_chunks (after sig)
        Then yields expected (IHDR,IDAT,IEND); raises on crc / trunc
        """
        # build a tiny valid png using our encoder (ct0 1x1)
        ih = {'width':1,'height':1,'bit_depth':8,'color_type':0,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        p = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
            make_chunk(b'IDAT', zlib.compress(b'\0\xff')) + make_chunk(b'IEND', b'')
        with io.BytesIO(p) as f:
            check_signature(f)
            chunks = list(iter_chunks(f))
            self.equa([t for t,d in chunks], [b'IHDR', b'IDAT', b'IEND'])

        # bad crc
        bad = bytearray(p)
        bad[-5] ^= 0xff  # flip in IEND crc area-ish
        with io.BytesIO(bad) as f:
            check_signature(f)
            with self.rais(ValueError) as ctx:
                list(iter_chunks(f))
            self.isin('CRC', str(ctx.exception))

        # trunc
        short = p[:-10]
        with io.BytesIO(short) as f:
            check_signature(f)
            with self.rais(ValueError):
                list(iter_chunks(f))


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
