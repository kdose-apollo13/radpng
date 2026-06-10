"""
viewer
The radical PNG viewer — now a small coherent cluster of atoms that demo
beautifully together.

The three pieces (plus the pure image helpers that live here) form one
"unified semantic facility" for an interactive image viewer:

- viewer.py          (this file) — thin orchestrator, focus model, `:` detection,
                     image state, the pure helpers, and high-level command verbs.
- view_canvas.py     — the focusable display canvas + scrollbars + vim h/j/k/l
                     navigation (local to the canvas widget).
- command_bar.py     — the focusable command bar. `:` focuses it so the user can
                     type plain commands (no leading ':').

Interaction model (the main change from the monolithic version):
- Only two focusable items exist: the canvas area and the cmd bar.
- Press `:` (while the canvas has focus) → the bar is activated (focused + cleared).
  You then type a command directly:  load foo.png   or   200x100
- Commands no longer contain a leading ':'.
- Esc in the bar returns focus to the canvas.
- With the canvas focused, h/j/k/l scroll the view by ~20% of the logical image size.

Everything stays pure stdlib + the png package. The cluster as a whole is still
one self-describing, runnable demo (`python viewer.py`).

See the individual atom files for more focused documentation.
"""

import tkinter as tk
import os

from png.decoder import decode_png

# The two sibling atoms that this orchestrator wires together.
# We use absolute imports (matching the style of the rest of the png package)
# so the cluster remains runnable when "png" is on sys.path.
from png.command_bar import CommandBar
from png.view_canvas import ViewCanvas


