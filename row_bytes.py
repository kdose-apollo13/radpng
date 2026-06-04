"""
    get_row_bytes
    bytes per scanline (no filter byte) for given w/ct/bd
"""


def get_row_bytes(width, color_type, bit_depth):
    """
        width
            : int
        color_type
            : int (0/2/3/4/6)
        bit_depth
            : int

        returns
            > int
            > bytes per scanline (no filter byte)
    """
    if color_type == 0:      # grayscale
        samples_per_pixel = 1
    elif color_type == 2:    # truecolor rgb
        samples_per_pixel = 3
    elif color_type == 3:    # indexed
        samples_per_pixel = 1
    elif color_type == 4:    # gray + alpha
        samples_per_pixel = 2
    elif color_type == 6:    # truecolor + alpha
        samples_per_pixel = 4
    else:
        raise ValueError(f'invalid color_type {color_type}')

    bits_per_row = width * samples_per_pixel * bit_depth
    return (bits_per_row + 7) // 8


if __name__ == '__main__':
    print('=== row_bytes demo ===')
    assert get_row_bytes(1, 0, 8) == 1
    assert get_row_bytes(200, 0, 8) == 200
    assert get_row_bytes(1, 2, 8) == 3
    assert get_row_bytes(1, 6, 8) == 4
    print('numeric cases ok')
