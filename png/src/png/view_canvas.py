"""
view_canvas
Focusable scrollable image canvas for the PNG viewer cluster.

Exports: ViewCanvas
"""

__all__ = ['ViewCanvas']

import tkinter as tk


class ViewCanvas:
    """
    Scrollable canvas with centering and vim-style h/j/k/l navigation.
    Enter (when focused) calls the registered open-file callback.
    """

    def __init__(self, parent, bg='#d0d0d0'):
        self.parent = parent
        self.bg = bg
        self._open_file = None

        self.frame = tk.Frame(parent, takefocus=0)
        self.canvas = tk.Canvas(self.frame, bg=bg, highlightthickness=0, takefocus=1)
        self.vbar = tk.Scrollbar(self.frame, orient='vertical',
                                 command=self.canvas.yview, takefocus=0)
        self.hbar = tk.Scrollbar(self.frame, orient='horizontal',
                                 command=self.canvas.xview, takefocus=0)

        self.canvas.configure(yscrollcommand=self.vbar.set,
                              xscrollcommand=self.hbar.set)

        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.vbar.grid(row=0, column=1, sticky='ns')
        self.hbar.grid(row=1, column=0, sticky='ew')
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        self._logical_w = 0
        self._logical_h = 0
        self._photo = None
        self._img_item = None

        self._bind_vim_keys()
        self.canvas.bind('<Configure>', self._on_configure)
        self.canvas.bind('<Return>', self._on_return)

        self._hint_item = self.canvas.create_text(
            20, 20, anchor='nw',
            text='Image focus — Enter: open file | Tab: cmd bar | : cmd | h/j/k/l scroll',
            fill='#555555',
        )

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def set_open_file_callback(self, callback):
        """callback() -> path str or None"""
        self._open_file = callback

    def set_image(self, photo, logical_w, logical_h):
        """
        : photo PhotoImage, logical_w/h int display size for scroll + vim math
        """
        self._photo = photo
        self._logical_w = logical_w
        self._logical_h = logical_h

        if self._img_item:
            self.canvas.delete(self._img_item)
            self._img_item = None
        if self._hint_item:
            self.canvas.delete(self._hint_item)
            self._hint_item = None

        ox, oy = self._compute_center_offset()
        self._img_item = self.canvas.create_image(ox, oy, anchor='nw', image=self._photo)
        self.canvas.config(scrollregion=(0, 0, logical_w, logical_h))

    def focus_canvas(self):
        self.canvas.focus_set()

    def has_focus(self):
        try:
            return self.canvas.focus_get() is self.canvas
        except Exception:
            return False

    def get_frame(self):
        return self.frame

    def _on_return(self, event):
        if self._open_file:
            self._open_file()
        return 'break'

    def _bind_vim_keys(self):
        self.canvas.bind('<Key-h>', lambda e: self._scroll_frac(-0.2, 0.0))
        self.canvas.bind('<Key-l>', lambda e: self._scroll_frac(+0.2, 0.0))
        self.canvas.bind('<Key-j>', lambda e: self._scroll_frac(0.0, +0.2))
        self.canvas.bind('<Key-k>', lambda e: self._scroll_frac(0.0, -0.2))

    def _scroll_frac(self, dx, dy):
        if self._logical_w == 0 or self._logical_h == 0:
            return
        x0, _ = self.canvas.xview()
        y0, _ = self.canvas.yview()
        self.canvas.xview_moveto(max(0.0, min(1.0, x0 + dx)))
        self.canvas.yview_moveto(max(0.0, min(1.0, y0 + dy)))

    def _compute_center_offset(self):
        cw = self.canvas.winfo_width() or self._logical_w
        ch = self.canvas.winfo_height() or self._logical_h
        ox = max(0, (cw - self._logical_w) // 2)
        oy = max(0, (ch - self._logical_h) // 2)
        return ox, oy

    def _on_configure(self, event):
        if not self._img_item or self._logical_w == 0 or self._logical_h == 0:
            return
        cw, ch = event.width, event.height
        if self._logical_w < cw or self._logical_h < ch:
            ox, oy = self._compute_center_offset()
            self.canvas.coords(self._img_item, ox, oy)


if __name__ == '__main__':
    print('view_canvas demo — h/j/k/l scroll, Enter logs open-file')

    root = tk.Tk()
    root.title('view_canvas atom demo')
    vc = ViewCanvas(root)
    vc.pack(fill='both', expand=True)
    vc.set_open_file_callback(lambda: print('[demo] open file dialog would run'))

    dummy = tk.PhotoImage(width=300, height=200)
    dummy.put('{#e8e8e8}', to=(0, 0, 300, 200))
    vc.set_image(dummy, 300, 200)
    vc.focus_canvas()
    root.mainloop()