"""
    interlace
    Adam7 7-pass geometry, progressive <-> interlaced raw data transforms,
    and the filtered IDAT payload builders used by encoder/decoder.

One atom per facility. GWT tests in test_interlace.py.
Pure stdlib only.
"""

from png.row_bytes import get_row_bytes


# Adam7 pass table (x_start, y_start, x_step, y_step) for passes 1..7 in order.
# Used for both geometry queries and the gather/place transform.
PASS_SPECS = [
    (0, 0, 8, 8),  # pass 1
    (4, 0, 8, 8),  # pass 2
    (0, 4, 4, 8),  # pass 3
    (2, 0, 4, 4),  # pass 4
    (0, 2, 2, 4),  # pass 5
    (1, 0, 2, 2),  # pass 6
    (0, 1, 1, 2),  # pass 7
]


def _samples_per_pixel(color_type):
    """Local copy of the small helper (same rules as row_bytes / bpp)."""
    if color_type in (0, 3):
        return 1
    elif color_type == 2:
        return 3
    elif color_type == 4:
        return 2
    elif color_type == 6:
        return 4
    else:
        raise ValueError(f'invalid color_type {color_type}')


def compute_pass_dimensions(width, height, x_start, y_start, x_step, y_step):
    """
        width, height
            : int
            : full image dimensions
        x_start, y_start, x_step, y_step
            : int
            : one entry from PASS_SPECS

        returns
            > (pw, ph)
            > reduced width and height for this pass (0 for a dimension if the
              start offset is beyond the image size)
    """
    if width <= x_start or height <= y_start:
        return 0, 0
    pw = (width - x_start + x_step - 1) // x_step
    ph = (height - y_start + y_step - 1) // y_step
    return max(pw, 0), max(ph, 0)


def get_adam7_pass_dimensions(width, height):
    """
        width, height
            : int
            : full progressive image size

        returns
            > list of (pw, ph)
            > one pair per Adam7 pass in order (some may be 0x0)
    """
    return [compute_pass_dimensions(width, height, xs, ys, xstep, ystep)
            for (xs, ys, xstep, ystep) in PASS_SPECS]


def _unpack_row_to_samples(row_data, n_samples, bit_depth):
    """
        row_data
            : bytes | bytearray
            : exactly one PNG scanline's packed bytes (no filter byte)
        n_samples, bit_depth
            : int
            : total number of channel samples in this row (pixels * spp)

        returns
            > list of int
            > the sample values (0..(2**bd-1)) for 'n_samples' samples in this row,
              in left-to-right order. Matches the layout produced by
              baselines/pack.pack_row and expected by encode_png 'data'.
    """
    if bit_depth == 8:
        return list(row_data[:n_samples])
    if bit_depth == 16:
        out = []
        for i in range(0, n_samples * 2, 2):
            out.append((row_data[i] << 8) | row_data[i + 1])
        return out

    # Sub-byte (1, 2 or 4). Samples are MSB-first within each byte.
    # For sub-byte, spp is always 1, therefore n_samples == pixel count for the row.
    out = []
    samples_per_byte = 8 // bit_depth
    mask = (1 << bit_depth) - 1
    for i in range(n_samples):
        byte_i = i // samples_per_byte
        shift = 8 - bit_depth - (i % samples_per_byte) * bit_depth
        val = (row_data[byte_i] >> shift) & mask
        out.append(val)
    return out


def _pack_samples_to_row(samples, bit_depth):
    """
        samples
            : list of int
            : the sample values for one pass row
        bit_depth
            : int

        returns
            > bytes
            > exactly the packed PNG row bytes (no filter byte) for these samples.
              Must be bit-identical to what baselines/pack.pack_row would emit.
    """
    if bit_depth == 8:
        return bytearray(samples)
    if bit_depth == 16:
        res = bytearray()
        for s in samples:
            res.extend([(s >> 8) & 0xff, s & 0xff])
        return res

    # Sub-byte packing, MSB first within bytes (identical to pack_row).
    res = bytearray()
    ppb = 8 // bit_depth
    mask = (1 << bit_depth) - 1
    for i in range(0, len(samples), ppb):
        chunk = samples[i:i + ppb]
        b = 0
        for j, s in enumerate(chunk):
            b |= (s & mask) << (8 - bit_depth - j * bit_depth)
        res.append(b)
    return res


