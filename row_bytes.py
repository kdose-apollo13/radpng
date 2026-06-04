"""
    get_row_bytes
    bytes per scanline (no filter byte) for given w/ct/bd
"""

def _samples_per_pixel(color_type):
    """Private helper: samples per pixel for the given color_type (dedups logic
    used by row_bytes + bpp; see SUGGESTIONS.md).
    """
    if color_type in (0, 3):      # grayscale or indexed
        return 1
    elif color_type == 2:         # truecolor rgb
        return 3
    elif color_type == 4:         # gray + alpha
        return 2
    elif color_type == 6:         # truecolor + alpha
        return 4
    else:
        raise ValueError(f'invalid color_type {color_type}')


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
    samples_per_pixel = _samples_per_pixel(color_type)
    bits_per_row = width * samples_per_pixel * bit_depth
    return (bits_per_row + 7) // 8


if __name__ == '__main__':
    print('=== row_bytes demo ===')
    assert get_row_bytes(1, 0, 8) == 1
    assert get_row_bytes(200, 0, 8) == 200
    assert get_row_bytes(1, 2, 8) == 3
    assert get_row_bytes(1, 6, 8) == 4
    print('numeric cases ok')
