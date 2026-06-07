"""
    make_chunk
    builds a png chunk: length(4) + type(4) + data + crc32(type+data)
"""
import struct
from zlib import crc32


def make_chunk(typ, data):
    """
        typ
            : bytes
            : exactly 4 bytes (e.g. b'IHDR', b'IDAT', b'IEND')
        data
            : bytes

        returns
            > bytes
            > full chunk ready to concatenate after signature or between chunks

        raises
            ! ValueError if len(typ) != 4
    """
    if len(typ) != 4:
        raise ValueError(f'chunk type must be 4 bytes, got {len(typ)}')

    clen = len(data)
    c = crc32(typ + data) & 0xffffffff
    return struct.pack('>I', clen) + typ + data + struct.pack('>I', c)


if __name__ == '__main__':
    print('=== make_chunk demo ===')

    # minimal ihdr data 13 bytes (w=1 h=1 etc, valid per ihdr rules)
    ihdr_data = bytes.fromhex('00 00 00 01  00 00 00 01  08  02  00  00  00')
    ch = make_chunk(b'IHDR', ihdr_data)
    print('ihdr chunk len:', len(ch), 'hex:', ch.hex())
    assert len(ch) == 4 + 4 + 13 + 4
    assert ch[4:8] == b'IHDR'

    iend = make_chunk(b'IEND', b'')
    print('iend chunk:', iend.hex())
    assert iend[:4] == b'\x00\x00\x00\x00'

    # bad type
    try:
        make_chunk(b'ABC', b'')
    except ValueError as e:
        print('bad type raised:', '4 bytes' in str(e).lower())

    print('make_chunk cases ok')
