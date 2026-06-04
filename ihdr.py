"""
    parse_ihdr
    struct.unpacks the header bytes into a dict
"""
import struct


def parse_ihdr(data):
    """
        data
            : bytes
            : an IHDR chunk

        returns
            > dict
            > parsed IHDR data

        raises
            ! ValueError if length != 13
            ! ValueError if width or height is 0
            ! ValueError if compression/filter/interlace invalid
            ! ValueError if color_type or bit_depth violates PNG spec matrix
    """
    if len(data) != 13:
        raise ValueError(f'IHDR must be 13 bytes, got {len(data)}')

    w, h, bd, ct, comp, filt, interl = struct.unpack('>IIBBBBB', data)

    if w == 0 or h == 0:
        raise ValueError('width and height must be > 0')
    if comp != 0:
        raise ValueError(f'compression_method must be 0, got {comp}')
    if filt != 0:
        raise ValueError(f'filter_method must be 0, got {filt}')
    if interl not in (0, 1):
        raise ValueError(f'interlace_method must be 0 or 1, got {interl}')

    # color type + bit depth matrix (png spec)
    allowed = {
        0: (1, 2, 4, 8, 16),   # grayscale
        2: (8, 16),            # truecolor rgb
        3: (1, 2, 4, 8),       # indexed
        4: (8, 16),            # grayscale + alpha
        6: (8, 16),            # truecolor + alpha
    }

    if ct not in allowed:
        raise ValueError(f'invalid color_type {ct} (must be 0,2,3,4,6)')
    if bd not in allowed[ct]:
        raise ValueError(f'bit_depth {bd} not allowed for color_type {ct}')

    return {
        'width': w,
        'height': h,
        'bit_depth': bd,
        'color_type': ct,
        'compression_method': comp,
        'filter_method': filt,
        'interlace_method': interl,
    }


if __name__ == '__main__':
    print('=== ihdr demo ===')

    # W x H -> 200 x 100, bd, ct, comp, filt, interl
    ihdr_data = bytes.fromhex('00 00 00 c8  00 00 00 64  08  00  00  00  00')
    print('raw:', ihdr_data.hex(' ').upper())

    ihdr = parse_ihdr(ihdr_data)
    print(*(f'{k}: {v}' for k, v in ihdr.items()), sep='\n')

    grayscale = '00 00 00 01  00 00 00 01  01  00  00  00  00'
    assert parse_ihdr(bytes.fromhex(grayscale))['color_type'] == 0

    rgb = '00 00 00 01  00 00 00 01  08  02  00  00  00'
    assert parse_ihdr(bytes.fromhex(rgb))['color_type'] == 2

