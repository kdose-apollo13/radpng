"""
    iter_chunks
    yields validated (type, data) after signature
"""
import io
import struct
import zlib
from zlib import crc32

from check_signature import check_signature


def iter_chunks(f):
    """
        f
            : file-like (binary)
            : positioned immediately after the 8-byte PNG signature

        yields
            > (bytes, bytes)
            > (chunk_type, chunk_data); stops after yielding IEND

        raises
            ! ValueError on truncated reads (length / type / data / crc)
            ! ValueError on CRC mismatch (format includes the chunk type)
    """
    while True:
        len_bytes = f.read(4)
        if len(len_bytes) < 4:
            raise ValueError('truncated PNG: missing chunk length')
        chunk_len = struct.unpack('>I', len_bytes)[0]

        typ = f.read(4)
        if len(typ) < 4:
            raise ValueError('truncated PNG: missing chunk type')

        data = f.read(chunk_len)
        if len(data) < chunk_len:
            raise ValueError(f'truncated PNG: short data for chunk {typ}')

        crc_bytes = f.read(4)
        if len(crc_bytes) < 4:
            raise ValueError(f'truncated PNG: missing CRC for chunk {typ}')
        crc = struct.unpack('>I', crc_bytes)[0]

        expected = crc32(typ + data) & 0xffffffff
        if crc != expected:
            raise ValueError(f'CRC mismatch for {typ!r} (got 0x{crc:08x}, expected 0x{expected:08x})')

        yield typ, data

        if typ == b'IEND':
            break


if __name__ == '__main__':
    print('=== iter_chunks demo ===')

    # use known-good minimal png (ct2 1x1) -- after sig, expect IHDR + IDAT + IEND
    from signature import PNG_SIGNATURE
    png = PNG_SIGNATURE + bytes.fromhex(
        '0000000d4948445200000001000000010802000000907753de'
        '0000000c49444154789c63606060000000040001f6173855'
        '0000000049454e44ae426082'
    )
    with io.BytesIO(png) as f:
        check_signature(f)
        chunks = list(iter_chunks(f))
        types = [t for t, d in chunks]
        print('chunks:', types)
        assert types == [b'IHDR', b'IDAT', b'IEND']
        assert len(chunks[0][1]) == 13
        assert chunks[-1][0] == b'IEND'
        print('iter_chunks on minimal png ok')

