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
from png.pack_bits import pack_1bit, pack_2bit, pack_4bit
# from png.synth_png import make_synthetic_png
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestEncoder(PngTestCase):
    def test_encode_rgba_validations(self):
        """Given bad pixel structures
        When encode_rgba
        Then ValueError for empty / ragged / bad tuple len
        """
        self.assert_raises_value_err('non-empty', encode_rgba, [])
        self.assert_raises_value_err('same width', encode_rgba, [[(1, 2, 3, 4)], [(1, 2, 3, 4), (5, 6, 7, 8)]])
        self.assert_raises_value_err('4-tuple', encode_rgba, [[(1, 2, 3)]])

    def test_encode_png_errors(self):
        """Given bad inputs to encode_png
        When called
        Then appropriate ValueError or NotImplemented (interlace)
        """
        ih = {'width': 2, 'height': 1, 'bit_depth': 8, 'color_type': 0,
              'compression_method': 0, 'filter_method': 0, 'interlace_method': 0}
        self.assert_raises_value_err('length', encode_png, ih, b'abc')
        ih3 = dict(ih, color_type=3)
        self.assert_raises_value_err('palette', encode_png, ih3, b'\0\0')
        ih_i = dict(ih, interlace_method=1)
        with self.rais(NotImplementedError):
            encode_png(ih_i, b'\0\0')


class TestFullRoundtrips(PngTestCase):
    def test_roundtrips_various_ct_bd_ft_small(self):
        """Given small images across ct 0/2/3/4/6 , bd extremes, all ft
        When encode_png (or rgba) + decode_png/rgba
        Then data + fields roundtrip exactly (via assert_png_roundtrip helper)
        """
        base_ih = lambda ct, bd: {
            'width': 2, 'height': 1,
            'bit_depth': bd, 'color_type': ct,
            'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
        }
        for ft in range(5):
            with self.subt(ct=0, bd=8, ft=ft):
                self.assert_png_roundtrip(base_ih(0, 8), b'\x10\x20', filter_type=ft)

        pal = [(10, 20, 30), (40, 50, 60)]
        self.assert_png_roundtrip(base_ih(3, 8), b'\x00\x01', palette=pal, filter_type=0)
        self.assert_png_roundtrip(base_ih(4, 8), b'\x11\xaa\x22\xbb', filter_type=2)
        self.assert_rgba_roundtrip([[(1, 2, 3, 255), (4, 5, 6, 128)]], filter_type=4)
        self.assert_png_roundtrip(base_ih(0, 16), b'\x01\x02\x03\x04', filter_type=0)

        self.assert_png_roundtrip(base_ih(0, 1), pack_1bit([1, 0], 2), filter_type=1)
        self.assert_png_roundtrip(base_ih(0, 2), pack_2bit([0, 3], 2), filter_type=3)
        self.assert_png_roundtrip(base_ih(0, 4), pack_4bit([15, 0], 2), filter_type=0)

    def test_1x1_edge_and_rgba(self):
        """Given 1x1 minimal cases
        When encode/decode (png + rgba)
        Then roundtrips and 1x1 decode_rgba works
        """
        p1 = encode_rgba([[(0, 0, 0, 255)]])
        self.equa(decode_rgba(p1), [[(0, 0, 0, 255)]])
        self.assert_png_roundtrip(
            {'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 0,
             'compression_method': 0, 'filter_method': 0, 'interlace_method': 0},
            b'\x7f'
        )


class TestChunkEdges(PngTestCase):
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

    def test_on_demand_synth_sizes_roundtrip(self):
        """Given the make_synthetic_* helpers (different file sizes)
        When encode/decode roundtrip via the helpers
        Then exact data match for several sizes (proves size scaling works)
        """
        for w, h in [(1, 1), (8, 4), (16, 8)]:
            for ct, bd, ft in [(0, 8, 0), (6, 8, 4), (2, 8, 2)]:
                with self.subt(w=w, h=h, ct=ct, bd=bd, ft=ft):
                    png = make_synthetic_png(w, h, ct, bd, filter_type=ft)
                    d = decode_png(png)
                    self.equa(d['width'], w)
                    self.equa(d['height'], h)
                    ih = {k: d[k] for k in ('width', 'height', 'bit_depth', 'color_type',
                                            'compression_method', 'filter_method', 'interlace_method')}
                    p2 = encode_png(ih, d['data'], filter_type=ft)
                    self.equa(decode_png(p2)['data'], d['data'])


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
