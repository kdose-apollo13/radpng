"""
filter method and compression method always 0

greyscale [Y, ...]
truecolor [(R, G, B), ...]
indexed-color [I, ...]
greyscale + alpha [(Y, A), ...]
truecolor + alpha [(R, G, B, A), ...]
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

def gen_grey(w, h, bd):
    max_val = (1 << bd) - 1
    data = bytearray()
    for y in range(h):
        row = []
        ny = y / (h - 1) if h > 1 else 0.5
        for x in range(w):
            nx = x / (w - 1) if w > 1 else 0.5
            val = int((nx + ny) / 2 * max_val)
            row.append(val)
        data.extend(pack_row(row, bd))
    return data


def gen_greya(w, h, bd):
    max_val = (1 << bd) - 1
    data = bytearray()
    for y in range(h):
        row = []
        ny = y / (h - 1) if h > 1 else 0.5
        for x in range(w):
            nx = x / (w - 1) if w > 1 else 0.5
            v = int(nx * max_val)
            a = int((1 - ny) * max_val) # Opaque top, transparent bottom
            row.extend([v, a])
        data.extend(pack_row(row, bd))
    return data


def gen_rgb(w, h, bd):
    max_val = (1 << bd) - 1
    data = bytearray()
    for y in range(h):
        row = []
        ny = y / (h - 1) if h > 1 else 0.5
        for x in range(w):
            nx = x / (w - 1) if w > 1 else 0.5
            r = int(nx * (1 - ny) * max_val)
            g = int((1 - nx) * ny * max_val)
            b = int(nx * ny * max_val)
            row.extend([r, g, b])
        data.extend(pack_row(row, bd))
    return data


def gen_rgba(w, h, bd):
    max_val = (1 << bd) - 1
    data = bytearray()
    for y in range(h):
        row = []
        ny = y / (h - 1) if h > 1 else 0.5
        for x in range(w):
            nx = x / (w - 1) if w > 1 else 0.5
            r = int(nx * (1 - ny) * max_val)
            g = int((1 - nx) * ny * max_val)
            b = int(nx * ny * max_val)
            a = int((0.5 + 0.5 * nx) * max_val) # 50% to 100% opaque left-to-right
            row.extend([r, g, b, a])
        data.extend(pack_row(row, bd))
    return data


def gen_indexed(w, h, bd):
    """Returns (data_bytes, palette_list)"""
    num_colors = 1 << bd
    palette = []
    # Build a simple rainbow-ish palette spanning the available size
    for i in range(num_colors):
        r = (i * 255 // (num_colors - 1)) if num_colors > 1 else 0
        g = 255 - r
        b = (128 + r // 2) % 256
        palette.append((r, g, b))
    
    data = bytearray()
    for y in range(h):
        row = []
        ny = y / (h - 1) if h > 1 else 0.5
        for x in range(w):
            nx = x / (w - 1) if w > 1 else 0.5
            idx = int((nx + ny) / 2 * (num_colors - 1))
            row.append(idx)
        data.extend(pack_row(row, bd))
    return data, palette


if __name__ == '__main__':
    # Add your imports here
    from encoder import encode_png
    from decoder import decode_png
    
    sizes = [(2, 2), (10, 10), (31, 31), (50, 50)]
    
    bit_depth_for_color_type = {
        0: [1, 2, 4, 8, 16],
        2: [8, 16],
        3: [1, 2, 4, 8],
        4: [8, 16],
        6: [8, 16]
    }
    
    generators = {
        0: gen_grey,
        2: gen_rgb,
        3: gen_indexed,
        4: gen_greya,
        6: gen_rgba
    }

    print('=== Full Matrix Test ===')
    tests_run = 0

    for (w, h) in sizes:
        for ct, depths in bit_depth_for_color_type.items():
            for bd in depths:
                for ft in [0, 1, 2, 3, 4]:
                    
                    # 1. Generate the raw data for the current configuration
                    if ct == 3:
                        data, palette = generators[ct](w, h, bd)
                    else:
                        data = generators[ct](w, h, bd)
                        palette = None
                        
                    # 2. Build the exact IHDR dict your encoder expects
                    ihdr = {
                        'width': w, 
                        'height': h,
                        'bit_depth': bd, 
                        'color_type': ct,
                        'compression_method': 0, 
                        'filter_method': 0, 
                        'interlace_method': 0
                    }
                    
                    # 3. Fire it through encode_png
                    try:
                        pngb = encode_png(ihdr, bytes(data), palette=palette, filter_type=ft)
                        
                        # 4. Optional: Pipe it back into your decoder
                        # back = decode_png(pngb)
                        # assert back['width'] == w and back['data'] == bytes(data)
                        
                        tests_run += 1
                        
                        # Optional: write out to disk to inspect the gradients visually!
                        # with open(f"test_{w}x{h}_ct{ct}_bd{bd}_ft{ft}.png", "wb") as f:
                        #     f.write(pngb)
                            
                    except Exception as e:
                        print(f"FAILED: {w}x{h} CT:{ct} BD:{bd} FT:{ft} -> {e}")

    print(f'Successfully ran {tests_run} matrix combinations.')
