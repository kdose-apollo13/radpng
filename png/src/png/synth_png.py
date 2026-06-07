"""
    make_synthetic_png
    on-demand complete PNG bytes for test size/ct/bd sweeps
"""
from png.encoder import encode_png
from png.synth_data import make_synthetic_image_data


def make_synthetic_png(width=8, height=8, color_type=0, bit_depth=8,
                       filter_type=0, palette=None):
    """
        width, height, color_type, bit_depth, filter_type
            : int
        palette
            : list | None
            : required for ct=3; auto gray ramp if None

        returns
            > bytes
            > complete PNG (sig + chunks)
    """
    ih = {
        'width': width,
        'height': height,
        'bit_depth': bit_depth,
        'color_type': color_type,
        'compression_method': 0,
        'filter_method': 0,
        'interlace_method': 0,
    }
    data = make_synthetic_image_data(width, height, color_type, bit_depth)

    if color_type == 3 and palette is None:
        n = min(1 << bit_depth, 256) or 1
        palette = [((i * 255) // max(n - 1, 1),) * 3 for i in range(n)]

    return encode_png(ih, data, palette=palette, filter_type=filter_type)


if __name__ == '__main__':
    print('=== synth_png demo ===')
    from png.decoder import decode_png
    png = make_synthetic_png(2, 2, 0, 8)
    d = decode_png(png)
    assert d['width'] == 2 and d['height'] == 2
    print('synth_png ok, len', len(png))
