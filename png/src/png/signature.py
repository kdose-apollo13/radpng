"""
    PNG_SIGNATURE
    the 8-byte png magic
"""
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'


if __name__ == '__main__':
    print('=== signature demo ===')
    print('raw:', PNG_SIGNATURE.hex(' ').upper())
    assert PNG_SIGNATURE == bytes.fromhex('89 50 4E 47 0D 0A 1A 0A')
