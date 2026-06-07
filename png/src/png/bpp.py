"""
    get_bpp
    bytes per pixel (filter stride) for given ct/bd
"""

from png.row_bytes import _samples_per_pixel


def get_bpp(color_type, bit_depth):
    """
        color_type
            : int
        bit_depth
            : int

        returns
            > int
            > bytes per pixel (filter predictor distance); >= 1
    """
    spp = _samples_per_pixel(color_type)
    b = spp * ((bit_depth + 7) // 8)
    return max(b, 1)


if __name__ == '__main__':
    print('=== bpp demo ===')
    assert get_bpp(0, 8) == 1
    assert get_bpp(0, 1) == 1
    assert get_bpp(2, 8) == 3
    assert get_bpp(6, 8) == 4
    assert get_bpp(2, 16) == 6
    print('numeric cases ok')

