"""
    parse_plte
    make_plte
    turns a PLTE chunk data into/from list of (r, g, b)
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


def make_plte(palette):
    """
        palette
            : list
            : [(r, g, b), ...] or equivalent; 1 to 256 entries

        returns
            > bytes
            > concatenated rgb bytes for the PLTE chunk data

        raises
            ! ValueError if len not in 1..256 or any entry not 3 values
    """
    if not (1 <= len(palette) <= 256):
        raise ValueError('PLTE must have 1..256 entries')

    data = bytearray()
    for p in palette:
        if len(p) != 3:
            raise ValueError('each PLTE entry must be (r, g, b)')
        data.extend((int(p[0]) & 0xff, int(p[1]) & 0xff, int(p[2]) & 0xff))
    return bytes(data)


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

    # make + parse roundtrip + error cases
    pal = [(0, 0, 0), (255, 0, 0), (0, 255, 0)]
    data = make_plte(pal)
    assert parse_plte(data) == pal
    assert len(data) == 9

    try:
        make_plte([])
    except ValueError as e:
        print('make bad len raised:', '1..256' in str(e).lower())

    try:
        make_plte([(1, 2)])
    except ValueError as e:
        print('make bad entry raised:', 'entry' in str(e).lower())

    print('custom plte cases ok')