def get_pass_raw(full_raw, full_w, full_h, color_type, bit_depth,
                 x_start, y_start, x_step, y_step):
    """
        full_raw
            : bytes | bytearray
            : the full progressive (non-interlaced) unfiltered scanline bytes
        full_w, full_h, color_type, bit_depth
            : int
        x_start, y_start, x_step, y_step
            : int
            : Adam7 pass offsets/steps

        returns
            > bytes
            > the packed raw bytes for the reduced pass image (ph * pass_row_bytes).
              Length 0 when the pass is empty for the given dimensions.
    """
    pw, ph = compute_pass_dimensions(full_w, full_h, x_start, y_start, x_step, y_step)
    if pw == 0 or ph == 0:
        return b''

    spp = _samples_per_pixel(color_type)
    full_rowb = get_row_bytes(full_w, color_type, bit_depth)
    pass_rowb = get_row_bytes(pw, color_type, bit_depth)

    out = bytearray(ph * pass_rowb)

    for py in range(ph):
        fy = y_start + py * y_step
        full_row = full_raw[fy * full_rowb : (fy + 1) * full_rowb]
        full_samples = _unpack_row_to_samples(full_row, full_w * spp, bit_depth)

        # Collect the spp samples belonging to each pass pixel in this row.
        pass_samples = []
        for px in range(pw):
            fx = x_start + px * x_step
            base = fx * spp
            pass_samples.extend(full_samples[base:base + spp])

        packed = _pack_samples_to_row(pass_samples, bit_depth)
        out[py * pass_rowb : (py + 1) * pass_rowb] = packed

    return bytes(out)


def place_pass_raw(full_buffer, pass_raw, full_w, full_h, color_type, bit_depth,
                   x_start, y_start, x_step, y_step):
    """
        full_buffer
            : bytearray (mutable)
            : the target full progressive raw buffer (already sized)
        pass_raw
            : bytes | bytearray
            : packed raw bytes for one pass (from unfilter on the pass slice)
        (other args identical to get_pass_raw)

        Mutates full_buffer in place by scattering the pass samples at the
        Adam7 locations. No return value.
    """
    pw, ph = compute_pass_dimensions(full_w, full_h, x_start, y_start, x_step, y_step)
    if pw == 0 or ph == 0:
        return

    spp = _samples_per_pixel(color_type)
    full_rowb = get_row_bytes(full_w, color_type, bit_depth)
    pass_rowb = get_row_bytes(pw, color_type, bit_depth)

    for py in range(ph):
        fy = y_start + py * y_step
        pass_row = pass_raw[py * pass_rowb : (py + 1) * pass_rowb]
        pass_samples = _unpack_row_to_samples(pass_row, pw * spp, bit_depth)

        # Write the samples back into the full row's sample list then repack the row.
        full_row = bytearray(full_buffer[fy * full_rowb : (fy + 1) * full_rowb])
        full_samples = _unpack_row_to_samples(full_row, full_w * spp, bit_depth)

        for px in range(pw):
            fx = x_start + px * x_step
            base = fx * spp
            for s in range(spp):
                full_samples[base + s] = pass_samples[px * spp + s]

        packed = _pack_samples_to_row(full_samples, bit_depth)
        full_buffer[fy * full_rowb : (fy + 1) * full_rowb] = packed


def build_adam7_filtered(full_raw, width, height, color_type, bit_depth,
                         filter_type=0):
    """
        full_raw
            : bytes | bytearray
            : full progressive unfiltered data (len == h * row_bytes(full_w))
        width, height, color_type, bit_depth, filter_type
            : as for apply_filter

        returns
            > bytes
            > the exact concatenated filtered bytes that belong in the zlib
              stream for an Adam7-interlaced IDAT (7 passes in order).
    """
    from png.filters import apply_filter

    out = bytearray()
    for (xs, ys, xstep, ystep) in PASS_SPECS:
        pw, ph = compute_pass_dimensions(width, height, xs, ys, xstep, ystep)
        if pw == 0 or ph == 0:
            continue
        p_raw = get_pass_raw(full_raw, width, height, color_type, bit_depth,
                             xs, ys, xstep, ystep)
        p_filt = apply_filter(p_raw, pw, ph, color_type, bit_depth,
                              filter_type=filter_type)
        out.extend(p_filt)
    return bytes(out)


