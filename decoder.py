"""
    decode_png

    orchestrates the decode atoms (sig/check/iter/ihdr/unfilter/plte + shared)
    to return dict with ihdr fields + raster "data" bytes + optional palette
"""
import io
import zlib

from signature import PNG_SIGNATURE
from row_bytes import get_row_bytes
from plte import parse_plte
from check_signature import check_signature
from iter_chunks import iter_chunks
from ihdr import parse_ihdr
from unfilter import unfilter


def decode_png(src):
    """
        src
            : str | bytes | bytearray
            : path or the raw png bytes (for custom/targeted known pngs in demos)

        returns
            > dict
            > ihdr fields + 'data' (bytes, unfiltered scanlines) + 'palette' (list or None)

        raises
            ! ValueError for bad signature / crc / missing chunks / zlib fail / ct=3 without plte
            ! NotImplementedError for adam7 interlace
    """
    if isinstance(src, (bytes, bytearray)):
        f = io.BytesIO(src)
        close_f = False
    else:
        f = open(src, 'rb')
        close_f = True
    try:
        check_signature(f)

        ihdr = None
        plte = None
        idat_list = []

        for typ, data in iter_chunks(f):
            if typ == b'IHDR':
                if ihdr is not None:
                    raise ValueError('multiple IHDR chunks')
                ihdr = parse_ihdr(data)
            elif typ == b'PLTE':
                if plte is not None:
                    raise ValueError('multiple PLTE chunks')
                plte = parse_plte(data)
            elif typ == b'IDAT':
                idat_list.append(data)
            # ancillary chunks and IEND handling are inside the lower modules

        if ihdr is None:
            raise ValueError('missing IHDR chunk')
        if not idat_list:
            raise ValueError('missing IDAT chunk(s)')

        if ihdr['interlace_method'] != 0:
            raise NotImplementedError(
                'interlace_method=1 (Adam7) is not supported in this basic decoder'
            )

        if ihdr['color_type'] == 3 and plte is None:
            raise ValueError('PLTE chunk is required for color_type 3 (indexed)')

        compressed = b''.join(idat_list)
        try:
            filtered = zlib.decompress(compressed)
        except Exception as e:
            raise ValueError(f'zlib decompression failed: {e}') from e

        raw = unfilter(
            filtered,
            ihdr['width'],
            ihdr['height'],
            ihdr['color_type'],
            ihdr['bit_depth'],
        )

        result = dict(ihdr)
        result['data'] = bytes(raw)
        result['palette'] = plte
        return result
    finally:
        if close_f:
            f.close()


if __name__ == '__main__':
    print('=== decoder demo ===')
    # TODO: compose this

