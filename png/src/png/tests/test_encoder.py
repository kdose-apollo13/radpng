"""
RADICAL PNG TEST: encoder

One test file per atomic (encoder.py). GWT on every method.
Pure stdlib only.
"""
import sys
import zlib

from png.signature import PNG_SIGNATURE
from png.make_chunk import make_chunk
from png.ihdr import make_ihdr
from png.encoder import encode_png, encode_rgba
from png.decoder import decode_png, decode_rgba
from png.baselines import gen_grey, gen_rgb, gen_rgba, gen_indexed
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestEncoder(RadicalTestCase):
    def test_encode_rgba_validations(self):
        """Given bad pixel structures
        When encode_rgba
        Then ValueError for empty / ragged / bad tuple len
        """
        with self.rais(ValueError):
            encode_rgba([])
        with self.rais(ValueError):
            encode_rgba([[(1, 2, 3, 4)], [(1, 2, 3, 4), (5, 6, 7, 8)]])
        with self.rais(ValueError):
            encode_rgba([[(1, 2, 3)]])

    def test_encode_png_errors(self):
        """Given bad inputs to encode_png
        When called
        Then appropriate ValueError (length, missing palette, etc.)
        """
        ih = {'width': 2, 'height': 1, 'bit_depth': 8, 'color_type': 0,
              'compression_method': 0, 'filter_method': 0, 'interlace_method': 0}
        with self.rais(ValueError):
            encode_png(ih, b'abc')
        ih3 = dict(ih, color_type=3)
        with self.rais(ValueError):
            encode_png(ih3, b'\0\0')
        # interlace=1 is now supported (see test_interlace)


class TestChunkEdges(RadicalTestCase):
    def test_split_idat_and_extra_chunks(self):
        """Given png constructed with split IDAT + extra ancillary
        When decode_png
        Then succeeds and data matches (decoder joins IDATs, ignores others)
        """
        ih = {'width': 2, 'height': 1, 'bit_depth': 8, 'color_type': 0,
              'compression_method': 0, 'filter_method': 0, 'interlace_method': 0}
        raw = b'\xaa\xbb'
        comp = zlib.compress(b'\0' + raw)
        mid = len(comp) // 2 or 1
        id1, id2 = comp[:mid], comp[mid:]
        png = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
            make_chunk(b'IDAT', id1) + make_chunk(b'IDAT', id2) + \
            make_chunk(b'tEXt', b'key\0value from radical test') + \
            make_chunk(b'IEND', b'')
        dec = decode_png(png)
        self.equa(dec['data'], raw)
        self.equa(dec['color_type'], 0)

    def test_sizes_roundtrip_via_baseline_generators(self):
        """Given baseline generators for varied (w,h,ct,bd,ft)
        When encode_png + decode_png + re-encode roundtrip
        Then exact data match for several sizes (proves size scaling works)
        """
        for w, h in [(1, 1), (8, 4), (16, 8)]:
            for ct, bd, ft in [(0, 8, 0), (6, 8, 4), (2, 8, 2)]:
                with self.subt(w=w, h=h, ct=ct, bd=bd, ft=ft):
                    if ct == 3:
                        data, palette = gen_indexed(w, h, bd)  # not exercised in this loop
                    elif ct == 0:
                        data = gen_grey(w, h, bd)
                        palette = None
                    elif ct == 2:
                        data = gen_rgb(w, h, bd)
                        palette = None
                    else:
                        data = gen_rgba(w, h, bd)
                        palette = None
                    ihdr = {
                        'width': w, 'height': h, 'bit_depth': bd, 'color_type': ct,
                        'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
                    }
                    png = encode_png(ihdr, bytes(data), palette=palette, filter_type=ft)
                    d = decode_png(png)
                    self.equa(d['width'], w)
                    self.equa(d['height'], h)
                    p2 = encode_png(ihdr, d['data'], palette=palette, filter_type=ft)
                    self.equa(decode_png(p2)['data'], d['data'])


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
