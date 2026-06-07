"""
RADICAL TEST: perf_memory
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_memory import (
    rss_sampler,
    make_rss_delta_collector,
    make_py_peak_collector,
    measure_mem,
    RSS_DELTA,
    PY_PEAK,
)


class TestPerfMemory(RadicalTestCase):
    def test_rss_sampler_non_negative(self):
        """Given the rss sampler
        When called
        Then returns an int >= 0 (best effort; 0 on platforms without resource)
        """
        val = rss_sampler()
        self.asrt(isinstance(val, int))
        self.asrt(val >= 0)

    def test_rss_delta_collector(self):
        """Given a small deterministic work func
        When using the rss delta collector (directly or via measure_mem)
        Then returns >= 0 int for the call
        """
        def work(n):
            lst = [0] * int(n)
            s = sum(lst)
            return s

        coll = make_rss_delta_collector()
        d = coll(work, 1000)
        self.asrt(isinstance(d, int) and d >= 0)

        d2 = measure_mem(work, 500, collector=RSS_DELTA)
        self.asrt(isinstance(d2, int) and d2 >= 0)

    def test_py_peak_collector(self):
        """Given work that allocates python objects
        When using the py peak collector
        Then returns >= 0 bytes (or 0 if tracemalloc path unavailable)
        """
        def work(n):
            return [i for i in range(int(n))]

        coll = make_py_peak_collector()
        p = coll(work, 2000)
        self.asrt(isinstance(p, int) and p >= 0)

        p2 = measure_mem(work, 1000, collector=PY_PEAK)
        self.asrt(isinstance(p2, int) and p2 >= 0)

    def test_measure_mem_propagates_errors(self):
        """Given a func that raises
        When measure_mem
        Then the original exception escapes (no swallowing)
        """
        def bad():
            raise ValueError('boom in mem-measured work')
        with self.rais(ValueError):
            measure_mem(bad)
        self.assert_raises_value_err('boom', measure_mem, bad)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
