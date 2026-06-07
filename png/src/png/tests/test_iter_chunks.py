"""
RADICAL PNG TEST: iter_chunks

One test file per atomic (iter_chunks.py). GWT on every method.
Pure stdlib only.
"""
import io
import sys
import zlib

from png.signature import PNG_SIGNATURE
from png.make_chunk import make_chunk
from png.ihdr import make_ihdr
from png.check_signature import check_signature
from png.iter_chunks import iter_chunks
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestIterChunks(PngTestCase):
    def test_iter_chunks_good_and_bad_crc_trunc(self):
        """Given minimal good png bytes + corrupted/truncated variants
        When iter_chunks (after sig)
        Then yields expected (IHDR,IDAT,IEND); raises on crc / trunc
        """
        ih = {'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 0,
              'compression_method': 0, 'filter_method': 0, 'interlace_method': 0}
        p = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
            make_chunk(b'IDAT', zlib.compress(b'\0\xff')) + make_chunk(b'IEND', b'')
        with io.BytesIO(p) as f:
            check_signature(f)
            chunks = list(iter_chunks(f))
            self.equa([t for t, d in chunks], [b'IHDR', b'IDAT', b'IEND'])

        bad = bytearray(p)
        bad[-5] ^= 0xff
        with io.BytesIO(bad) as f:
            check_signature(f)
            with self.rais(ValueError) as ctx:
                list(iter_chunks(f))
            self.isin('CRC', str(ctx.exception))

        short = p[:-10]
        with io.BytesIO(short) as f:
            check_signature(f)
            with self.rais(ValueError):
                list(iter_chunks(f))

    def test_iter_chunks_missing_chunk_type(self):
        """Given bytes with length field but truncated chunk type
        When iter_chunks
        Then ValueError mentioning chunk type
        """
        # sig + 4-byte length only (no type/data/crc)
        partial = PNG_SIGNATURE + b'\x00\x00\x00\x0d'
        with io.BytesIO(partial) as f:
            check_signature(f)

            def consume():
                list(iter_chunks(f))

            self.assert_raises_value_err('chunk type', consume)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
