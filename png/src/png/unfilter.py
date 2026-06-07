"""
    unfilter
    reverses the 5 png filters on decompressed (filtered) scanline bytes
"""
from png.row_bytes import get_row_bytes
from png.bpp import get_bpp
from png.paeth import paeth_predictor


def unfilter(filtered, width, height, color_type, bit_depth):
    """
        filtered
            : bytes
            : decompressed idat bytes (filter byte + row data, per row)
        width, height, color_type, bit_depth
            : int

        returns
            > bytearray
            > unfiltered image data (filter bytes stripped, predictors reversed)

        raises
            ! ValueError if length does not match expected for w/h/ct/bd
            ! ValueError on unknown filter type
    """
    row_bytes = get_row_bytes(width, color_type, bit_depth)
    bpp = get_bpp(color_type, bit_depth)

    expected = height * (1 + row_bytes)
    if len(filtered) != expected:
        raise ValueError(f'filtered length {len(filtered)} != expected {expected} for {width}x{height}')

    out = bytearray(height * row_bytes)
    prev = bytearray(row_bytes)   # previous row, starts as all zeros

    for y in range(height):
        row_start = y * (1 + row_bytes)
        ftype = filtered[row_start]
        data_start = row_start + 1

        for x in range(row_bytes):
            f = filtered[data_start + x]

            if ftype == 0:  # None
                r = f
            elif ftype == 1:  # Sub (left)
                a = out[y * row_bytes + (x - bpp)] if x >= bpp else 0
                r = (f + a) & 0xff
            elif ftype == 2:  # Up (above)
                b = prev[x]
                r = (f + b) & 0xff
            elif ftype == 3:  # Average
                a = out[y * row_bytes + (x - bpp)] if x >= bpp else 0
                b = prev[x]
                r = (f + (a + b) // 2) & 0xff
            elif ftype == 4:  # Paeth
                a = out[y * row_bytes + (x - bpp)] if x >= bpp else 0
                b = prev[x]
                c = prev[x - bpp] if x >= bpp else 0
                r = (f + paeth_predictor(a, b, c)) & 0xff
            else:
                raise ValueError(f'invalid filter type {ftype} at row {y}')

            out[y * row_bytes + x] = r

        # prepare prev for next row
        prev[:] = out[y * row_bytes : (y + 1) * row_bytes]

    return out


if __name__ == '__main__':
    print('=== unfilter demo ===')

    from filters import apply_filter

    W, H = 4, 2
    orig = bytearray((x + y * 3) * 40 % 256 for y in range(H) for x in range(W))
    print('orig:', list(orig))

    for ftype in range(5):
        filt = apply_filter(orig, W, H, 0, 8, filter_type=ftype)
        recon = unfilter(filt, W, H, 0, 8)
        assert list(recon) == list(orig), f'roundtrip failed for filter type {ftype}'
        print(f'  filter {ftype} roundtrip ok')

    # all 5 proven (paeth edges included) via apply_filter + unfilter symmetry on shared helper data
