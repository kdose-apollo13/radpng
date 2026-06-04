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
    # TODO: compose this

