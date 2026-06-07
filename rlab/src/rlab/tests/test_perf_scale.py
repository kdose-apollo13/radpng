"""
RADICAL TEST: perf_scale
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_scale import scale
from rlab.perf_timer import WALL_TIMER, make_repeated_timer


class TestPerfScale(RadicalTestCase):
    def test_scale_basic_variants_and_rows(self):
        """Given a subject + two variants + list of sizes
        When scale
        Then 2xN rows; each has subject/variant/size/times/pixels; times has entries
        """
        def work(n):
            return sum(range(int(n))) & 0xff

        def alt(n):
            return work(n)

        sizes = [5, 10, 20]
        rows = scale(work, sizes, variants={'baseline': work, 'alt': alt})
        self.equa(len(rows), 6)
        for r in rows:
            self.isin('subject', r)
            self.isin('variant', r)
            self.isin('times', r)
            self.asrt(len(r['times']) >= 1)
            self.asrt(r['pixels'] is None or isinstance(r['pixels'], int))

    def test_scale_with_arg_builder_and_pixels(self):
        """Given (w,h) sizes + arg_builder that turns them into call args
        When scale
        Then pixels computed as w*h for those sizes
        """
        def work(n):
            return (int(n) * 7) & 0xff

        def build(wh):
            w, h = wh
            return (w * h,), {}

        sizes = [(2, 4), (4, 4)]
        rows = scale(work, sizes, arg_builder=build)
        self.equa(rows[0]['pixels'], 8)
        self.equa(rows[1]['pixels'], 16)

    def test_scale_uses_injected_measurers(self):
        """Given explicit list of measurers
        When scale
        Then times dict has one key per measurer (labels from __name__)
        """
        def work(n):
            return n & 0xff

        rt = make_repeated_timer(WALL_TIMER, reps=2, reducer=min)
        rows = scale(work, [3, 5], measurers=[WALL_TIMER, rt])
        self.asrt(len(rows[0]['times']) == 2)

    def test_scale_metadata_and_post(self):
        """Given metadata + post hook
        When scale
        Then metadata merged; post called once per row with (size, vname, times, pix)
        """
        calls = []
        def post(sz, v, t, p):
            calls.append((sz, v, p))

        def work(n):
            return n

        rows = scale(work, [1, 2], metadata={'ft': 0}, post=post)
        self.equa(len(calls), 2)
        self.equa(rows[0]['ft'], 0)
        self.equa(calls[0][0], 1)

    def test_scale_repeats_auto_wraps(self):
        """Given repeats=3 and no explicit measurers
        When scale
        Then a repeated measurer is used (name contains 'repeated')
        """
        def work(n):
            return n & 0xff
        rows = scale(work, [4], repeats=3)
        tkeys = list(rows[0]['times'].keys())
        self.asrt(any('repeated' in k.lower() for k in tkeys))


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
