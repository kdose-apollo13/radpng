"""
command_bar
Focusable command bar for the PNG viewer cluster.

Exports: CommandBar
"""

__all__ = ['CommandBar']

import tkinter as tk


class CommandBar:
    """
    Bottom command entry. activate() focuses and clears.
    Return runs handler(text); Esc yields via callback (orchestrator sets target).
    """

    def __init__(self, parent, prompt=':'):
        self.parent = parent

        self.frame = tk.Frame(parent, takefocus=0)
        self.label = tk.Label(self.frame, text=prompt, width=2, takefocus=0)
        self.entry = tk.Entry(self.frame, takefocus=1)

        self.label.pack(side='left')
        self.entry.pack(side='left', fill='x', expand=True)
        self.frame.pack(side='bottom', fill='x')

        self._command_handler = None
        self._yield_focus = None

        self.entry.bind('<Return>', self._on_return)

    def set_command_handler(self, handler):
        self._command_handler = handler

    def set_yield_focus_callback(self, callback):
        self._yield_focus = callback

    def activate(self):
        self.entry.focus_set()
        self.entry.delete(0, 'end')

    def focus_bar(self):
        self.activate()

    def _on_return(self, event):
        text = self.entry.get().strip()
        self.entry.delete(0, 'end')
        if self._command_handler and text:
            self._command_handler(text)
        elif self._yield_focus:
            self._yield_focus()
        return 'break'


if __name__ == '__main__':
    print('command_bar demo — Enter executes, Esc handled by focus_triad in real app')

    root = tk.Tk()
    root.title('command_bar atom demo')

    def handle(text):
        print(f'[demo] command: {text!r}')

    bar = CommandBar(root)
    bar.set_command_handler(handle)
    tk.Label(root, text='Type below; Enter runs handler').pack(pady=10)
    root.after(100, bar.activate)
    root.mainloop()