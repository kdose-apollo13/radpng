"""
win_geometry
Apply window geometry commands to a tkinter toplevel.

Exports: apply_win_command, default_geometry
"""

__all__ = ['apply_win_command', 'default_geometry']

import tkinter

from png.parse_cmd import parse_win_spec

DEFAULT_W = 1300
DEFAULT_H = 800


def default_geometry():
    """> 'WxH' string for viewer startup."""
    return f'{DEFAULT_W}x{DEFAULT_H}'


def apply_win_command(root, spec):
    """
    : root tk.Tk, spec str — max | min | WxH
    > None
    ! ValueError on bad spec
    """
    kind = parse_win_spec(spec)
    if kind[0] == 'max':
        _win_max(root)
    elif kind[0] == 'min':
        root.iconify()
    else:
        _, w, h = kind
        root.geometry(f'{w}x{h}')
        root.deiconify()


def _win_max(root):
    root.deiconify()
    try:
        root.state('zoomed')
        return
    except tkinter.TclError:
        pass
    try:
        root.attributes('-zoomed', True)  # some X11 WMs
        return
    except tkinter.TclError:
        pass
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f'{sw}x{sh}+0+0')


if __name__ == '__main__':
    print(f'default_geometry -> {default_geometry()}')
    print('win_geometry atom — run viewer for live demo')