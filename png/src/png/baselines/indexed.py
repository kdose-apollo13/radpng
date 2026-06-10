from png.baselines.pack import pack_row


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
