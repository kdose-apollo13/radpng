from png.baselines.baseline import pack_row


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

