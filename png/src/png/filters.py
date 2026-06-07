"""
    apply_filter
    applies the 5 png filters to raw scanline bytes, producing filter-byte-prefixed rows for zlib
"""
from png.row_bytes import get_row_bytes
from png.bpp import get_bpp
from png.paeth import paeth_predictor


def apply_filter(raw, width, height, color_type, bit_depth, filter_type=0):
    """
        raw
            : bytes | bytearray
            : unfiltered image data (scanlines concatenated, no filter bytes)
        width, height, color_type, bit_depth
            : int
        filter_type
            : int
            : 0-4 (applied uniformly to every row; 0 is always valid)

        returns
            > bytes
            > filtered bytes (height * (1 + row_bytes)), ready for zlib.compress into IDAT

        raises
            ! ValueError if length does not match expected for w/h/ct/bd
            ! ValueError if filter_type not in 0..4
    """
    row_bytes = get_row_bytes(width, color_type, bit_depth)
    bpp = get_bpp(color_type, bit_depth)

    expected = height * row_bytes
    if len(raw) != expected:
        raise ValueError(f'raw length {len(raw)} != expected {expected} for {width}x{height}')

    if filter_type not in (0, 1, 2, 3, 4):
        raise ValueError(f'filter_type must be 0-4, got {filter_type}')

    out = bytearray(height * (1 + row_bytes))
    prev = bytearray(row_bytes)  # previous raw row

    for y in range(height):
        row_start = y * (1 + row_bytes)
        out[row_start] = filter_type
        data_start = row_start + 1

        for x in range(row_bytes):
            val = raw[y * row_bytes + x]

            if filter_type == 0:  # None
                f = val
            elif filter_type == 1:  # Sub (left)
                a = raw[y * row_bytes + (x - bpp)] if x >= bpp else 0
                f = (val - a) & 0xff
            elif filter_type == 2:  # Up (above)
                b = prev[x]
                f = (val - b) & 0xff
            elif filter_type == 3:  # Average
                a = raw[y * row_bytes + (x - bpp)] if x >= bpp else 0
                b = prev[x]
                f = (val - (a + b) // 2) & 0xff
            elif filter_type == 4:  # Paeth
                a = raw[y * row_bytes + (x - bpp)] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                f = (val - paeth_predictor(a, b, c)) & 0xff

            out[data_start + x] = f

        prev[:] = raw[y * row_bytes : (y + 1) * row_bytes]

    return bytes(out)


if __name__ == '__main__':
    print('=== apply_filter demo ===')

    from unfilter import unfilter

    W, H = 4, 2
    orig = bytearray((x + y * 3) * 40 % 256 for y in range(H) for x in range(W))

    print('orig:', list(orig))

    for ftype in range(5):
        filt = apply_filter(orig, W, H, 0, 8, filter_type=ftype)
        recon = unfilter(filt, W, H, 0, 8)
        assert list(recon) == list(orig), f'roundtrip failed for filter type {ftype}'
        print(f'  filter {ftype} roundtrip ok')

    # all 5 proven (paeth edges included) with shared helper data; symmetry with unfilter exercised
