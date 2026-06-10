"""
    pack_row
    pack a flat list of integer samples into exact PNG scanline bytes for a given bit depth.
    This is the layout rule used by the synthetic baseline generators (and any code
    that must produce "unfiltered image data" bytes matching what encode_png expects).
    One small atom. Pure stdlib.
"""


def pack_row(samples, bd):
    """Packs a list of raw integer samples into PNG-compliant scanline bytes."""
    if bd == 8:
        return bytearray(samples)
    
    if bd == 16:
        res = bytearray()
        for s in samples:
            res.extend([(s >> 8) & 0xff, s & 0xff])
        return res
    
    # Sub-byte packing (bd in [1, 2, 4])
    res = bytearray()
    ppb = 8 // bd  # pixels per byte
    mask = (1 << bd) - 1
    
    for i in range(0, len(samples), ppb):
        chunk = samples[i:i+ppb]
        b = 0
        for j, s in enumerate(chunk):
            # Shift the value into the correct position (MSB first)
            b |= (s & mask) << (8 - bd - j*bd)
        res.append(b)
        
    return res


if __name__ == '__main__':
    print('=== pack_row demo ===')
    # 8-bit: identity
    assert pack_row([10, 20, 30], 8) == bytearray([10, 20, 30])
    # 16-bit big-endian per sample
    assert pack_row([0x0102], 16) == bytearray([0x01, 0x02])
    # 1-bit (MSB first within each byte)
    b1 = pack_row([1, 0, 1, 0, 1, 0, 1, 0], 1)
    assert b1[0] == 0b10101010
    # 2-bit
    b2 = pack_row([0, 1, 2, 3], 2)
    assert b2[0] == (0 << 6) | (1 << 4) | (2 << 2) | 3
    print('pack_row basic cases ok')
