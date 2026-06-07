"""
    perf_complexity
    guess algorithm complexity class from observed (size, time) series.
    pure stdlib heuristic; good enough to surface trends as dims grow.
    one atom.
"""
import math
from rlab.safe_log import safe_log as _safe_log
from rlab.normalize_series import normalize_series as _normalize
from rlab.model_error import model_error as _model_error


def guess_complexity(ns, ts):
    """
        ns
            : list[int|float]
            : sizes (pixel counts, widths, etc.) in increasing order
        ts
            : list[float]
            : corresponding times (seconds or ms); same length as ns

        returns
            > dict
            > {
            >   'guess': 'O(n)' | 'O(n log n)' | 'O(n^2)' | 'O(1)' | 'unclear',
            >   'exponent': float (empirical log-log slope from first/last),
            >   'best_model': str,
            >   'model_errors': dict,
            >   'note': str,
            > }

        tolerates
            short series, near-constant times, noise (heuristic only)
    """
    if not ns or not ts or len(ns) != len(ts) or len(ns) < 2:
        return {
            'guess': 'unclear',
            'exponent': 0.0,
            'best_model': 'unknown',
            'model_errors': {},
            'note': 'insufficient data points',
        }

    # empirical power (tail heavy for "as dimensions go up")
    n0, n1 = ns[0], ns[-1]
    t0, t1 = ts[0], ts[-1]
    if n0 > 0 and t0 > 0 and n1 > n0 and t1 > 0:
        exponent = _safe_log(t1 / t0) / _safe_log(n1 / n0)
    else:
        exponent = 0.0

    models = {
        'O(1)': lambda n: 1.0,
        'O(n)': lambda n: float(n),
        'O(n log n)': lambda n: float(n) * (_safe_log(n) if n > 1 else 1.0),
        'O(n^2)': lambda n: float(n) * float(n),
    }

    errors = {name: _model_error(ns, ts, fn) for name, fn in models.items()}
    best = min(errors, key=errors.get)

    # bucket exponent for human guess
    e = exponent
    if e < 0.3:
        guess = 'O(1)'
    elif 0.7 <= e <= 1.35:
        guess = 'O(n)'
    elif 1.35 < e <= 2.2:
        # could be n log n or light quadratic; prefer the model error winner
        guess = best if best in ('O(n log n)', 'O(n^2)') else 'O(n log n)'
    elif e > 2.2:
        guess = 'O(n^2)'
    else:
        guess = best

    note = (
        f"empirical exponent ~{e:.2f}; "
        f"2x size ~{ (2**e):.2f}x time (rough)"
    )

    return {
        'guess': guess,
        'exponent': e,
        'best_model': best,
        'model_errors': {k: round(v, 4) for k, v in errors.items()},
        'note': note,
    }


if __name__ == '__main__':
    print('=== perf_complexity demo ===')

    # synthetic linear (O(n)) data
    ns_lin = [100, 200, 400, 800, 1600]
    ts_lin = [t * 0.001 for t in [1.0, 2.05, 4.1, 7.9, 16.2]]  # ~linear with noise
    g = guess_complexity(ns_lin, ts_lin)
    print('  linear data:', g['guess'], 'exp~', round(g['exponent'], 2))
    assert 'O(n)' in g['guess'] or g['best_model'] == 'O(n)'

    # constant-ish
    ns_c = [10, 20, 40]
    ts_c = [0.005, 0.0051, 0.0049]
    g_c = guess_complexity(ns_c, ts_c)
    print('  const data :', g_c['guess'])
    assert g_c['guess'] in ('O(1)', 'O(n)')

    # quadratic-ish
    ns_q = [10, 20, 40, 80]
    ts_q = [0.001, 0.004, 0.016, 0.065]
    g_q = guess_complexity(ns_q, ts_q)
    print('  quad data  :', g_q['guess'], 'exp~', round(g_q['exponent'], 2))
    assert g_q['guess'] in ('O(n^2)', 'O(n log n)')

    print('perf_complexity ok')
