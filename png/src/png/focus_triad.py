"""
focus_triad
Explicit three-mode focus for the viewer GUI cluster.

Exports: FocusTriad

Modes:
  canvas  — image area; Enter opens file picker; h/j/k/l scroll
  cmd     — command bar active, receives typed input
  general — window focused; ':' jumps to cmd (vim)

Tab cycles canvas <-> cmd only (one press each way).
Esc from any mode -> general.
"""

__all__ = ['FocusTriad']


class FocusTriad:
    """
    : root, canvas_widget, cmd_entry, on_canvas, on_cmd, on_general
    > explicit focus state machine; binds Tab/Esc/: at root
    """

    def __init__(self, root, canvas_widget, cmd_entry):
        self.root = root
        self.canvas_widget = canvas_widget
        self.cmd_entry = cmd_entry
        self.mode = 'general'
        self._activate_cmd = None
        self._on_change = None

        for widget in (root, canvas_widget, cmd_entry):
            widget.bind('<Tab>', self._on_tab)
            widget.bind('<Shift-Tab>', self._on_shift_tab)
            widget.bind('<Escape>', self._on_escape)
        root.bind('<Key>', self._on_colon, add='+')

    def set_cmd_activator(self, fn):
        """fn() focuses and clears the command entry."""
        self._activate_cmd = fn

    def set_on_change(self, fn):
        """Optional fn(mode) after each transition."""
        self._on_change = fn

    def focus_canvas(self):
        self.mode = 'canvas'
        self.canvas_widget.focus_set()
        self._notify()

    def focus_cmd(self):
        self.mode = 'cmd'
        if self._activate_cmd:
            self._activate_cmd()
        else:
            self.cmd_entry.focus_set()
        self._notify()

    def focus_general(self):
        self.mode = 'general'
        self.root.focus_set()
        self._notify()

    def is_canvas(self):
        return self.mode == 'canvas'

    def is_cmd(self):
        return self.mode == 'cmd'

    def _notify(self):
        if self._on_change:
            self._on_change(self.mode)

    def _on_tab(self, event):
        if self.mode == 'cmd':
            self.focus_canvas()
        else:
            self.focus_cmd()
        return 'break'

    def _on_shift_tab(self, event):
        if self.mode == 'canvas':
            self.focus_cmd()
        else:
            self.focus_canvas()
        return 'break'

    def _on_escape(self, event):
        self.focus_general()
        return 'break'

    def _on_colon(self, event):
        if event.char != ':':
            return
        if self.mode == 'cmd':
            return
        self.focus_cmd()
        return 'break'


if __name__ == '__main__':
    import tkinter as tk
    from png.command_bar import CommandBar
    from png.view_canvas import ViewCanvas

    print('focus_triad demo — Tab img<->cmd, Esc general, : cmd from general/img')

    root = tk.Tk()
    root.geometry('600x400')
    status = tk.Label(root, text='mode: ?', anchor='w')
    status.pack(fill='x')

    vc = ViewCanvas(root)
    vc.pack(fill='both', expand=True)
    bar = CommandBar(root)

    triad = FocusTriad(root, vc.canvas, bar.entry)
    triad.set_cmd_activator(bar.activate)
    triad.set_on_change(lambda m: status.config(text=f'mode: {m}'))

    triad.focus_canvas()
    root.mainloop()
