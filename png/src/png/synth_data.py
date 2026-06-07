"""
    make_synthetic_image_data
    deterministic unfiltered scanline bytes for test matrices
"""
from png.row_bytes import get_row_bytes, _samples_per_pixel
from png.pack_bits import pack_1bit, pack_2bit, pack_4bit


def make_synthetic_image_data(width, height, color_type, bit_depth):
    """
        width, height, color_type, bit_depth
            : int

        returns
            > bytes
            > unfiltered raw scanline bytes; length == height * get_row_bytes(...)

        raises
            ! AssertionError if internal length check fails
    """
    spp = _samples_per_pixel(color_type)
    samples_per_row = width * spp
    max_sample = (1 << bit_depth) - 1 if bit_depth <= 16 else 255

    def sample_val(i):
        return (i * 37 + (i // samples_per_row) * 11) % (max_sample + 1)

    out = bytearray()
    for y in range(height):
        vals = [sample_val(y * samples_per_row + x) for x in range(samples_per_row)]
        if bit_depth == 1:
            packed = pack_1bit(vals, samples_per_row)
        elif bit_depth == 2:
            packed = pack_2bit(vals, samples_per_row)
        elif bit_depth == 4:
            packed = pack_4bit(vals, samples_per_row)
        elif bit_depth == 8:
            packed = bytes(v & 0xff for v in vals)
        else:
            ba = bytearray()
            for v in vals:
                vv = v & 0xffff
                ba.extend(((vv >> 8) & 0xff, vv & 0xff))
            packed = bytes(ba)
        out.extend(packed)

    expected = height * get_row_bytes(width, color_type, bit_depth)
    if len(out) != expected:
        raise AssertionError(f'synth data len {len(out)} != expected {expected}')
    return bytes(out)


if __name__ == '__main__':
    print('=== synth_data demo ===')
    data = make_synthetic_image_data(4, 2, 0, 8)
    assert len(data) == 8
    data16 = make_synthetic_image_data(2, 1, 6, 16)
    assert len(data16) == 16
    print('synth_data ok')