def extract_from_adam7_filtered(filt_concat, width, height, color_type, bit_depth):
    """
        filt_concat
            : bytes
            : the decompressed IDAT payload for an Adam7 image (concat of the
              7 filtered pass blocks)
        (other args as usual)

        returns
            > bytearray
            > the full progressive unfiltered raw data (ready for the 'data'
              field returned by decode_png).
    """
    from png.unfilter import unfilter

    full_rowb = get_row_bytes(width, color_type, bit_depth)
    full_raw = bytearray(height * full_rowb)

    offset = 0
    for (xs, ys, xstep, ystep) in PASS_SPECS:
        pw, ph = compute_pass_dimensions(width, height, xs, ys, xstep, ystep)
        if pw == 0 or ph == 0:
            continue
        pass_rowb = get_row_bytes(pw, color_type, bit_depth)
        pass_filt_len = ph * (1 + pass_rowb)
        pass_filt = filt_concat[offset:offset + pass_filt_len]
        offset += pass_filt_len

        pass_raw = unfilter(pass_filt, pw, ph, color_type, bit_depth)
        place_pass_raw(full_raw, pass_raw, width, height, color_type, bit_depth,
                       xs, ys, xstep, ystep)

    return full_raw


if __name__ == '__main__':
    print('=== interlace (Adam7) demo ===')

    # Geometry for a representative size that exercises all passes
    w, h = 8, 8
    dims = get_adam7_pass_dimensions(w, h)
    print('8x8 pass dims (pw,ph):', dims)
    assert dims[0] == (1, 1)
    assert dims[6] == (4, 4)

    # Tiny image (only first pass has content)
    dims1 = get_adam7_pass_dimensions(1, 1)
    print('1x1 pass dims:', dims1)
    assert dims1[0] == (1, 1)
    assert dims1[1] == (0, 0)

    # Roundtrip a small ct6 pattern through gather + place (no filter yet)
    from png.baselines import gen_rgba
    data = gen_rgba(4, 4, 8)   # 4*4*4 = 64 bytes
    # For demo we treat the generated bytes as the "full_raw"
    # Extract pass 7 (the last, densest) and place it back; the other passes
    # would be zero for this tiny grid in some locations, but we just sanity
    # a full gather-all + place-all.
    buf = bytearray(len(data))
    # Simulate a full 7-pass round (we don't have the filtered concat here,
    # so we just prove the raw transform is an identity on the progressive data).
    for spec in PASS_SPECS:
        xs, ys, xstep, ystep = spec
        p = get_pass_raw(data, 4, 4, 6, 8, xs, ys, xstep, ystep)
        place_pass_raw(buf, p, 4, 4, 6, 8, xs, ys, xstep, ystep)
    assert bytes(buf) == bytes(data), 'raw gather/place identity failed'
    print('ct6 4x4 raw gather/place identity: ok')

    # Now the real thing: build filtered payload for interlace + extract back
    # (uses apply/unfilter under the hood)
    filt = build_adam7_filtered(data, 4, 4, 6, 8, filter_type=0)
    recon = extract_from_adam7_filtered(filt, 4, 4, 6, 8)
    assert bytes(recon) == bytes(data), 'adam7 filtered roundtrip failed'
    print('ct6 4x4 build_adam7_filtered <-> extract roundtrip: ok')

    # Quick interlace via the public encode/decode (will be wired in encoder/decoder)
    from encoder import encode_png
    from decoder import decode_png
    ih = {
        'width': 4, 'height': 4,
        'bit_depth': 8, 'color_type': 6,
        'compression_method': 0, 'filter_method': 0, 'interlace_method': 1,
    }
    pngb = encode_png(ih, bytes(data), filter_type=0)
    d = decode_png(pngb)
    assert d['interlace_method'] == 1
    assert d['data'] == bytes(data)
    print('public encode_png(interlace=1) + decode_png roundtrip: ok')

    print('interlace demo complete')