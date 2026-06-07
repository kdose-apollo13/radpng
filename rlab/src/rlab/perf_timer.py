"""
    perf_timer
    single source for all measurements; multiple strategies (wall, cpu, repeated min etc);
    fully injectable; pure stdlib. One atom.
"""
import time


def make_timer(timestamp_fn=time.perf_counter):
    """
        timestamp_fn
            : callable
            : 0-arg that returns a float "now" (e.g. time.perf_counter, time.process_time)

        returns
            > callable
            > measurer(func, *args, **kwargs) -> float (elapsed seconds for one call)
    """
    def _measurer(func, *args, **kwargs):
        t0 = timestamp_fn()
        func(*args, **kwargs)
        t1 = timestamp_fn()
        return t1 - t0
    _measurer.__name__ = f"timer({getattr(timestamp_fn, '__name__', str(timestamp_fn))})"
    return _measurer


WALL_TIMER = make_timer(time.perf_counter)
CPU_TIMER = make_timer(time.process_time)


def make_repeated_timer(base_timer=WALL_TIMER, reps=3, reducer=min):
    """
        base_timer
            : callable(func, *a, **k) -> float
            : the single-shot measurer to repeat
        reps
            : int
            : >= 1
        reducer
            : callable(list[float]) -> float
            : e.g. min, max, statistics.mean

        returns
            > callable
            > measurer that runs base_timer reps times and reduces the deltas
    """
    if reps < 1:
        raise ValueError('reps must be >= 1')

    def _repeated(func, *args, **kwargs):
        deltas = [base_timer(func, *args, **kwargs) for _ in range(reps)]
        return reducer(deltas)

    name = getattr(base_timer, '__name__', 'base')
    _repeated.__name__ = f"repeated({name}, reps={reps}, reducer={getattr(reducer, '__name__', str(reducer))})"
    return _repeated


def time_call(func, *args, measurer=WALL_TIMER, **kwargs):
    """
        func
            : callable
        *args, **kwargs
            : passed through to func
        measurer
            : callable(func, *a, **k) -> float seconds
            : default WALL_TIMER (perf_counter single shot)
            : inject any (CPU_TIMER, repeated, custom, ...)

        returns
            > float
            > seconds elapsed under the measurer

        ! ValueError or whatever func raises is propagated (no swallowing)
    """
    return measurer(func, *args, **kwargs)


if __name__ == '__main__':
    print('=== perf_timer demo ===')

    def _work(n):
        # small deterministic work
        s = 0
        for i in range(n):
            s += (i * 37) & 0xff
        return s

    # basic wall
    dt = time_call(_work, 1000)
    assert dt >= 0.0, 'time must be non-negative'
    print(f'  time_call (wall, 1000): {dt*1000:.3f} ms')

    # cpu timer
    dt_cpu = time_call(_work, 500, measurer=CPU_TIMER)
    assert dt_cpu >= 0.0
    print(f'  time_call (cpu, 500):  {dt_cpu*1000:.3f} ms')

    # repeated min
    min3 = make_repeated_timer(WALL_TIMER, reps=3, reducer=min)
    dt_min = time_call(_work, 2000, measurer=min3)
    assert dt_min >= 0.0
    print(f'  time_call (min-of-3):  {dt_min*1000:.3f} ms')

    # direct measurer use
    dt2 = WALL_TIMER(_work, 100)
    assert dt2 >= 0.0

    # error propagation (no catch)
    def _bad():
        raise ValueError('boom in timed func')
    try:
        time_call(_bad)
    except ValueError as e:
        assert 'boom' in str(e).lower()

    print('perf_timer ok')
