"""
    parse_plte
    turns a PLTE chunk data into list of (r,g,b)
"""


def parse_plte(data):
    """
        data
            : bytes
            : the raw data of a PLTE chunk (must be multiple of 3)

        returns
            > list
            > [(r, g, b), ...]

        raises
            ! ValueError if len(data) % 3 != 0
    """
    if len(data) % 3 != 0:
        raise ValueError('PLTE length must be multiple of 3')

    return [(data[i], data[i + 1], data[i + 2]) for i in range(0, len(data), 3)]


if __name__ == '__main__':
    print('=== plte demo ===')
    # custom known plte bytes
    plte_bytes = b'\x00\x00\x00\xff\x00\x00'  # black, red
    pal = parse_plte(plte_bytes)
    print('parsed:', pal)
    assert pal == [(0, 0, 0), (255, 0, 0)]

    try:
        parse_plte(b'\x00\x00')
    except ValueError as e:
        print('bad len raised:', 'multiple' in str(e).lower())
    print('custom plte cases ok')

