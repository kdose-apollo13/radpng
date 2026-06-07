"""
    perf_scale
    high level input (subjects, sizes, variants, measurers, arg builders)
    -> list of measurement result dicts. One source for scaling experiments.
    Composes perf_timer. Pure stdlib. Thin surface.
"""
from rlab.perf_timer import time_call, WALL_TIMER, make_repeated_timer

# Re-absorbed narrow private helpers (previously over-extracted micro atoms).
# They have no independent life outside this scaling facility.

def _pixels_from_size(size):
    """Best-effort pixel count for common (w, h) or int sizes (internal to scale)."""
    if isinstance(size, (list, tuple)) and len(size) == 2:
        try:
            w, h = int(size[0]), int(size[1])
            return w * h
        except Exception:
            return None
    if isinstance(size, int):
        return size
    return None


def _name_of(obj, fallback='subject'):
    """Best-effort human name for a subject (str or __name__ or fallback). Internal."""
    if isinstance(obj, str):
        return obj
    return getattr(obj, '__name__', fallback)


def scale(
    subject,
    sizes,
    *,
    arg_builder=None,
    variants=None,
    measurers=None,
    warmup=0,
    repeats=1,
    metadata=None,
    post=None,
    mem_collectors=None,
    profiler=None,
):
    """
        subject
            : callable
            : the baseline implementation (used for 'baseline' variant if no variants given)
        sizes
            : iterable
            : size descriptors (e.g. [(w,h), ...] or [n, ...]); order defines trend order
        arg_builder
            : callable | None
            : if given: size -> (args_tuple, kwargs_dict) for the call
            : if None: the size is passed as the single positional arg
        variants
            : dict[str, callable] | None
            : name -> callable with same contract as subject; if None: {'baseline': subject}
        measurers
            : list[callable] | None
            : list of measurer(callable, *a, **k)->float ; if None a WALL (or repeated if repeats>1)
        warmup
            : int
            : number of untimed calls before each measurement (for cache etc)
        repeats
            : int
            : when measurers=None and repeats>1, auto-wraps a min-of-repeats measurer
        metadata
            : dict | None
            : arbitrary extra info copied into each result row (e.g. {'filter_type': 0})
        post
            : callable | None
            : if given: (size, variant_name, times_dict, pixels) -> None
            : called after each measurement (useful for assertions or side logging)
        mem_collectors
            : list[callable] | None
            : list of memory collectors (same shape as measurers: collector(func, *a, **k) -> value)
            : when supplied, each produces an entry under the 'mem' dict in the row
        profiler
            : object | None
            : if it has a .wrap(callable, name=...) the subject invocations for this scale
            : run will be wrapped so the profiler records them (for hotspot attribution)

        returns
            > list[dict]
            > rows in order of variants then sizes; each row has:
            >   'subject', 'variant', 'size', 'pixels', 'times': {measurer_name: seconds, ...},
            >   optionally 'mem': {collector_label: value, ...}
            >   plus any metadata

        The perf scenarios (sizes + builders) are the locked part in OPTIMIZE phase.
        Only the callables under variants= or using_impls change.
    """
    if not sizes:
        return []

    # normalize variants
    if variants is None:
        variants = {'baseline': subject}
    elif not isinstance(variants, dict) or not variants:
        raise ValueError('variants must be a non-empty dict name->callable')

    # normalize measurers (single source via perf_timer)
    if measurers is None:
        base = WALL_TIMER
        if repeats and repeats > 1:
            base = make_repeated_timer(WALL_TIMER, reps=repeats, reducer=min)
        measurers = [base]
    if not measurers:
        raise ValueError('at least one measurer required')

    # derive labels for the measurers (for report columns)
    measurer_labels = []
    for m in measurers:
        lab = getattr(m, '__name__', None) or 'measurer'
        measurer_labels.append(lab)

    subject_name = _name_of(subject)
    results = []

    for vname, vcall in variants.items():
        for sz in sizes:
            # build call arguments
            if arg_builder is not None:
                a, k = arg_builder(sz)
                if not isinstance(a, (list, tuple)):
                    a = (a,)
                k = k or {}
            else:
                a = (sz,)
                k = {}

            # warmup (untimed)
            for _ in range(max(0, int(warmup))):
                vcall(*a, **k)

            # optional: let a profiler see (and record) the top-level subject invocations
            effective_call = vcall
            if profiler is not None and hasattr(profiler, 'wrap'):
                try:
                    effective_call = profiler.wrap(vcall, name=f"{subject_name}/{vname}")
                except Exception:
                    effective_call = vcall

            # measure with every provided measurer (all shown in report)
            times = {}
            for lab, m in zip(measurer_labels, measurers):
                dt = time_call(effective_call, *a, **k, measurer=m)
                times[lab] = dt

            # memory collectors (executed similarly to measurers; may cause extra invocations
            # of the subject if the collector itself runs the callable — this is explicit and
            # consistent with "multiple injectable ways")
            mem = {}
            for coll in (mem_collectors or []):
                try:
                    label = getattr(coll, '__name__', 'mem')
                    mem[label] = coll(effective_call, *a, **k)
                except Exception:
                    # best effort; never let mem collection break a timing run
                    pass

            pix = _pixels_from_size(sz)

            row = {
                'subject': subject_name,
                'variant': vname,
                'size': sz,
                'pixels': pix,
                'times': times,
            }
            if mem:
                row['mem'] = mem
            if metadata:
                row.update(metadata)

            if post is not None:
                post(sz, vname, times, pix)

            results.append(row)

    return results


if __name__ == '__main__':
    print('=== perf_scale demo ===')

    def _demo_work(n):
        s = 0
        for i in range(int(n)):
            s = (s + (i * 17)) & 0xff
        return s

    def _demo_alt(n):
        # same (n)->int , pretend faster impl for demo
        return _demo_work(n)

    sizes = [10, 20, 40]
    variants = {'baseline': _demo_work, 'alt': _demo_alt}

    rows = scale(
        _demo_work,
        sizes,
        variants=variants,
        repeats=2,  # auto repeated measurer
        metadata={'demo': True},
    )

    assert len(rows) == 6, f'expected 2 variants x 3 sizes, got {len(rows)}'
    for r in rows:
        assert 'times' in r and r['times']
        assert r['subject'] == '_demo_work'
        assert r['pixels'] is None or isinstance(r['pixels'], int)

    print(f'  produced {len(rows)} rows')
    print(f'  first row keys: {list(rows[0].keys())}')
    print(f'  sample times: {rows[0]["times"]}')

    # Demonstrate the three pixels cases explicitly (this used to have a wrong assert expecting None for int sizes)
    # Case A: plain int size (pixels derived as the int value itself)
    def build_int(n):
        return (int(n),), {}
    rows_int = scale(_demo_work, [8, 16], arg_builder=build_int, warmup=1)
    assert rows_int[0]['pixels'] == 8
    assert rows_int[1]['pixels'] == 16

    # Case B: size shape that does not yield pixels (e.g. strings) → None
    def build_str(s):
        return (len(str(s)),), {}
    rows_none = scale(_demo_work, ["small", "larger"], arg_builder=build_str)
    assert rows_none[0]['pixels'] is None
    assert rows_none[1]['pixels'] is None

    # Case C: (w, h) tuple → pixels = w * h (product)
    def build_wh(wh):
        w, h = wh
        return (w * h,), {}  # flatten to work(n_pixels)
    rows3 = scale(_demo_work, [(4, 4), (8, 4)], arg_builder=build_wh)
    assert rows3[0]['pixels'] == 16

    print('perf_scale ok')
