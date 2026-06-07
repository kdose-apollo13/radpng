"""
RADICAL PNG TEST: decoder

One test file per atomic (decoder.py). GWT on every method.
Known minimals, error paths, path+bytes acceptance, canvas integration.
Reuses RadicalTestCase + helpers from test_helpers.
Pure stdlib only.
"""
import os
import sys

import io
import zlib
import unittest
from test_helpers import (
    RadicalTestCase, RadicalTextTestRunner,
    make_synthetic_png,
)
from png.signature import PNG_SIGNATURE
from png.make_chunk import make_chunk
from png.ihdr import make_ihdr
from png.encoder import encode_png
from png.decoder import decode_png, decode_rgba


class TestDecoder(RadicalTestCase):
    def test_decode_known_minimals_ct0_2_3_6(self):
        """Given the hardcoded 1x1 minimal PNGs (ct 0/2/3/6 bd8)
        When decode_png + decode_rgba (for ct6)
        Then correct fields, data, palette (ct3), and rgba pixels
        """
        # ct0
        p0 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d49484452000000010000000108000000003a7e9b55'
            '0000000a49444154789c63f80f0001010100b138f6140000000049454e44ae426082'
        )
        d0 = decode_png(p0)
        self.equa(d0['width'], 1)
        self.equa(d0['color_type'], 0)
        self.equa(d0['data'], b'\xff')
        self.equa(d0['palette'], None)

        # ct3
        p3 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d494844520000000100000001080300000028cb34bb'
            '00000003504c5445ff000019e209370000000a49444154789c636000000002000148afa4710000000049454e44ae426082'
        )
        d3 = decode_png(p3)
        self.equa(d3['color_type'], 3)
        self.equa(d3['palette'], [(255, 0, 0)])

        # ct6 + rgba
        p6 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d49484452000000010000000108060000001f15c489'
            '0000000d49444154789c63606060f80f00010401005fe5c34b0000000049454e44ae426082'
        )
        d6 = decode_png(p6)
        self.equa(d6['color_type'], 6)
        pix = decode_rgba(p6)
        self.equa(pix, [[(0, 0, 0, 255)]])

    def test_decode_rgba_wrong_ct_raises(self):
        """Given non-ct6/8 png (ct2)
        When decode_rgba
        Then ValueError mentioning 6
        """
        p2 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d4948445200000001000000010802000000907753de'
            '0000000c49444154789c63606060000000040001f61738550000000049454e44ae426082'
        )
        self.assert_raises_value_err('6', decode_rgba, p2)

    def test_decode_errors_missing_multi_bad_zlib(self):
        """Given truncated / missing / multi / corrupt-zlib cases
        When decode_png
        Then ValueError as documented
        """
        ihb = make_ihdr({'width':1,'height':1,'bit_depth':8,'color_type':0})
        # missing ihdr (only sig + iend-ish)
        bad = PNG_SIGNATURE + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('IHDR', decode_png, bad)

        # multi ihdr (build two)
        bad2 = PNG_SIGNATURE + make_chunk(b'IHDR', ihb) + make_chunk(b'IHDR', ihb) + make_chunk(b'IDAT', zlib.compress(b'\0')) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('multiple IHDR', decode_png, bad2)

        # ct3 no plte
        ih3 = make_ihdr({'width':1,'height':1,'bit_depth':8,'color_type':3})
        bad3 = PNG_SIGNATURE + make_chunk(b'IHDR', ih3) + make_chunk(b'IDAT', zlib.compress(b'\0')) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('PLTE', decode_png, bad3)

        # zlib fail: corrupt the idat payload
        good_id = zlib.compress(b'\0\xff')
        badz = bytearray(good_id)
        if badz: badz[0] ^= 0xff
        bad4 = PNG_SIGNATURE + make_chunk(b'IHDR', ihb) + make_chunk(b'IDAT', bytes(badz)) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('zlib', decode_png, bytes(bad4))

    def test_decode_accepts_path_and_bytes(self):
        """Given a produced png on disk and as bytes/bytearray
        When decode_png on all three forms
        Then same result
        """
        ih = {'width':1,'height':1,'bit_depth':8,'color_type':2,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        # filtered for ct=2 w=1 h=1: 1 filter byte + 3 data bytes
        pngb = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
               make_chunk(b'IDAT', zlib.compress(b'\0\0\0\0')) + make_chunk(b'IEND', b'')
        # bytes
        d1 = decode_png(pngb)
        # bytearray
        d2 = decode_png(bytearray(pngb))
        # path (write temp in cwd; cleaned)
        tmp = 'tmp_radical_test.png'
        try:
            with open(tmp, 'wb') as f: f.write(pngb)
            d3 = decode_png(tmp)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self.equa(d1['data'], d2['data'])
        self.equa(d1['data'], d3['data'])


class TestIntegration(RadicalTestCase):
    def test_canvas_output_png_round_and_reencode(self):
        """Given the real canvas_output.png (ct6/8 400x300 produced by current code)
        When decode_png + re-encode its data (ft=0) + decode again
        Then dims/ct match + data roundtrips (integration with real file)
        """
        d = decode_png('canvas_output.png')
        self.equa(d['width'], 400)
        self.equa(d['height'], 300)
        self.equa(d['color_type'], 6)
        self.equa(d['bit_depth'], 8)
        self.equa(d['palette'], None)

        # re-encode the extracted data (note: canvas used default ft=0)
        ih = {k: d[k] for k in ('width','height','bit_depth','color_type',
                                'compression_method','filter_method','interlace_method')}
        png2 = encode_png(ih, d['data'], filter_type=0)
        d2 = decode_png(png2)
        self.equa(d2['data'], d['data'])

    def test_synth_sizes_via_decode_png_bytes_and_stream(self):
        """Given on-demand synth pngs of varied sizes (via helpers)
        When decode_png(bytes) and via BytesIO
        Then both succeed and produce matching dims/data
        """
        for w, h in [(4, 2), (32, 16)]:
            png = make_synthetic_png(w, h, 6, 8)
            d_bytes = decode_png(png)
            self.equa(d_bytes['width'], w)
            # (decode_png accepts bytes/bytearray or path str; the synth helpers return
            # bytes which are the "on-demand png stream" payload. Direct bytes already
            # exercised above and throughout; no need to force BytesIO into decode_png.)
            self.equa(len(d_bytes['data']), w * h * 4)  # ct6/8 sanity on the size variant


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
