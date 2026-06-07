"""
    fmt_ms
    format a seconds value as milliseconds with fixed width for tables.
    one job, one function.
"""

def fmt_ms(t):
    """
        t
            : float seconds

        returns
            > str
            > e.g. '   12.340' (ms, 8 chars wide)
    """
    return f"{t*1000:8.3f}"


if __name__ == '__main__':
    print('=== fmt_ms demo ===')
    assert fmt_ms(0.01234) == '  12.340'
    assert fmt_ms(0) == '   0.000'
    print('fmt_ms ok')
