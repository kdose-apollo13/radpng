"""
RADICAL PNG TEST: encoder

One test file per atomic (encoder.py). GWT on every method.
Holds validations + the bulk of roundtrip / matrix cases (radical: explicit coverage).
Reuses RadicalTestCase + helpers + packers from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
import zlib
from test_helpers import (
    RadicalTestCase, RadicalTextTestRunner,
    _pack_1bit, _pack_2bit, _pack_4bit,
    make_synthetic_png, make_synthetic_image_data,
)
from png.signature import PNG_SIGNATURE
from png.make_chunk import make_chunk
from png.ihdr import make_ihdr
from png.encoder import encode_png, encode_rgba
from png.decoder import decode_png, decode_rgba


class TestEncoder(RadicalTestCase):
    def test_encode_rgba_validations(self):
        """Given bad pixel structures
        When encode_rgba
        Then ValueError for empty / ragged / bad tuple len
        """
        self.assert_raises_value_err('non-empty', encode_rgba, [])
        self.assert_raises_value_err('same width', encode_rgba, [[(1,2,3,4)], [(1,2,3,4),(5,6,7,8)]])
        self.assert_raises_value_err('4-tuple', encode_rgba, [[(1,2,3)]])

    def test_encode_png_errors(self):
        """Given bad inputs to encode_png
        When called
        Then appropriate ValueError or NotImplemented (interlace)
        """
        ih = {'width':2,'height':1,'bit_depth':8,'color_type':0,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        self.assert_raises_value_err('length', encode_png, ih, b'abc')  # wrong len
        ih3 = dict(ih, color_type=3)
        self.assert_raises_value_err('palette', encode_png, ih3, b'\0\0')
        ih_i = dict(ih, interlace_method=1)
        with self.rais(NotImplementedError):
            encode_png(ih_i, b'\0\0')


class TestFullRoundtrips(RadicalTestCase):
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
        # ct0 bd8
        for ft in range(5):
            with self.subt(ct=0, bd=8, ft=ft):
                data = b'\x10\x20'
                self.assert_png_roundtrip(base_ih(0, 8), data, filter_type=ft)

        # ct3 bd8 + pal
        pal = [(10,20,30), (40,50,60)]
        data3 = b'\x00\x01'
        self.assert_png_roundtrip(base_ih(3, 8), data3, palette=pal, filter_type=0)

        # ct4 bd8
        data4 = b'\x11\xaa\x22\xbb'
        self.assert_png_roundtrip(base_ih(4, 8), data4, filter_type=2)

        # ct6 bd8 via high level
        pix = [[(1,2,3,255), (4,5,6,128)]]
        self.assert_rgba_roundtrip(pix, filter_type=4)

        # bd16 ct0 (w=2 needs 4 bytes for 16-bit samples)
        ih16 = base_ih(0, 16)
        data16 = b'\x01\x02\x03\x04'
        self.assert_png_roundtrip(ih16, data16, filter_type=0)

        # low bd ct0 (use packers; base w=2 so only 2 samples)
        data1 = _pack_1bit([1,0], 2)
        self.assert_png_roundtrip(base_ih(0, 1), data1, filter_type=1)
        data2 = _pack_2bit([0,3], 2)
        self.assert_png_roundtrip(base_ih(0, 2), data2, filter_type=3)
        data4b = _pack_4bit([15,0], 2)
        self.assert_png_roundtrip(base_ih(0, 4), data4b, filter_type=0)

    def test_1x1_edge_and_rgba(self):
        """Given 1x1 minimal cases
        When encode/decode (png + rgba)
        Then roundtrips and 1x1 decode_rgba works
        """
        p1 = encode_rgba([[(0,0,0,255)]])
        self.equa(decode_rgba(p1), [[(0, 0, 0, 255)]])
        self.assert_png_roundtrip(
            {'width':1,'height':1,'bit_depth':8,'color_type':0,
             'compression_method':0,'filter_method':0,'interlace_method':0},
            b'\x7f'
        )


class TestChunkEdges(RadicalTestCase):
    def test_split_idat_and_extra_chunks(self):
        """Given png constructed with split IDAT + extra ancillary
        When decode_png
        Then succeeds and data matches (decoder joins IDATs, ignores others)
        """
        ih = {'width':2,'height':1,'bit_depth':8,'color_type':0,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        raw = b'\xaa\xbb'
        comp = zlib.compress(b'\0' + raw)  # filter0
        # split into two idat payloads
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
        for w, h in [(1,1), (8,4), (16,8)]:
            for ct, bd, ft in [(0,8,0), (6,8,4), (2,8,2)]:
                with self.subt(w=w, h=h, ct=ct, bd=bd, ft=ft):
                    png = make_synthetic_png(w, h, ct, bd, filter_type=ft)
                    d = decode_png(png)
                    self.equa(d['width'], w)
                    self.equa(d['height'], h)
                    # re-encode the extracted data and compare
                    ih = {k: d[k] for k in ('width','height','bit_depth','color_type',
                                            'compression_method','filter_method','interlace_method')}
                    p2 = encode_png(ih, d['data'], filter_type=ft)
                    self.equa(decode_png(p2)['data'], d['data'])


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
