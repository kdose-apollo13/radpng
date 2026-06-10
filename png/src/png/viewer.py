"""
viewer
A pure-stdlib Tkinter PNG viewer demo for the radical-png library
(post-apocalyptic rules: no external libs, one atomic file, descriptive,
demonstrative, every module is a demo).

Commands (typed in the bottom bar, must start with : ):

  :load path/to/file.png
      Load and display at true file size.
      Bigger than screen/viewport -> scrollbars appear.
      Smaller -> image is centered in the canvas area.

  :200x100
      Bilinear-scale the loaded image to exactly 200 px wide by 100 px high
      for display. The result stays centered when it fits, scrollable when
      it doesn't. Aspect ratio is not preserved (explicit WxH as requested).

Bilinear is used for all scaling (as required). Alpha is composited over
a simple checker pattern for display (so transparency is visible).

The viewer consumes only the public decode_png API (interlace support
is automatic). All GUI-specific code (conversion, scaling, Tk layout)
lives here in the demo, keeping the core library thin.

Run (typical):
    cd png/src/png
    PYTHONPATH=. python3 viewer.py
"""

import tkinter as tk
import os

from png.decoder import decode_png


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
    Convert decode_png() result into a simple list-of-rows of RGBA tuples (0-255).
    Handles the full ct/bd matrix + palette. This lives in the demo (GUI
    presentation code) and is intentionally descriptive.
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
                if ct == 0:      # gray
                    g = row_bytes[i]
                    row.append((g, g, g, 255))
                elif ct == 2:    # rgb
                    row.append((row_bytes[i], row_bytes[i+1], row_bytes[i+2], 255))
                elif ct == 3:    # indexed
                    idx = row_bytes[i]
                    if idx < len(pal):
                        r, g, b = pal[idx]
                        row.append((r, g, b, 255))
                    else:
                        row.append((0, 0, 0, 255))
                elif ct == 4:    # gray + a
                    g = row_bytes[i]
                    a = row_bytes[i+1]
                    row.append((g, g, g, a))
                elif ct == 6:    # rgba
                    row.append((row_bytes[i], row_bytes[i+1], row_bytes[i+2], row_bytes[i+3]))
        elif bd == 16:
            for x in range(w):
                i = x * spp * 2
                if ct == 0:
                    g = (row_bytes[i] << 8) | row_bytes[i+1]
                    g = norm(g)
                    row.append((g, g, g, 255))
                elif ct == 2:
                    r = (row_bytes[i] << 8) | row_bytes[i+1]
                    g = (row_bytes[i+2] << 8) | row_bytes[i+3]
                    b = (row_bytes[i+4] << 8) | row_bytes[i+5]
                    row.append((norm(r), norm(g), norm(b), 255))
                elif ct == 4:
                    g = (row_bytes[i] << 8) | row_bytes[i+1]
                    a = (row_bytes[i+2] << 8) | row_bytes[i+3]
                    g = norm(g); a = norm(a)
                    row.append((g, g, g, a))
                elif ct == 6:
                    r = (row_bytes[i] << 8) | row_bytes[i+1]
                    g = (row_bytes[i+2] << 8) | row_bytes[i+3]
                    b = (row_bytes[i+4] << 8) | row_bytes[i+5]
                    a = (row_bytes[i+6] << 8) | row_bytes[i+7]
                    row.append((norm(r), norm(g), norm(b), norm(a)))
        else:
            # 1/2/4 bit (only legal for ct 0 and 3)
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
    """Simple 8x8 checker composite (dark/light gray) for alpha display."""
    checker = 200 if ((x // 8) + (y // 8)) % 2 == 0 else 160
    inv = 255 - checker
    bg = checker if a == 0 else int(checker * (255 - a) / 255 + inv * a / 255) if a < 255 else 0
    # for full opaque just use the color
    if a >= 255:
        return r, g, b
    # simple over-white-ish for speed in common case
    # better checker:
    cr = int(r * (a / 255) + bg * (1 - a / 255))
    cg = int(g * (a / 255) + bg * (1 - a / 255))
    cb = int(b * (a / 255) + bg * (1 - a / 255))
    return cr, cg, cb


def _rgba_to_ppm(rows):
    """Build an in-memory P6 PPM from list-of-rows of (r,g,b,a) or (r,g,b)."""
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
    Pure-Python bilinear resize. Returns new list-of-rows of (r,g,b,a).
    Works on the original decoded data so repeated resizes stay high quality.
    """
    if dst_w <= 0 or dst_h <= 0:
        return []
    if src_w == dst_w and src_h == dst_h:
        # shallow copy of rows is enough for identity
        return [row[:] for row in src_rows]

    dst = [[(0, 0, 0, 0) for _ in range(dst_w)] for _ in range(dst_h)]

    x_ratio = src_w / dst_w
    y_ratio = src_h / dst_h

    for dy in range(dst_h):
        for dx in range(dst_w):
            # Map output pixel center to source
            sx = (dx + 0.5) * x_ratio - 0.5
            sy = (dy + 0.5) * y_ratio - 0.5

            x0 = int(sx)
            y0 = int(sy)
            x1 = x0 + 1
            y1 = y0 + 1

            # weights
            wx1 = sx - x0
            wy1 = sy - y0
            wx0 = 1.0 - wx1
            wy0 = 1.0 - wy1

            def get(x, y):
                xx = max(0, min(src_w - 1, x))
                yy = max(0, min(src_h - 1, y))
                return src_rows[yy][xx]

            p00 = get(x0, y0)
            p10 = get(x1, y0)
            p01 = get(x0, y1)
            p11 = get(x1, y1)

            def lerp(c00, c10, c01, c11):
                return int(c00 * wx0 * wy0 +
                           c10 * wx1 * wy0 +
                           c01 * wx0 * wy1 +
                           c11 * wx1 * wy1)

            r = lerp(p00[0], p10[0], p01[0], p11[0])
            g = lerp(p00[1], p10[1], p01[1], p11[1])
            b = lerp(p00[2], p10[2], p01[2], p11[2])
            a = lerp(p00[3], p10[3], p01[3], p11[3])
            dst[dy][dx] = (r, g, b, a)

    return dst


class PNGViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("radical png viewer — :load foo.png  |  :200x100")

        self.orig_w = 0
        self.orig_h = 0
        self.orig_rgba = None          # list[list[(r,g,b,a)]]
        self.disp_w = 0
        self.disp_h = 0
        self.disp_rgba = None
        self.photo = None
        self.img_item = None

        # --- display area (canvas + scrollbars) ---
        self.display_frame = tk.Frame(root)
        self.display_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.display_frame, bg="#d0d0d0",
                                highlightthickness=0)
        self.vbar = tk.Scrollbar(self.display_frame, orient="vertical",
                                 command=self.canvas.yview)
        self.hbar = tk.Scrollbar(self.display_frame, orient="horizontal",
                                 command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=self.vbar.set,
                              xscrollcommand=self.hbar.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.display_frame.rowconfigure(0, weight=1)
        self.display_frame.columnconfigure(0, weight=1)

        # --- command bar at bottom ---
        self.cmd_frame = tk.Frame(root)
        self.cmd_label = tk.Label(self.cmd_frame, text=":", width=2)
        self.cmd_entry = tk.Entry(self.cmd_frame)
        self.cmd_label.pack(side="left")
        self.cmd_entry.pack(side="left", fill="x", expand=True)
        self.cmd_frame.pack(side="bottom", fill="x")

        self.cmd_entry.bind("<Return>", self._on_return)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # helpful startup hint
        self.canvas.create_text(20, 20, anchor="nw",
                                text="Type :load path/to/image.png\n"
                                     "Then :200x100 etc. to bilinear-scale display size",
                                fill="#555555")

        self.root.update_idletasks()

    # ---------------- command handling ----------------
    def _on_return(self, event):
        text = self.cmd_entry.get().strip()
        self.cmd_entry.delete(0, "end")
        if not text or not text.startswith(":"):
            return
        cmd = text[1:].strip()
        if not cmd:
            return
        if cmd.lower().startswith("load "):
            path = cmd[5:].strip()
            self._cmd_load(path)
        elif "x" in cmd:
            self._cmd_resize(cmd)
        else:
            print(f"[viewer] unknown command: {cmd}")

    def _cmd_load(self, path):
        if not os.path.exists(path):
            print(f"[viewer] file not found: {path}")
            return
        try:
            d = decode_png(path)
        except Exception as e:
            print(f"[viewer] decode failed: {e}")
            return

        self.orig_w, self.orig_h, self.orig_rgba = decoded_to_rgba(d)
        self.disp_w, self.disp_h = self.orig_w, self.orig_h
        self.disp_rgba = [row[:] for row in self.orig_rgba]   # copy

        # initial viewport size (clamped so huge images get scrollbars)
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except Exception:
            sw, sh = 1024, 768

        view_w = min(self.disp_w, max(200, sw - 100))
        view_h = min(self.disp_h, max(150, sh - 180))

        self.canvas.config(width=view_w, height=view_h)
        self._render()

        print(f"[viewer] loaded {path}  native={self.orig_w}x{self.orig_h}")

    def _cmd_resize(self, spec):
        if not self.orig_rgba:
            print("[viewer] load an image first")
            return
        spec = spec.lower().replace(" ", "")
        if "x" not in spec:
            print("[viewer] usage: :200x100")
            return
        try:
            tw, th = spec.split("x", 1)
            tw = int(tw)
            th = int(th)
        except Exception:
            print("[viewer] bad size, use :200x100")
            return
        if tw < 1 or th < 1:
            print("[viewer] size must be positive")
            return

        self.disp_w = tw
        self.disp_h = th
        self.disp_rgba = bilinear_resize_rgba(self.orig_rgba, self.orig_w, self.orig_h,
                                              self.disp_w, self.disp_h)
        self._render()
        print(f"[viewer] scaled display to {tw}x{th} (bilinear)")

    # ---------------- rendering ----------------
    def _render(self):
        if not self.disp_rgba:
            return

        ppm = _rgba_to_ppm(self.disp_rgba)
        self.photo = tk.PhotoImage(data=ppm)

        # remove previous image (if any)
        if self.img_item:
            self.canvas.delete(self.img_item)
            self.img_item = None

        # compute centering offset (only when the logical image is smaller than canvas)
        cw = self.canvas.winfo_width() or self.disp_w
        ch = self.canvas.winfo_height() or self.disp_h

        ox = max(0, (cw - self.disp_w) // 2)
        oy = max(0, (ch - self.disp_h) // 2)

        self.img_item = self.canvas.create_image(ox, oy, anchor="nw", image=self.photo)

        # scrollregion is always the logical (possibly scaled) image size
        self.canvas.config(scrollregion=(0, 0, self.disp_w, self.disp_h))

    def _on_canvas_configure(self, event):
        # Re-center when the canvas widget size changes and the current
        # display image is smaller than the new viewport.
        if not self.img_item or not self.disp_rgba:
            return
        cw = event.width
        ch = event.height
        if self.disp_w < cw or self.disp_h < ch:
            ox = max(0, (cw - self.disp_w) // 2)
            oy = max(0, (ch - self.disp_h) // 2)
            self.canvas.coords(self.img_item, ox, oy)


if __name__ == "__main__":
    print("radical png viewer")
    print("  :load path.png")
    print("  :200x100   (bilinear display scale)")
    root = tk.Tk()
    app = PNGViewer(root)
    root.mainloop()