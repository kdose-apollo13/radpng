"""
rgba_display
Pure image presentation helpers for the PNG viewer cluster.

Exports: decoded_to_rgba, bilinear_resize_rgba, rgba_rows_to_ppm
"""

__all__ = ['decoded_to_rgba', 'bilinear_resize_rgba', 'rgba_rows_to_ppm']


def _samples_per_pixel(ct):
    if ct in (0, 3):
        return 1
    if ct == 2:
        return 3
    if ct == 4:
        return 2
    if ct == 6:
        return 4
    raise ValueError(f"unsupported color_type {ct}")


def decoded_to_rgba(decoded):
    """
    : decoded dict from decode_png()
    > (width, height, rows) where rows is list-of-rows of RGBA 0-255
    """
    w = decoded['width']
    h = decoded['height']
    ct = decoded['color_type']
    bd = decoded['bit_depth']
    data = decoded['data']
    pal = decoded['palette'] or []

    spp = _samples_per_pixel(ct)
    rowb = (w * spp * bd + 7) // 8
    out = []
    maxv = (1 << bd) - 1

    def norm(v):
        return int(v * 255 / maxv) if maxv else 0

    for y in range(h):
        row = []
        row_bytes = data[y * rowb : (y + 1) * rowb]
        if bd == 8:
            for x in range(w):
                i = x * spp
                if ct == 0:
                    g = row_bytes[i]
                    row.append((g, g, g, 255))
                elif ct == 2:
                    row.append((row_bytes[i], row_bytes[i + 1], row_bytes[i + 2], 255))
                elif ct == 3:
                    idx = row_bytes[i]
                    if idx < len(pal):
                        r, g, b = pal[idx]
                        row.append((r, g, b, 255))
                    else:
                        row.append((0, 0, 0, 255))
                elif ct == 4:
                    g = row_bytes[i]
                    a = row_bytes[i + 1]
                    row.append((g, g, g, a))
                elif ct == 6:
                    row.append((row_bytes[i], row_bytes[i + 1],
                                row_bytes[i + 2], row_bytes[i + 3]))
        elif bd == 16:
            for x in range(w):
                i = x * spp * 2
                if ct == 0:
                    g = norm((row_bytes[i] << 8) | row_bytes[i + 1])
                    row.append((g, g, g, 255))
                elif ct == 2:
                    r = norm((row_bytes[i] << 8) | row_bytes[i + 1])
                    g = norm((row_bytes[i + 2] << 8) | row_bytes[i + 3])
                    b = norm((row_bytes[i + 4] << 8) | row_bytes[i + 5])
                    row.append((r, g, b, 255))
                elif ct == 4:
                    g = norm((row_bytes[i] << 8) | row_bytes[i + 1])
                    a = norm((row_bytes[i + 2] << 8) | row_bytes[i + 3])
                    row.append((g, g, g, a))
                elif ct == 6:
                    r = norm((row_bytes[i] << 8) | row_bytes[i + 1])
                    g = norm((row_bytes[i + 2] << 8) | row_bytes[i + 3])
                    b = norm((row_bytes[i + 4] << 8) | row_bytes[i + 5])
                    a = norm((row_bytes[i + 6] << 8) | row_bytes[i + 7])
                    row.append((r, g, b, a))
        else:
            if ct not in (0, 3):
                raise ValueError(f"bit_depth {bd} only valid for ct 0/3")
            samples_per_byte = 8 // bd
            mask = (1 << bd) - 1
            for x in range(w):
                byte_i = x // samples_per_byte
                shift = 8 - bd - (x % samples_per_byte) * bd
                val = (row_bytes[byte_i] >> shift) & mask
                if ct == 0:
                    g = norm(val)
                    row.append((g, g, g, 255))
                else:
                    if val < len(pal):
                        r, g, b = pal[val]
                        row.append((r, g, b, 255))
                    else:
                        row.append((0, 0, 0, 255))
        out.append(row)
    return w, h, out


def _composite_checker(r, g, b, a, x, y):
    checker = 200 if ((x // 8) + (y // 8)) % 2 == 0 else 160
    if a >= 255:
        return r, g, b
    cr = int(r * (a / 255) + checker * (1 - a / 255))
    cg = int(g * (a / 255) + checker * (1 - a / 255))
    cb = int(b * (a / 255) + checker * (1 - a / 255))
    return cr, cg, cb


def rgba_rows_to_ppm(rows):
    """
    : rows list-of-rows of RGBA tuples
    > bytes P6 PPM (alpha composited on 8x8 checker)
    """
    h = len(rows)
    w = len(rows[0]) if h else 0
    header = f"P6\n{w} {h}\n255\n".encode('ascii')
    body = bytearray()
    for y, row in enumerate(rows):
        for x, pix in enumerate(row):
            if len(pix) == 4:
                rr, gg, bb = _composite_checker(pix[0], pix[1], pix[2], pix[3], x, y)
            else:
                rr, gg, bb = pix[:3]
            body.extend((rr & 0xff, gg & 0xff, bb & 0xff))
    return header + body


def bilinear_resize_rgba(src_rows, src_w, src_h, dst_w, dst_h):
    """
    : src_rows, src_w, src_h, dst_w, dst_h
    > new list-of-rows of (r,g,b,a)
    """
    if dst_w <= 0 or dst_h <= 0:
        return []
    if src_w == dst_w and src_h == dst_h:
        return [row[:] for row in src_rows]

    dst = [[(0, 0, 0, 0) for _ in range(dst_w)] for _ in range(dst_h)]
    x_ratio = src_w / dst_w
    y_ratio = src_h / dst_h

    for dy in range(dst_h):
        for dx in range(dst_w):
            sx = (dx + 0.5) * x_ratio - 0.5
            sy = (dy + 0.5) * y_ratio - 0.5
            x0 = int(sx)
            y0 = int(sy)
            x1 = x0 + 1
            y1 = y0 + 1
            wx1 = sx - x0
            wy1 = sy - y0
            wx0 = 1.0 - wx1
            wy0 = 1.0 - wy1

            def get(x, y):
                xx = max(0, min(src_w - 1, x))
                yy = max(0, min(src_h - 1, y))
                return src_rows[yy][xx]

            p00, p10, p01, p11 = get(x0, y0), get(x1, y0), get(x0, y1), get(x1, y1)

            def lerp(c00, c10, c01, c11):
                return int(c00 * wx0 * wy0 + c10 * wx1 * wy0 +
                           c01 * wx0 * wy1 + c11 * wx1 * wy1)

            r = lerp(p00[0], p10[0], p01[0], p11[0])
            g = lerp(p00[1], p10[1], p01[1], p11[1])
            b = lerp(p00[2], p10[2], p01[2], p11[2])
            a = lerp(p00[3], p10[3], p01[3], p11[3])
            dst[dy][dx] = (r, g, b, a)
    return dst


if __name__ == '__main__':
    print('rgba_display atom — pure helpers, no tkinter')
    tiny = [[(255, 0, 0, 255), (0, 255, 0, 128)]]
    ppm = rgba_rows_to_ppm(tiny)
    scaled = bilinear_resize_rgba(tiny, 2, 1, 4, 2)
    print(f'  ppm bytes={len(ppm)}  scaled={len(scaled)}x{len(scaled[0])}')
