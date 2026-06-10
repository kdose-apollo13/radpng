"""
parse_cmd
Parse plain viewer command strings (no leading colon).

Exports: parse_viewer_command
"""

__all__ = ['parse_viewer_command']


def parse_viewer_command(text):
    """
    : text str — stripped command the user typed after pressing ':'
    > dict verb + payload, or None if empty

    Verbs: load, resize, win, quit, unknown
    """
    text = text.strip()
    if not text:
        return None

    lower = text.lower()
    if lower in ('q', 'quit', 'exit'):
        return {'verb': 'quit'}

    if lower.startswith('load '):
        return {'verb': 'load', 'path': text[5:].strip()}

    if lower == 'win' or lower.startswith('win '):
        spec = text[4:].strip().lower().replace(' ', '') if lower.startswith('win ') else ''
        if not spec:
            raise ValueError('win needs max, min, or WxH')
        return {'verb': 'win', 'spec': spec}

    if 'x' in lower:
        spec = lower.replace(' ', '')
        parts = spec.split('x', 1)
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            tw, th = int(parts[0]), int(parts[1])
            if tw < 1 or th < 1:
                raise ValueError('size must be positive')
            return {'verb': 'resize', 'w': tw, 'h': th}

    return {'verb': 'unknown', 'raw': text}


def parse_win_spec(spec):
    """
    : spec str — max, min, or WxH (digits only)
    > ('max'|'min'|'size', w?, h?)
    ! ValueError on bad spec
    """
    if spec == 'max':
        return ('max',)
    if spec == 'min':
        return ('min',)
    if 'x' not in spec:
        raise ValueError('win usage: max | min | 500x300')
    left, right = spec.split('x', 1)
    if not left.isdigit() or not right.isdigit():
        raise ValueError('win usage: max | min | 500x300')
    w, h = int(left), int(right)
    if w < 1 or h < 1:
        raise ValueError('win size must be positive')
    return ('size', w, h)


if __name__ == '__main__':
    for raw in ('load foo.png', '200x100', 'win max', 'win 500x300', 'q', ''):
        try:
            print(f'  {raw!r} -> {parse_viewer_command(raw)}')
        except ValueError as e:
            print(f'  {raw!r} -> ValueError: {e}')