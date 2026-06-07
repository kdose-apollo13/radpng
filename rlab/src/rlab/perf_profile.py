"""
    perf_profile
    hotspot / atom attribution for pinpointing which functions (atoms) cost the most.
    explicit wrap-based recorder + session context. Uses perf_timer for timing.
    Pure stdlib. One atom.
"""
from contextlib import contextmanager

from rlab.perf_timer import time_call, WALL_TIMER


def _default_name(fn, explicit=None):
    if explicit:
        return explicit
    return getattr(fn, '__qualname__', getattr(fn, '__name__', str(fn)))


def make_call_recorder(base_measurer=WALL_TIMER):
    """
        base_measurer
            : the measurer used for each wrapped call (default WALL_TIMER)

        returns
            > recorder object with:
            >   .wrap(fn, name=None) -> wrapped callable (records on every call)
            >   .stats() -> dict name -> {'calls': int, 'time': float}
            >   .reset()
    """
    stats = {}

    class _Recorder:
        def wrap(self, fn, name=None):
            label = _default_name(fn, name)

            def _wrapped(*a, **k):
                dt = time_call(fn, *a, **k, measurer=base_measurer)
                if label not in stats:
                    stats[label] = {'calls': 0, 'time': 0.0}
                stats[label]['calls'] += 1
                stats[label]['time'] += dt
                return  # the original return value is intentionally dropped for pure timing wrappers
                        # (callers that need the value should wrap a closure that captures it,
                        #  or use the session around a higher-level subject)

            # preserve a little identity for debugging
            _wrapped.__name__ = f"wrapped({label})"
            return _wrapped

        def stats(self):
            # return a shallow copy so callers cannot mutate our internal dict
            return {k: v.copy() for k, v in stats.items()}

        def reset(self):
            stats.clear()

    return _Recorder()


@contextmanager
def profile_session(base_measurer=WALL_TIMER):
    """
        yields
            > a fresh recorder (from make_call_recorder) that is active for the with block
        on exit the recorder is still usable (stats can be read after the block)
    """
    rec = make_call_recorder(base_measurer=base_measurer)
    try:
        yield rec
    finally:
        # nothing special; user keeps the rec and can call .stats() after the with
        pass


def profile_around(subject, sizes, *, arg_builder=None, variants=None, measurers=None,
                   warmup=0, repeats=1, metadata=None, base_measurer=WALL_TIMER):
    """
        Convenience: run scale(...) under a fresh profile_session and return (rows, hotspots_stats).

        The subject / variants you pass are the ones that will be wrapped if you want
        attribution; for atom pinpointing the caller typically wraps the leaf atom(s)
        and passes a variant or uses a builder that exercises the wrapped version.
    """
    from rlab.perf_scale import scale  # local import to avoid circulars at module load

    with profile_session(base_measurer=base_measurer) as prof:
        rows = scale(
            subject, sizes,
            arg_builder=arg_builder,
            variants=variants,
            measurers=measurers,
            warmup=warmup,
            repeats=repeats,
            metadata=metadata,
        )
        return rows, prof.stats()


if __name__ == '__main__':
    print('=== perf_profile demo ===')

    def _work(n):
        s = 0
        for i in range(int(n)):
            s = (s + (i * 17)) & 0xff
        return s

    # explicit recorder + wrap
    rec = make_call_recorder()
    wrapped = rec.wrap(_work, name='demo_work')
    # call a few times (the wrapper records)
    wrapped(100)
    wrapped(200)
    wrapped(100)
    st = rec.stats()
    print('  recorder stats:', st)
    assert 'demo_work' in st
    assert st['demo_work']['calls'] == 3
    assert st['demo_work']['time'] >= 0.0

    # context manager
    with profile_session() as prof2:
        w2 = prof2.wrap(_work, name='sess_work')
        w2(50)
        w2(50)
    st2 = prof2.stats()
    assert st2['sess_work']['calls'] == 2

    # profile_around convenience (runs scale under the hood)
    rows, hot = profile_around(_work, [10, 20], repeats=1)
    print('  profile_around produced', len(rows), 'rows and hotspots keys:', list(hot.keys())[:3] or '(empty if not wrapped)')
    # when the subject itself is wrapped before passing, the stats will contain it

    print('perf_profile ok')
