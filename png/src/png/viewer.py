"""
viewer
Thin orchestrator for the radical PNG viewer cluster.

Cluster atoms:
  view_canvas    — scrollable image display + vim navigation
  command_bar    — plain-text command entry
  focus_triad    — canvas / cmd / general focus model
  parse_cmd      — command string -> verb dict
  win_geometry   — window resize commands
  rgba_display   — decode -> RGBA rows -> PPM for PhotoImage

Focus: Tab cycles img <-> cmd; Esc -> general; : -> cmd from img or general.
Enter on img opens file dialog. Default window 1300x800.
Commands (no leading colon): load PATH, WxH, win max|min|WxH, q
"""

import os
import tkinter as tk
from tkinter import filedialog

from png.command_bar import CommandBar
from png.decoder import decode_png
from png.focus_triad import FocusTriad
from png.parse_cmd import parse_viewer_command
from png.rgba_display import bilinear_resize_rgba, decoded_to_rgba, rgba_rows_to_ppm
from png.view_canvas import ViewCanvas
from png.win_geometry import apply_win_command, default_geometry


class PNGViewer:
    def __init__(self, root):
        self.root = root
        self.root.title('radical png viewer')
        self.root.geometry(default_geometry())

        self.orig_w = 0
        self.orig_h = 0
        self.orig_rgba = None
        self.disp_w = 0
        self.disp_h = 0
        self.disp_rgba = None
        self._current_photo = None

        self.view_canvas = ViewCanvas(root)
        self.view_canvas.pack(fill='both', expand=True)
        self.view_canvas.set_open_file_callback(self._open_file_dialog)

        self.cmd_bar = CommandBar(root)
        self.cmd_bar.set_command_handler(self._handle_plain_command)
        self.cmd_bar.set_yield_focus_callback(self._after_command_focus)

        self.focus = FocusTriad(root, self.view_canvas.canvas, self.cmd_bar.entry)
        self.focus.set_cmd_activator(self.cmd_bar.activate)

        self.root.after(30, self.focus.focus_canvas)

    def _after_command_focus(self):
        self.focus.focus_canvas()

    def _open_file_dialog(self):
        path = filedialog.askopenfilename(
            title='Open PNG',
            filetypes=[('PNG images', '*.png'), ('All files', '*.*')],
        )
        if path:
            self._cmd_load(path)

    def _handle_plain_command(self, text):
        try:
            parsed = parse_viewer_command(text)
        except ValueError as e:
            print(f'[viewer] {e}')
            self._after_command_focus()
            return

        if parsed is None:
            self._after_command_focus()
            return

        verb = parsed['verb']
        if verb == 'load':
            self._cmd_load(parsed['path'])
        elif verb == 'resize':
            self._cmd_resize(parsed['w'], parsed['h'])
        elif verb == 'win':
            try:
                apply_win_command(self.root, parsed['spec'])
                print(f"[viewer] win {parsed['spec']}")
            except ValueError as e:
                print(f'[viewer] {e}')
        elif verb == 'quit':
            self.root.destroy()
        elif verb == 'unknown':
            print(f"[viewer] unknown command: {parsed['raw']}")

        self._after_command_focus()

    def _cmd_load(self, path):
        if not path or not os.path.exists(path):
            print(f'[viewer] file not found: {path}')
            return
        try:
            decoded = decode_png(path)
        except Exception as e:
            print(f'[viewer] decode failed: {e}')
            return

        self.orig_w, self.orig_h, self.orig_rgba = decoded_to_rgba(decoded)
        self.disp_w, self.disp_h = self.orig_w, self.orig_h
        self.disp_rgba = [row[:] for row in self.orig_rgba]
        self._render_current_image()
        print(f'[viewer] loaded {path}  native={self.orig_w}x{self.orig_h}')

    def _cmd_resize(self, tw, th):
        if not self.orig_rgba:
            print('[viewer] load an image first')
            return
        self.disp_w = tw
        self.disp_h = th
        self.disp_rgba = bilinear_resize_rgba(
            self.orig_rgba, self.orig_w, self.orig_h, tw, th,
        )
        self._render_current_image()
        print(f'[viewer] scaled display to {tw}x{th} (bilinear)')

    def _render_current_image(self):
        if not self.disp_rgba:
            return
        ppm = rgba_rows_to_ppm(self.disp_rgba)
        photo = tk.PhotoImage(data=ppm)
        self.view_canvas.set_image(photo, self.disp_w, self.disp_h)
        self._current_photo = photo


if __name__ == '__main__':
    print('radical png viewer')
    print('  Tab: img <-> cmd   Esc: general   : cmd (vim)')
    print('  Enter on img: file dialog')
    print('  commands: load PATH | WxH | win max|min|500x300 | q')
    root = tk.Tk()
    PNGViewer(root)
    root.mainloop()