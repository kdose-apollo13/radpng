"""
view_canvas
The focusable "display canvas" atom for the radical PNG viewer.

Responsibilities (one coherent job):
- Own a scrollable Canvas + its two scrollbars (grid inside a frame).
- Accept a PhotoImage + logical (possibly scaled) size via set_image().
- Handle placement of the image, scrollregion, and centering when the logical
  image is smaller than the current widget size.
- Support <Configure> so that centering is maintained when the window is resized.
- When this canvas has focus, provide vim-like navigation (h/j/k/l) that scrolls
  the view by a fraction of the *logical image* size (not the viewport page size).
- Expose a tiny surface so the orchestrator can treat it as one of the two
  focusable items: focus_canvas(), and a way to ask whether it currently "owns"
  the interesting focus.

This atom is deliberately focused on the *display + navigation* experience.
It does not know about PNG decoding, bilinear scaling, or command verbs.
It demos beautifully together with command_bar.py and the thin viewer.py
orchestrator.

Plain tkinter, explicit methods, readable top-to-bottom. GUI demands a small
class; we keep the class small.
"""

import tkinter as tk


class ViewCanvas:
    """
    A scrollable image canvas with built-in centering and vim-style navigation.

    The orchestrator typically does:

        vc = ViewCanvas(root)
        ...
        vc.set_image(photo, logical_w, logical_h)
        vc.focus_canvas()          # make it one of the two focus targets

        # on ':' detection while this has focus:
        #   (orchestrator calls command_bar.activate())

        # on Esc from the bar:
        vc.focus_canvas()
    """

    def __init__(self, parent, bg="#d0d0d0"):
        self.parent = parent
        self.bg = bg

        # The container that holds canvas + scrollbars.
        self.frame = tk.Frame(parent)

        self.canvas = tk.Canvas(self.frame, bg=bg, highlightthickness=0)
        self.vbar = tk.Scrollbar(self.frame, orient="vertical",
                                 command=self.canvas.yview)
        self.hbar = tk.Scrollbar(self.frame, orient="horizontal",
                                 command=self.canvas.xview)

        self.canvas.configure(yscrollcommand=self.vbar.set,
                              xscrollcommand=self.hbar.set)

        # Grid so scrollbars only take the space they need.
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.frame.rowconfigure(0, weight=1)
        self.frame.columnconfigure(0, weight=1)

        # Current logical (image) size for centering and vim scrolling math.
        self._logical_w = 0
        self._logical_h = 0
        self._photo = None
        self._img_item = None

        # Bind the vim keys only on *this* canvas widget.
        # They will only be active when the canvas has focus.
        self._bind_vim_keys()

        # Centering / viewport reaction.
        self.canvas.bind("<Configure>", self._on_configure)

        # A tiny startup hint (the orchestrator can replace or clear it).
        self._hint_item = self.canvas.create_text(
            20, 20, anchor="nw",
            text="Canvas focused — h/j/k/l to scroll\n"
                 "Press ':' to focus command bar (type commands without the colon)",
            fill="#555555"
        )

    # ---------------- public surface used by the orchestrator ----------------

    def pack(self, **kwargs):
        """Convenience so the orchestrator can treat the atom like a widget."""
        self.frame.pack(**kwargs)

    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

    def set_image(self, photo, logical_w, logical_h):
        """
        Replace the displayed image.

        photo       : tk.PhotoImage (already scaled by the caller via bilinear)
        logical_w/h : the size the image *logically* occupies (used for
                      scrollregion and vim fractional scrolling).
        """
        self._photo = photo
        self._logical_w = logical_w
        self._logical_h = logical_h

        if self._img_item:
            self.canvas.delete(self._img_item)
            self._img_item = None

        # Remove the initial hint once we have real content.
        if self._hint_item:
            self.canvas.delete(self._hint_item)
            self._hint_item = None

        # Place with current centering logic.
        ox, oy = self._compute_center_offset()
        self._img_item = self.canvas.create_image(ox, oy, anchor="nw",
                                                  image=self._photo)

        # The scrollable area is always the logical image size.
        self.canvas.config(scrollregion=(0, 0, logical_w, logical_h))

    def focus_canvas(self):
        """Make this the active focus target (one of the two allowed)."""
        self.canvas.focus_set()

    def has_focus(self):
        """Rough check the orchestrator can use."""
        try:
            return self.canvas.focus_get() is self.canvas
        except Exception:
            return False

    # ---------------- vim navigation (local to this widget) ----------------

    def _bind_vim_keys(self):
        # Bind only on the canvas so the keys are inert when the cmd bar has focus.
        self.canvas.bind("<Key-h>", lambda e: self._scroll_frac(-0.2, 0.0))
        self.canvas.bind("<Key-l>", lambda e: self._scroll_frac(+0.2, 0.0))
        self.canvas.bind("<Key-j>", lambda e: self._scroll_frac(0.0, +0.2))
        self.canvas.bind("<Key-k>", lambda e: self._scroll_frac(0.0, -0.2))

        # Make sure the canvas can actually receive keys.
        self.canvas.configure(takefocus=1)

    def _scroll_frac(self, dx, dy):
        """Scroll the view by a fraction of the *logical image* size."""
        if self._logical_w == 0 or self._logical_h == 0:
            return

        # Current view position as fraction of the scrollregion.
        x0, x1 = self.canvas.xview()
        y0, y1 = self.canvas.yview()

        new_x = max(0.0, min(1.0, x0 + dx))
        new_y = max(0.0, min(1.0, y0 + dy))

        self.canvas.xview_moveto(new_x)
        self.canvas.yview_moveto(new_y)

    # ---------------- centering & viewport reaction ----------------

    def _compute_center_offset(self):
        """Return (ox, oy) so the image is centered when it is smaller than the widget."""
        cw = self.canvas.winfo_width() or self._logical_w
        ch = self.canvas.winfo_height() or self._logical_h

        ox = max(0, (cw - self._logical_w) // 2)
        oy = max(0, (ch - self._logical_h) // 2)
        return ox, oy

    def _on_configure(self, event):
        """Keep the image centered when the canvas widget size changes."""
        if not self._img_item or self._logical_w == 0 or self._logical_h == 0:
            return

        # Only re-center when the logical image is smaller than the new viewport.
        cw = event.width
        ch = event.height

        if self._logical_w < cw or self._logical_h < ch:
            ox, oy = self._compute_center_offset()
            self.canvas.coords(self._img_item, ox, oy)

    # ---------------- convenience for the orchestrator ----------------

    def get_frame(self):
        """Return the container the orchestrator should pack/grid."""
        return self.frame


if __name__ == "__main__":
    # Self-demo of the atom (no real image, just the widget + vim keys + centering hint).
    print("view_canvas self-demo — click the canvas, try h/j/k/l, resize the window")

    root = tk.Tk()
    root.title("view_canvas atom demo")

    vc = ViewCanvas(root)
    vc.pack(fill="both", expand=True)

    # Give it an initial "image" size so centering and scrolling are visible.
    # We use a dummy PhotoImage of a solid color.
    dummy = tk.PhotoImage(width=300, height=200)
    # Fill it with a very light gray so the centering is obvious against the bg.
    dummy.put("{#e8e8e8}", to=(0, 0, 300, 200))

    vc.set_image(dummy, 300, 200)
    vc.focus_canvas()

    root.mainloop()
    print("view_canvas demo finished")