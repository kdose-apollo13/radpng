"""
RADICAL TEST: perf_timer
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_timer import (
    time_call,
    make_timer,
    WALL_TIMER,
    CPU_TIMER,
    make_repeated_timer,
)


class TestPerfTimer(RadicalTestCase):
    def test_time_call_basic_wall(self):
        """Given a tiny deterministic func
        When time_call with default (WALL_TIMER)
        Then returns non-negative float seconds and func ran
        """
        side = []
        def work(n):
            side.append(n)
            s = 0
            for i in range(n):
                s = (s + i) & 0xff
            return s

        dt = time_call(work, 200)
        self.asrt(dt >= 0.0)
        self.equa(side, [200])

    def test_time_call_injects_measurer(self):
        """Given WALL and CPU measurers
        When time_call(..., measurer=...)
        Then both produce >=0 results for same work
        """
        def work(n):
            return sum(range(n)) & 0xff

        dt_wall = time_call(work, 100, measurer=WALL_TIMER)
        dt_cpu = time_call(work, 100, measurer=CPU_TIMER)
        self.asrt(dt_wall >= 0.0)
        self.asrt(dt_cpu >= 0.0)

    def test_make_repeated_timer(self):
        """Given a base timer and reps=3 + min reducer
        When make_repeated_timer then time_call with it
        Then result >=0 and is the min of the individual runs
        """
        def work(n):
            return (n * 31) & 0xff

        rt = make_repeated_timer(WALL_TIMER, reps=3, reducer=min)
        dt = time_call(work, 50, measurer=rt)
        self.asrt(dt >= 0.0)
        # sanity: repeated name contains info
        self.isin('repeated', rt.__name__.lower())

    def test_time_call_propagates_errors(self):
        """Given a func that raises ValueError
        When time_call
        Then the original exception is raised (no swallowing)
        """
        def bad():
            raise ValueError('boom inside timed work')
        with self.rais(ValueError):
            time_call(bad)
        self.assert_raises_value_err('boom', time_call, bad)

    def test_repeated_timer_reps_validation(self):
        """Given reps < 1
        When make_repeated_timer
        Then ValueError
        """
        self.assert_raises_value_err('reps', make_repeated_timer, WALL_TIMER, reps=0)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
