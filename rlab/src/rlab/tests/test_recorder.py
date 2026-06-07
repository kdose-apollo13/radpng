"""
RADICAL TEST: recorder
One test file per atom.
"""
import sys
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests
from rlab.recorder import Recorder
from rlab.perf_timer import WALL_TIMER


class TestRecorder(RadicalTestCase):
    def test_wrap_records_and_stats(self):
        """Given a recorder and a wrapped func
        When calling the wrapped version
        Then stats reflect calls and time
        """
        rec = Recorder(base_measurer=WALL_TIMER)
        def work(n): return sum(range(int(n)))
        w = rec.wrap(work, name='w')
        w(100)
        w(100)
        st = rec.stats()
        self.equa(st['w']['calls'], 2)
        self.asrt(st['w']['time'] >= 0)

    def test_reset_clears(self):
        rec = Recorder(base_measurer=WALL_TIMER)
        def f(): pass
        rec.wrap(f)()
        self.asrt(len(rec.stats()) > 0)
        rec.reset()
        self.equa(len(rec.stats()), 0)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
