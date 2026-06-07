"""
    perf_memory
    injectable memory collectors (rss via resource on Unix, python heap via tracemalloc).
    one source, parallel to perf_timer. Pure stdlib only. One atom.
    Best-effort and platform-dependent; collectors degrade gracefully.
"""
import resource
import tracemalloc


def rss_sampler():
    """
        returns
            > int
            > current max RSS in kilobytes (platform dependent; 0 if unavailable)
    """
    try:
        ru = resource.getrusage(resource.RUSAGE_SELF)
        # ru_maxrss is in KB on Linux, bytes on some BSDs; we treat as "units" and document as KB on linux
        return int(ru.ru_maxrss)
    except Exception:
        return 0


def make_rss_delta_collector():
    """
        returns
            > callable
            > collector(func, *args, **kwargs) -> int (delta in rss units, >= 0)
    """
    def _delta(func, *args, **kwargs):
        before = rss_sampler()
        func(*args, **kwargs)
        after = rss_sampler()
        return max(0, after - before)
    _delta.__name__ = "rss_delta"
    return _delta


def make_py_peak_collector():
    """
        returns
            > callable
            > collector(func, *args, **kwargs) -> int (peak python bytes during the call)
              or 0 if tracemalloc cannot be used
    """
    def _peak(func, *args, **kwargs):
        try:
            tracemalloc.start()
            func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            return int(peak)
        except Exception:
            return 0
        finally:
            try:
                tracemalloc.stop()
            except Exception:
                pass
    _peak.__name__ = "py_peak_bytes"
    return _peak


RSS_DELTA = make_rss_delta_collector()
PY_PEAK = make_py_peak_collector()


def measure_mem(func, *args, collector=RSS_DELTA, **kwargs):
    """
        func, *args, **kwargs
            : the work to measure
        collector
            : callable(func, *a, **k) -> memory figure (e.g. RSS_DELTA or PY_PEAK)

        returns
            > int | 0
            > the memory figure returned by the collector for this call

        ! exceptions from func are propagated (no swallowing)
    """
    return collector(func, *args, **kwargs)


if __name__ == '__main__':
    print('=== perf_memory demo ===')

    def _work(n):
        # allocate a little python memory + do cpu work
        lst = [0] * int(n)
        s = 0
        for i in range(int(n)):
            s = (s + (i * 17)) & 0xff
        return s + len(lst)

    # rss delta (may be 0 or small on tiny work; still exercises the path)
    delta = measure_mem(_work, 2000, collector=RSS_DELTA)
    assert isinstance(delta, int) and delta >= 0
    print(f'  rss_delta for 2000: {delta} units')

    # py peak
    peak = measure_mem(_work, 5000, collector=PY_PEAK)
    assert isinstance(peak, int) and peak >= 0
    print(f'  py_peak_bytes for 5000: {peak}')

    # direct collector use
    d2 = RSS_DELTA(_work, 100)
    assert d2 >= 0

    # direct measure_mem
    p2 = measure_mem(_work, 100, collector=PY_PEAK)
    assert p2 >= 0

    print('perf_memory ok')
