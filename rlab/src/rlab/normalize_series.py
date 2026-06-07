"""
    normalize_series
    scale a list of numbers to [0,1] by max (or empty).
    one job.
"""

def normalize_series(series):
    if not series:
        return []
    m = max(series) or 1.0
    return [v / m for v in series]


if __name__ == '__main__':
    print('=== normalize_series demo ===')
    assert normalize_series([0, 50, 100]) == [0.0, 0.5, 1.0]
    assert normalize_series([]) == []
    print('normalize_series ok')