# ---------------- pure image helpers (stay with the orchestrator for cohesion) ----------------

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
    Convert decode_png() result into list-of-rows of RGBA (0-255).
    Handles the full ct/bd/palette matrix. Lives here because it is the
    "image presentation" foundation that the rest of the viewer demo is built on.
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
                    row.append((row_bytes[i], row_bytes[i+1], row_bytes[i+2], 255))
                elif ct == 3:
                    idx = row_bytes[i]
                    if idx < len(pal):
                        r, g, b = pal[idx]
                        row.append((r, g, b, 255))
                    else:
                        row.append((0, 0, 0, 255))
                elif ct == 4:
                    g = row_bytes[i]
                    a = row_bytes[i+1]
                    row.append((g, g, g, a))
                elif ct == 6:
                    row.append((row_bytes[i], row_bytes[i+1], row_bytes[i+2], row_bytes[i+3]))
        elif bd == 16:
            for x in range(w):
                i = x * spp * 2
                if ct == 0:
                    g = norm((row_bytes[i] << 8) | row_bytes[i+1])
                    row.append((g, g, g, 255))
                elif ct == 2:
                    r = norm((row_bytes[i] << 8) | row_bytes[i+1])
                    g = norm((row_bytes[i+2] << 8) | row_bytes[i+3])
                    b = norm((row_bytes[i+4] << 8) | row_bytes[i+5])
                    row.append((r, g, b, 255))
                elif ct == 4:
                    g = norm((row_bytes[i] << 8) | row_bytes[i+1])
                    a = norm((row_bytes[i+2] << 8) | row_bytes[i+3])
                    row.append((g, g, g, a))
                elif ct == 6:
                    r = norm((row_bytes[i] << 8) | row_bytes[i+1])
                    g = norm((row_bytes[i+2] << 8) | row_bytes[i+3])
                    b = norm((row_bytes[i+4] << 8) | row_bytes[i+5])
                    a = norm((row_bytes[i+6] << 8) | row_bytes[i+7])
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
    """8x8 checker composite for alpha display (dark/light gray)."""
    checker = 200 if ((x // 8) + (y // 8)) % 2 == 0 else 160
    if a >= 255:
        return r, g, b
    cr = int(r * (a / 255) + checker * (1 - a / 255))
    cg = int(g * (a / 255) + checker * (1 - a / 255))
    cb = int(b * (a / 255) + checker * (1 - a / 255))
    return cr, cg, cb


def _rgba_to_ppm(rows):
    """In-memory P6 PPM (composite alpha on the fly)."""
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
    """Pure bilinear. Returns new list-of-rows of (r,g,b,a)."""
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
            x0 = int(sx); y0 = int(sy)
            x1 = x0 + 1;  y1 = y0 + 1
            wx1 = sx - x0; wy1 = sy - y0
            wx0 = 1.0 - wx1; wy0 = 1.0 - wy1

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


# ---------------- the thin orchestrator ----------------

class PNGViewer:
    """
    The viewer orchestrator.

    It owns:
    - the two focusable atoms (ViewCanvas + CommandBar)
    - the global focus / `:` detection / Esc model (only two focus targets)
    - the original + current display image state
    - high-level command verbs (plain text, no leading ':')
    - the pure helpers (above)

    It is deliberately small so the whole viewer cluster remains readable.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("radical png viewer — : focuses cmd bar (plain commands) | h/j/k/l on canvas")

        # Image state (original decoded data + current display size/pixels)
        self.orig_w = 0
        self.orig_h = 0
        self.orig_rgba = None
        self.disp_w = 0
        self.disp_h = 0
        self.disp_rgba = None

        # --- create the two atoms ---
        self.view_canvas = ViewCanvas(root)
        self.view_canvas.pack(fill="both", expand=True)

        self.cmd_bar = CommandBar(root)
        self.cmd_bar.set_command_handler(self._handle_plain_command)
        self.cmd_bar.set_yield_focus_callback(self._focus_canvas)

        # Wire the `:` detection (plain tkinter bind).
        # We bind on the root so it works from anywhere, but we only act
        # when the canvas currently has the interesting focus.
        self.root.bind("<Key>", self._on_global_key, add=True)

        # Helpful initial hint on the canvas (will be replaced on first load).
        # The ViewCanvas already has a default hint; we can leave it or let it
        # be replaced when set_image is called.

        self.root.update_idletasks()

    # ---------------- focus model (only two targets) ----------------

    def _focus_canvas(self):
        self.view_canvas.focus_canvas()

    def _focus_cmd_bar(self):
        self.cmd_bar.activate()

    # ---------------- `:` detection (the event system) ----------------

    def _on_global_key(self, event):
        if event.char != ":":
            return
        # Only switch if the canvas currently "has the view"
        if self.view_canvas.has_focus():
            self._focus_cmd_bar()
            return "break"   # consume the ':' so it never appears in the entry

    # ---------------- high-level command dispatch (plain text) ----------------

    def _handle_plain_command(self, text):
        """
        Commands arrive here *without* a leading ':'.
        Examples of what the user actually types after pressing `:`:
            load foo.png
            200x100
        """
        text = text.strip()
        if not text:
            self._focus_canvas()
            return

        lower = text.lower()
        if lower.startswith("load "):
            path = text[5:].strip()
            self._cmd_load(path)
        elif "x" in text:
            self._cmd_resize(text)
        else:
            print(f"[viewer] unknown command: {text}")

        # After a command we usually want to be back in "view" mode.
        self._focus_canvas()

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
        self.disp_rgba = [row[:] for row in self.orig_rgba]

        # Clamp initial viewport so huge images get scrollbars.
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
        except Exception:
            sw, sh = 1024, 768

        view_w = min(self.disp_w, max(200, sw - 100))
        view_h = min(self.disp_h, max(150, sh - 180))

        # Give the ViewCanvas a reasonable widget size on first load.
        # (The ViewCanvas will still expand if the user resizes the window.)
        self.view_canvas.get_frame().master.winfo_toplevel()  # root
        # We don't force the root size here; we just tell the canvas what
        # size we *want* for its widget on initial display.
        # The ViewCanvas itself doesn't expose a direct "set widget size",
        # so we let the normal pack/grid do its job and rely on the clamped
        # logical size + scrollregion.  For a more precise initial size the
        # orchestrator could have kept a reference to the inner canvas, but
        # we keep the surface small as per the plan.

        self._render_current_image()
        print(f"[viewer] loaded {path}  native={self.orig_w}x{self.orig_h}")

    def _cmd_resize(self, spec):
        if not self.orig_rgba:
            print("[viewer] load an image first")
            return
        spec = spec.lower().replace(" ", "")
        if "x" not in spec:
            print("[viewer] usage: 200x100")
            return
        try:
            tw, th = spec.split("x", 1)
            tw = int(tw)
            th = int(th)
        except Exception:
            print("[viewer] bad size, use 200x100")
            return
        if tw < 1 or th < 1:
            print("[viewer] size must be positive")
            return

        self.disp_w = tw
        self.disp_h = th
        self.disp_rgba = bilinear_resize_rgba(self.orig_rgba, self.orig_w, self.orig_h,
                                              self.disp_w, self.disp_h)
        self._render_current_image()
        print(f"[viewer] scaled display to {tw}x{th} (bilinear)")

    # ---------------- rendering glue ----------------

    def _render_current_image(self):
        if not self.disp_rgba:
            return
        ppm = _rgba_to_ppm(self.disp_rgba)
        photo = tk.PhotoImage(data=ppm)
        self.view_canvas.set_image(photo, self.disp_w, self.disp_h)

        # Keep a reference so the PhotoImage isn't GC'd.
        self._current_photo = photo


if __name__ == "__main__":
    print("radical png viewer (multi-atom cluster)")
    print("  press ':' while canvas focused  ->  focus command bar")
    print("  then type plain commands (no leading colon):  load foo.png   or   200x100")
    print("  Esc from bar -> back to canvas;  h/j/k/l on canvas scroll by ~20% of image")
    root = tk.Tk()
    app = PNGViewer(root)
    root.mainloop()