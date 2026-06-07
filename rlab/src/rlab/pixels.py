"""
    pixels_from_size
    best-effort derivation of pixel count from common size descriptors (int or (w,h) tuple).
    one job, one function. pure stdlib.
"""

def pixels_from_size(size):
    """
        size
            : int | (w, h) tuple/list | other
            : common size descriptor used in perf scaling experiments

        returns
            > int | None
            > product for (w,h), the int itself if bare count, None otherwise
    """
    if isinstance(size, (list, tuple)) and len(size) == 2:
        try:
            w, h = int(size[0]), int(size[1])
            return w * h
        except Exception:
            return None
    if isinstance(size, int):
        return size
    return None


if __name__ == '__main__':
    print('=== pixels_from_size demo ===')
    assert pixels_from_size(42) == 42
    assert pixels_from_size((4, 2)) == 8
    assert pixels_from_size([8, 4]) == 32
    assert pixels_from_size("not a size") is None
    assert pixels_from_size((1, 2, 3)) is None
    print('pixels_from_size ok')
