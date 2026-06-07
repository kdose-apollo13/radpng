"""
    primary_label
    choose a preferred timer label from a times dict for ratios and complexity.
    one job, one function.
"""

def primary_label(times_dict):
    """
        times_dict
            : dict label -> seconds

        returns
            > str | None
            > first matching preferred prefix (wall, perf_counter, min, repeated) or first key
    """
    for pref in ('wall', 'perf_counter', 'min', 'repeated'):
        for k in times_dict:
            if pref in k.lower():
                return k
    return next(iter(times_dict.keys())) if times_dict else None


if __name__ == '__main__':
    print('=== primary_label demo ===')
    assert primary_label({'wall': 0.1, 'cpu': 0.05}) == 'wall'
    assert primary_label({'foo': 1, 'min_of_3': 0.9}) == 'min_of_3'
    assert primary_label({}) is None
    print('primary_label ok')
