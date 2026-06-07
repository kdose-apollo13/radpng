"""
    model_error
    crude normalized L2 relative error of model vs observed (ts) after scaling to tail.
    one job (used by complexity guesser).
"""

def model_error(ns, ts, model_fn):
    """
        ns, ts
            : parallel lists of sizes and times
        model_fn
            : n -> expected

        returns
            > float (0 is perfect)
    """
    if len(ns) < 2 or len(ts) < 2:
        return 1.0
    model_last = model_fn(ns[-1]) or 1.0
    scale = (ts[-1] or 1.0) / model_last
    err = 0.0
    n = 0
    for n_i, t_i in zip(ns, ts):
        m = model_fn(n_i) * scale
        if t_i <= 0:
            continue
        rel = abs(t_i - m) / max(t_i, 1e-9)
        err += rel * rel
        n += 1
    return (err / max(n, 1)) ** 0.5


if __name__ == '__main__':
    print('=== model_error demo ===')
    def linear(n): return n
    e = model_error([1,2], [1.0, 2.1], linear)
    assert 0 <= e < 0.1
    print('model_error ok')
