"""
    PngTestCase
    RadicalTestCase with PNG encode/decode roundtrip helpers
"""
from rlab.test_case import RadicalTestCase
from png.encoder import encode_png, encode_rgba
from png.decoder import decode_png, decode_rgba

# encode/decode_rgba are too generally named for their specificity
# since they bake in certain color options for a purpose


class PngTestCase(RadicalTestCase):
    """
        extends RadicalTestCase with
            assert_png_roundtrip(ihdr, data, palette=None, filter_type=0)
            assert_rgba_roundtrip(pixels, filter_type=0)
    """

    def assert_png_roundtrip(self, ihdr, data, palette=None, filter_type=0):
        """
            ihdr
                : dict
            data
                : bytes | bytearray
            palette
                : list | None
            filter_type
                : int 0-4

        raises
            ! AssertionError on roundtrip mismatch
        """
        png = encode_png(ihdr, data, palette=palette, filter_type=filter_type)
        dec = decode_png(png)
        self.equa(dec['data'], bytes(data))
        for k in ('width', 'height', 'bit_depth', 'color_type'):
            self.equa(dec[k], ihdr[k])
        if palette is not None:
            self.equa(dec.get('palette'), palette)

    def assert_rgba_roundtrip(self, pixels, filter_type=0):
        """
            pixels
                : list
                : 2d list of (r,g,b,a) tuples

        raises
            ! AssertionError on roundtrip mismatch
        """
        png = encode_rgba(pixels, filter_type=filter_type)
        back = decode_rgba(png)
        self.equa(back, pixels)


if __name__ == '__main__':
    print('=== png_test_case demo ===')
    t = PngTestCase()
    t.assert_rgba_roundtrip([[(0, 0, 0, 255)]])
    print('png_test_case ok')
