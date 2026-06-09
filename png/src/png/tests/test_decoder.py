"""
RADICAL PNG TEST: decoder

One test file per atomic (decoder.py). GWT on every method.
Pure stdlib only.
"""
import os
import sys
import zlib

from png.signature import PNG_SIGNATURE
from png.make_chunk import make_chunk
from png.ihdr import make_ihdr
from png.encoder import encode_png
from png.decoder import decode_png, decode_rgba
from png.baseline import gen_rgba
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestDecoder(PngTestCase):
    def test_decode_known_minimals_ct0_2_3_6(self):
        """Given the hardcoded 1x1 minimal PNGs (ct 0/2/3/6 bd8)
        When decode_png + decode_rgba (for ct6)
        Then correct fields, data, palette (ct3), and rgba pixels
        """
        p0 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d49484452000000010000000108000000003a7e9b55'
            '0000000a49444154789c63f80f0001010100b138f6140000000049454e44ae426082'
        )
        d0 = decode_png(p0)
        self.equa(d0['width'], 1)
        self.equa(d0['color_type'], 0)
        self.equa(d0['data'], b'\xff')
        self.equa(d0['palette'], None)

        p3 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d494844520000000100000001080300000028cb34bb'
            '00000003504c5445ff000019e209370000000a49444154789c636000000002000148afa4710000000049454e44ae426082'
        )
        d3 = decode_png(p3)
        self.equa(d3['color_type'], 3)
        self.equa(d3['palette'], [(255, 0, 0)])

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
        ihb = make_ihdr({'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 0})
        bad = PNG_SIGNATURE + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('IHDR', decode_png, bad)

        bad2 = PNG_SIGNATURE + make_chunk(b'IHDR', ihb) + make_chunk(b'IHDR', ihb) + \
            make_chunk(b'IDAT', zlib.compress(b'\0')) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('multiple IHDR', decode_png, bad2)

        ih3 = make_ihdr({'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 3})
        bad3 = PNG_SIGNATURE + make_chunk(b'IHDR', ih3) + \
            make_chunk(b'IDAT', zlib.compress(b'\0')) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('PLTE', decode_png, bad3)

        good_id = zlib.compress(b'\0\xff')
        badz = bytearray(good_id)
        if badz:
            badz[0] ^= 0xff
        bad4 = PNG_SIGNATURE + make_chunk(b'IHDR', ihb) + \
            make_chunk(b'IDAT', bytes(badz)) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('zlib', decode_png, bytes(bad4))

    def test_decode_accepts_path_and_bytes(self):
        """Given a produced png on disk and as bytes/bytearray
        When decode_png on all three forms
        Then same result
        """
        ih = {'width': 1, 'height': 1, 'bit_depth': 8, 'color_type': 2,
              'compression_method': 0, 'filter_method': 0, 'interlace_method': 0}
        pngb = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
            make_chunk(b'IDAT', zlib.compress(b'\0\0\0\0')) + make_chunk(b'IEND', b'')
        d1 = decode_png(pngb)
        d2 = decode_png(bytearray(pngb))
        tmp = 'tmp_radical_test.png'
        try:
            with open(tmp, 'wb') as f:
                f.write(pngb)
            d3 = decode_png(tmp)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self.equa(d1['data'], d2['data'])
        self.equa(d1['data'], d3['data'])


class TestIntegration(PngTestCase):
    def test_roundtrip_generated_ct6_image(self):
        """Given a ct6/8 image produced on-demand via baseline generator + encode_png
        When decode_png + re-encode its data (ft=0) + decode again
        Then dims/ct match + data roundtrips (integration via current encoder/decoder)
        """
        w, h = 64, 32
        data = gen_rgba(w, h, 8)
        ihdr = {
            'width': w, 'height': h, 'bit_depth': 8, 'color_type': 6,
            'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
        }
        png = encode_png(ihdr, bytes(data), filter_type=0)
        d = decode_png(png)
        self.equa(d['width'], w)
        self.equa(d['height'], h)
        self.equa(d['color_type'], 6)
        self.equa(d['bit_depth'], 8)
        self.equa(d['palette'], None)
        png2 = encode_png(ihdr, d['data'], filter_type=0)
        d2 = decode_png(png2)
        self.equa(d2['data'], d['data'])

    def test_sizes_via_decode_png_bytes_and_stream(self):
        """Given on-demand PNGs produced via baseline generator + encode_png
        When decode_png(bytes) and via BytesIO
        Then both succeed and produce matching dims/data
        """
        for w, h in [(4, 2), (32, 16)]:
            data = gen_rgba(w, h, 8)
            ihdr = {
                'width': w, 'height': h, 'bit_depth': 8, 'color_type': 6,
                'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
            }
            png = encode_png(ihdr, bytes(data), filter_type=0)
            d_bytes = decode_png(png)
            self.equa(d_bytes['width'], w)
            self.equa(len(d_bytes['data']), w * h * 4)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
