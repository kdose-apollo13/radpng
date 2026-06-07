"""
    pack_1bit
    pack_2bit
    pack_4bit
    test-only MSB-first bit packers for low bit-depth PNG data
"""


def pack_1bit(values, width):
    """
        values
            : list
            : 0/1 ints left-to-right
        width
            : int
            : sample count (may exceed len(values) for row padding)

        returns
            > bytes
            > MSB-first packed row bytes
    """
    rowb = (width + 7) // 8
    data = bytearray(rowb)
    for x, v in enumerate(values):
        if v:
            byte_i = x // 8
            bit = 7 - (x % 8)
            data[byte_i] |= (1 << bit)
    return bytes(data)


def pack_2bit(values, width):
    """
        values
            : list
            : 0-3 ints left-to-right
        width
            : int

        returns
            > bytes
            > 4 samples per byte, high bits first
    """
    rowb = (width + 3) // 4
    data = bytearray(rowb)
    for x, v in enumerate(values):
        byte_i = x // 4
        shift = 6 - 2 * (x % 4)
        data[byte_i] |= ((v & 3) << shift)
    return bytes(data)


def pack_4bit(values, width):
    """
        values
            : list
            : 0-15 ints left-to-right
        width
            : int

        returns
            > bytes
            > 2 samples per byte, high nibble first
    """
    rowb = (width + 1) // 2
    data = bytearray(rowb)
    for x, v in enumerate(values):
        byte_i = x // 2
        if x % 2 == 0:
            data[byte_i] |= ((v & 15) << 4)
        else:
            data[byte_i] |= (v & 15)
    return bytes(data)


if __name__ == '__main__':
    print('=== pack_bits demo ===')
    assert pack_1bit([1, 0, 1, 0, 1, 0, 1, 0], 8) == b'\xAA'
    assert pack_2bit([3, 0], 2) == b'\xC0'
    assert pack_4bit([15, 0], 2) == b'\xF0'
    print('pack_bits ok')
