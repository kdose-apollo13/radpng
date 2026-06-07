"""
    perf_report
    turn scale() result rows into readable tables + trend + complexity guess.
    explicit formatting. consumes perf_complexity. one atom.
"""
from rlab.perf_complexity import guess_complexity


def _fmt_ms(t):
    return f"{t*1000:8.3f}"


def _get_primary_label(times_dict):
    # prefer wall / repeated / first key
    for pref in ('wall', 'perf_counter', 'min', 'repeated'):
        for k in times_dict:
            if pref in k.lower():
                return k
    return next(iter(times_dict.keys())) if times_dict else None


def format_perf_report(results, title='perf report'):
    """
        results
            : list[dict] as returned by scale()
            : each must have 'subject','variant','size','pixels','times':{label: seconds}
        title
            : str

        returns
            > str
            > multi-line report with per-(subject,variant) table, ratios, and Complexity block
    """
    if not results:
        return f"{title}\n(no data)\n"

    lines = [f"=== {title} ==="]

    # group by (subject, variant) preserving order of first appearance
    groups = {}
    order = []
    for r in results:
        key = (r.get('subject', '?'), r.get('variant', 'baseline'))
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(r)

    for subj, vname in order:
        rows = groups[(subj, vname)]
        lines.append(f"\nsubject: {subj}")
        lines.append(f"variant:  {vname}")

        # header from the times keys of first row (all rows should have same timers)
        t0 = rows[0]['times']
        timer_labels = list(t0.keys())
        header = "size".ljust(14) + "pixels".rjust(8)
        for lab in timer_labels:
            header += "  " + lab[:10].rjust(10)
        header += "  ratio".rjust(8)
        lines.append(header)

        prev_t = None
        prim_label = _get_primary_label(t0) or timer_labels[0]

        for r in rows:
            sz = str(r['size'])
            pix = r.get('pixels')
            pixs = f"{pix}" if pix is not None else "-"
            line = sz.ljust(14) + pixs.rjust(8)
            times = r['times']
            for lab in timer_labels:
                dt = times.get(lab, 0.0)
                line += "  " + _fmt_ms(dt)
            # ratio on primary
            cur = times.get(prim_label, 0.0)
            if prev_t and prev_t > 0 and cur > 0:
                ratio = cur / prev_t
                line += f"  {ratio:6.2f}x"
            else:
                line += "       -"
            lines.append(line)
            prev_t = cur

        # complexity on the primary timer series (use pixels when present, else index)
        ns = []
        ts = []
        for r in rows:
            p = r.get('pixels')
            n = p if p is not None else len(ns) + 1
            ns.append(float(n))
            ts.append(r['times'].get(prim_label, 0.0))
        g = guess_complexity(ns, ts)
        lines.append(
            f"Complexity: {g['guess']}  (exp~{g['exponent']:.2f}, best={g['best_model']})  {g['note']}"
        )

    lines.append("")
    return "\n".join(lines)


def print_perf_report(results, title='perf report'):
    """Convenience: print(format_perf_report(...))"""
    print(format_perf_report(results, title=title))


if __name__ == '__main__':
    print('=== perf_report demo ===')

    # fabricate linear-ish scaling results (as if from scale on filter-like)
    fake = []
    for i, (sz, ms) in enumerate([
        ((8, 8), 0.12),
        ((16, 8), 0.25),
        ((16, 16), 0.49),
        ((32, 16), 0.95),
    ]):
        fake.append({
            'subject': 'apply_filter',
            'variant': 'baseline',
            'size': sz,
            'pixels': sz[0] * sz[1],
            'times': {'wall': ms / 1000.0, 'min3': (ms * 0.98) / 1000.0},
        })

    txt = format_perf_report(fake, title='demo filter scaling')
    print(txt)
    assert 'apply_filter' in txt
    assert 'Complexity' in txt
    assert 'O(n)' in txt or 'linear' in txt.lower() or 'exp~' in txt

    print('perf_report ok')
