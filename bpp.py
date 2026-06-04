"""
    get_bpp
    bytes per pixel (filter stride) for given ct/bd
"""


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
    if color_type in (0, 3):          # gray or palette
        b = (bit_depth + 7) // 8
    elif color_type == 2:             # truecolor rgb
        b = 3 * ((bit_depth + 7) // 8)
    elif color_type == 4:             # gray+alpha
        b = 2 * ((bit_depth + 7) // 8)
    elif color_type == 6:             # truecolor + alpha
        b = 4 * ((bit_depth + 7) // 8)
    else:
        raise ValueError(f'invalid color_type {color_type}')
    return max(b, 1)


if __name__ == '__main__':
    print('=== bpp demo ===')
    assert get_bpp(0, 8) == 1
    assert get_bpp(0, 1) == 1
    assert get_bpp(2, 8) == 3
    assert get_bpp(6, 8) == 4
    assert get_bpp(2, 16) == 6
    print('numeric cases ok')

