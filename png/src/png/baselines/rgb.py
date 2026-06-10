from png.baselines.pack import pack_row


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
