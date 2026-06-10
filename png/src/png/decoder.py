"""
    decode_png
    decode_rgba

    orchestrates the decode atoms (sig/check/iter/ihdr/unfilter/plte + shared)
    to return dict (ihdr + 'data' + 'palette') or 2d list of (r, g, b, a) 4-tuples
"""
import io
import zlib

from png.signature import PNG_SIGNATURE
from png.row_bytes import get_row_bytes
from png.plte import parse_plte
from png.check_signature import check_signature
from png.iter_chunks import iter_chunks
from png.ihdr import parse_ihdr
from png.unfilter import unfilter


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

        if ihdr['color_type'] == 3 and plte is None:
            raise ValueError('PLTE chunk is required for color_type 3 (indexed)')

        compressed = b''.join(idat_list)
        try:
            filtered = zlib.decompress(compressed)
        except Exception as e:
            raise ValueError(f'zlib decompression failed: {e}') from e

        interlace = ihdr['interlace_method']
        if interlace == 0:
            raw = unfilter(
                filtered,
                ihdr['width'],
                ihdr['height'],
                ihdr['color_type'],
                ihdr['bit_depth'],
            )
        else:
            from png.interlace import extract_from_adam7_filtered
            raw = extract_from_adam7_filtered(
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


def decode_rgba(src):
    """
        src
            : str | bytes | bytearray
            : path or raw png bytes (same as decode_png)

        returns
            > list
            > pixels[y][x] = (r, g, b, a) for color_type=6 bit_depth=8 images only

        raises
            ! ValueError if the png is not ct=6 / bd=8 (plus all from decode_png)
    """
    d = decode_png(src)
    if d['color_type'] != 6 or d['bit_depth'] != 8:
        raise ValueError(
            f"decode_rgba only supports color_type=6 bit_depth=8, got ct={d['color_type']} bd={d['bit_depth']}"
        )
    w = d['width']
    h = d['height']
    data = d['data']
    rowb = w * 4
    pixels = []
    for y in range(h):
        row = []
        for x in range(w):
            i = y * rowb + x * 4
            row.append((data[i], data[i + 1], data[i + 2], data[i + 3]))
        pixels.append(row)
    return pixels


if __name__ == '__main__':
    print('=== decoder demo ===')

    from signature import PNG_SIGNATURE

    # ct0 gray8 1x1 (white-ish)
    p0 = PNG_SIGNATURE + bytes.fromhex(
        '0000000d49484452000000010000000108000000003a7e9b55'
        '0000000a49444154789c63f80f0001010100b138f6140000000049454e44ae426082'
    )
    d0 = decode_png(p0)
    assert d0['width'] == 1 and d0['height'] == 1 and d0['color_type'] == 0 and d0['bit_depth'] == 8
    assert d0['data'] == b'\xff'
    assert d0['palette'] is None
    print('ct0 ok')

    # ct2 rgb8 1x1 black
    p2 = PNG_SIGNATURE + bytes.fromhex(
        '0000000d4948445200000001000000010802000000907753de'
        '0000000c49444154789c63606060000000040001f61738550000000049454e44ae426082'
    )
    d2 = decode_png(p2)
    assert d2['color_type'] == 2
    assert d2['data'] == b'\x00\x00\x00'
    print('ct2 ok')

    # ct3 indexed8 1x1 with plte
    p3 = PNG_SIGNATURE + bytes.fromhex(
        '0000000d494844520000000100000001080300000028cb34bb'
        '00000003504c5445ff000019e209370000000a49444154789c636000000002000148afa4710000000049454e44ae426082'
    )
    d3 = decode_png(p3)
    assert d3['color_type'] == 3
    assert d3['data'] == b'\x00'
    assert d3['palette'] == [(255, 0, 0)]
    print('ct3 ok')

    # ct6 rgba8 1x1 black opaque -- use decode_rgba too
    p6 = PNG_SIGNATURE + bytes.fromhex(
        '0000000d49484452000000010000000108060000001f15c489'
        '0000000d49444154789c63606060f80f00010401005fe5c34b0000000049454e44ae426082'
    )
    d6 = decode_png(p6)
    assert d6['color_type'] == 6 and d6['bit_depth'] == 8
    assert d6['data'] == b'\x00\x00\x00\xff'
    pix = decode_rgba(p6)
    assert pix == [[(0, 0, 0, 255)]]
    print('ct6 + decode_rgba ok')

    # decode_rgba on non-rgba raises
    try:
        decode_rgba(p2)
    except ValueError as e:
        print('decode_rgba wrong ct raised:', '6' in str(e))

    print('all decoder cases ok')

