"""
command_bar
The focusable command bar atom for the radical PNG viewer.

Responsibilities (one small job):
- Own the bottom frame + visual prompt + Entry.
- Provide activate() so the orchestrator (or : detection) can give it focus
  and clear it so the user types a *plain* command (no leading ':').
- On <Return> call a registered handler with the stripped text.
- Support yielding focus (e.g. on Esc) via a callback the orchestrator registers.

This atom knows nothing about the actual command verbs ("load", WxH, etc.).
It is deliberately tiny and self-describing so it can be understood in isolation
while still demoing perfectly with the rest of the viewer cluster.

Pure stdlib tkinter + explicit callbacks. GUI demands a tiny class here; we
keep it minimal.
"""

import tkinter as tk


class CommandBar:
    """
    A minimal command bar that lives at the bottom of a viewer.

    Typical usage from the orchestrator:

        bar = CommandBar(root)
        bar.set_command_handler(self._handle_plain_command)
        bar.set_yield_focus_callback(self.focus_canvas)

        # later, when ':' is detected while canvas has focus:
        bar.activate()          # focuses the entry, clears it
    """

    def __init__(self, parent, prompt=":"):
        self.parent = parent

        self.frame = tk.Frame(parent)
        self.label = tk.Label(self.frame, text=prompt, width=2)
        self.entry = tk.Entry(self.frame)

        self.label.pack(side="left")
        self.entry.pack(side="left", fill="x", expand=True)
        self.frame.pack(side="bottom", fill="x")

        self._command_handler = None
        self._yield_focus = None

        self.entry.bind("<Return>", self._on_return)
        self.entry.bind("<Escape>", self._on_escape)

    # ---------------- public API used by the orchestrator ----------------

    def set_command_handler(self, handler):
        """handler(text) will be called with the plain command (no leading ':')."""
        self._command_handler = handler

    def set_yield_focus_callback(self, callback):
        """callback() will be called when the user wants to leave the bar (Esc)."""
        self._yield_focus = callback

    def activate(self):
        """
        Give focus to the command bar and clear any previous text.

        This is what the ':' detection in the orchestrator calls.
        After this the user types a plain command (e.g. "load foo.png").
        """
        self.entry.focus_set()
        self.entry.delete(0, "end")

    def focus_bar(self):
        """Alias for activate (sometimes clearer in calling code)."""
        self.activate()

    # ---------------- internal ----------------

    def _on_return(self, event):
        text = self.entry.get().strip()
        self.entry.delete(0, "end")

        if self._command_handler and text:
            # We deliberately pass the text exactly as typed (no leading ':').
            self._command_handler(text)

        # After executing a command it is often nice to return to canvas mode.
        # The handler can decide; we also offer an easy yield here.
        if self._yield_focus:
            self._yield_focus()

    def _on_escape(self, event):
        if self._yield_focus:
            self._yield_focus()
        # prevent the escape from doing other default things
        return "break"


if __name__ == "__main__":
    # Tiny self-demo so the atom teaches itself.
    print("command_bar self-demo (type something and press Enter or Esc)")

    root = tk.Tk()
    root.title("command_bar atom demo")

    def handle(text):
        print(f"[command_bar demo] received plain command: {text!r}")

    def back_to_canvas():
        print("[command_bar demo] yielding focus (imagine focusing canvas now)")
        # In a real app the orchestrator would do canvas.focus_set() here.

    bar = CommandBar(root)
    bar.set_command_handler(handle)
    bar.set_yield_focus_callback(back_to_canvas)

    # Hint for the user of this tiny demo
    hint = tk.Label(root, text="Type in the bar below, Enter to 'execute', Esc to yield")
    hint.pack(pady=10)

    # Start with the bar "activated" so the demo is immediately usable
    root.after(100, bar.activate)

    root.mainloop()
    print("command_bar demo finished")