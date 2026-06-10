from png.baselines.pack import pack_row


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

