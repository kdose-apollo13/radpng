"""
    perf_report
    turn scale() result rows into readable tables + trend + complexity guess.
    explicit formatting. consumes perf_complexity. one atom.
"""
from rlab.perf_complexity import guess_complexity

# Re-absorbed narrow private helpers (previously over-extracted).
# These are implementation details of the reporting facility.

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

        # mem (if present in any row for the group)
        has_mem = any('mem' in r for r in rows)
        mem_keys = []
        if has_mem:
            for r in rows:
                if 'mem' in r:
                    mem_keys = list(r['mem'].keys())[:3]  # first few
                    break
            for mk in mem_keys:
                header += "  " + str(mk)[:9].rjust(9)

        for lab in timer_labels:
            # slightly longer truncation for long repeated(...) names
            short = lab if len(lab) <= 12 else (lab[:9] + '...')
            header += "  " + short.rjust(12)
        header += "  ratio".rjust(8)
        lines.append(header)

        prev_t = None
        prim_label = _get_primary_label(t0) or timer_labels[0]

        for r in rows:
            sz = str(r['size'])
            pix = r.get('pixels')
            pixs = f"{pix}" if pix is not None else "-"
            line = sz.ljust(14) + pixs.rjust(8)

            # mem values (if present)
            if has_mem and mem_keys:
                m = r.get('mem') or {}
                for mk in mem_keys:
                    mv = m.get(mk, 0)
                    # show small numbers as-is, larger in 'k' units for readability
                    if isinstance(mv, (int, float)) and mv >= 10000:
                        val = f"{int(mv/1024)}k"
                    else:
                        val = str(int(mv)) if isinstance(mv, (int, float)) else str(mv)[:8]
                    line += "  " + val.rjust(9)

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

        # Hotspots section (user can attach by putting "hotspots": stats_dict on a row
        # or via the scale metadata that ends up in the row)
        first = rows[0] if rows else {}
        hot = first.get('hotspots')
        if isinstance(hot, dict) and hot:
            lines.append("Hotspots (top consumers):")
            # show a few largest by time
            sorted_hot = sorted(hot.items(), key=lambda kv: kv[1].get('time', 0), reverse=True)[:5]
            for name, s in sorted_hot:
                c = s.get('calls', 0)
                t = s.get('time', 0.0)
                lines.append(f"  {name}: calls={c} time={t*1000:.3f}ms")

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
