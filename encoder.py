"""
    encode_png
    encode_rgba

    orchestrates the encode atoms (sig/make_chunk/filter/make_ihdr/make_plte + zlib)
    to return full png bytes; encode_rgba gives direct 2d (r,g,b,a) list -> png for ct=6/8
"""
import zlib

from signature import PNG_SIGNATURE
from row_bytes import get_row_bytes
from filters import apply_filter
from make_chunk import make_chunk
from ihdr import make_ihdr, parse_ihdr
from plte import make_plte


def encode_png(ihdr, data, palette=None, filter_type=0):
    """
        ihdr
            : dict
            : width/height/bit_depth/color_type + the three _method (validation via parse_ihdr)
        data
            : bytes
            : unfiltered scanline bytes (len must == height * row_bytes for the ct/bd).
            : For bit_depth < 8, must be pre-packed per PNG (MSB-first within bytes,
            : left-to-right pixels); for 16-bit, samples are big-endian. (See the
            : test packers or row_bytes for the exact layout; this keeps the lib thin.)
        palette
            : list or None
            : required only for color_type=3; list of (r,g,b)
        filter_type
            : int
            : 0-4 passed to apply_filter() for all rows (0 is simplest/always valid).
            : This encoder uses a *uniform* filter_type for the whole image (explicit
            : caller choice). This is intentional for radical minimality; many real
            : encoders adapt per-scanline for size.

        returns
            > bytes
            > complete png (sig + ihdr chunk + optional plte + idat + iend)

        raises
            ! ValueError for len mismatch, missing plte for ct3, bad ihdr (via parse)
            ! NotImplementedError for interlace=1
    """
    ihdr_data = make_ihdr(ihdr)
    parsed = parse_ihdr(ihdr_data)  # validates w/h>0, ct/bd matrix, methods etc

    w = parsed['width']
    h = parsed['height']
    bd = parsed['bit_depth']
    ct = parsed['color_type']

    if parsed['interlace_method'] != 0:
        raise NotImplementedError(
            'interlace_method=1 (Adam7) is not supported in this basic encoder'
        )

    if ct == 3 and palette is None:
        raise ValueError('palette required for color_type 3 (indexed)')

    rowb = get_row_bytes(w, ct, bd)
    if len(data) != h * rowb:
        raise ValueError(f'data length {len(data)} != expected {h * rowb} for {w}x{h}')

    filt = apply_filter(data, w, h, ct, bd, filter_type=filter_type)
    comp = zlib.compress(filt)

    out = bytearray(PNG_SIGNATURE)
    out += make_chunk(b'IHDR', ihdr_data)
    if palette is not None:
        out += make_chunk(b'PLTE', make_plte(palette))
    out += make_chunk(b'IDAT', comp)
    out += make_chunk(b'IEND', b'')
    return bytes(out)


def encode_rgba(pixels, filter_type=0):
    """
        pixels
            : list
            : list of lists; pixels[y][x] == (r, g, b, a) with ints 0-255; rectangular, non-empty
        filter_type
            : int 0-4 (passed through)

        returns
            > bytes
            > png bytes using color_type=6, bit_depth=8 (alpha in samples), filter chosen
    """
    if not pixels or not pixels[0]:
        raise ValueError('pixels must be non-empty')
    h = len(pixels)
    w = len(pixels[0])
    for row in pixels:
        if len(row) != w:
            raise ValueError('all rows must have same width')
    data = bytearray()
    for row in pixels:
        for p in row:
            if len(p) != 4:
                raise ValueError('each pixel must be 4-tuple (r, g, b, a)')
            data.extend((p[0] & 0xff, p[1] & 0xff, p[2] & 0xff, p[3] & 0xff))
    ihdr = {
        'width': w,
        'height': h,
        'bit_depth': 8,
        'color_type': 6,
        'compression_method': 0,
        'filter_method': 0,
        'interlace_method': 0,
    }
    return encode_png(ihdr, bytes(data), palette=None, filter_type=filter_type)


if __name__ == '__main__':
    print('=== encoder demo ===')

    # 4x2 gray8 synthetic (same expression as TestFilterUnfilter; "same as lib demos")
    W, H = 4, 2
    orig = bytearray((x + y * 3) * 40 % 256 for y in range(H) for x in range(W))
    ih = {
        'width': W, 'height': H,
        'bit_depth': 8, 'color_type': 0,
        'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
    }

    from decoder import decode_png, decode_rgba

    for ft in range(5):
        pngb = encode_png(ih, bytes(orig), filter_type=ft)
        d = decode_png(pngb)
        assert d['width'] == W and d['data'] == bytes(orig)
        print(f'  ct0 filter{ft} roundtrip ok (png len {len(pngb)})')

    # rgba small grid (2x1; paeth) via high level + decode_rgba
    pix = [[(1, 2, 3, 255), (4, 5, 6, 128)]]
    b = encode_rgba(pix, filter_type=4)
    back = decode_rgba(b)
    assert back == pix
    d = decode_png(b)
    assert d['color_type'] == 6 and d['bit_depth'] == 8
    print('rgba 2x1 (paeth) roundtrip ok (png len', len(b), ')')

    # 1x1 edge (matches decoder + test cases)
    p1 = encode_rgba([[(0, 0, 0, 255)]])
    assert decode_rgba(p1) == [[(0, 0, 0, 255)]]
    print('rgba 1x1 ok')

    # error path (style match to decoder/make_chunk/check demos)
    try:
        encode_rgba([])
    except ValueError as e:
        print('empty rgba raised:', 'non-empty' in str(e).lower())

    print('all encoder cases ok')
