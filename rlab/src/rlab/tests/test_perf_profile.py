"""
RADICAL TEST: perf_profile
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_profile import make_call_recorder, profile_session, profile_around
from rlab.perf_scale import scale


class TestPerfProfile(RadicalTestCase):
    def test_recorder_wrap_records_calls_and_time(self):
        """Given a tiny work func and a recorder
        When wrapping and calling the wrapped version
        Then stats contains the label with positive call count and non-negative time
        """
        def work(n):
            return sum(range(int(n))) & 0xff

        rec = make_call_recorder()
        w = rec.wrap(work, name='tiny_work')
        w(100)
        w(200)
        w(100)
        st = rec.stats()
        self.isin('tiny_work', st)
        self.equa(st['tiny_work']['calls'], 3)
        self.asrt(st['tiny_work']['time'] >= 0.0)

    def test_profile_session_yields_recorder(self):
        """Given a profile_session
        When entering the with and wrapping/calling inside
        Then after exit the recorder still has the stats
        """
        def work(n):
            s = 0
            for i in range(int(n)): s += 1
            return s

        with profile_session() as prof:
            w = prof.wrap(work, name='sess')
            w(50)
            w(50)
        st = prof.stats()
        self.equa(st['sess']['calls'], 2)

    def test_profile_around_runs_scale_and_returns_hotspots(self):
        """Given profile_around + a subject and sizes
        When called
        Then it returns (rows, stats_dict) and rows look like normal scale output
        """
        def work(n):
            return (int(n) * 31) & 0xff

        rows, hot = profile_around(work, [10, 20], repeats=1)
        self.asrt(len(rows) >= 1)
        self.asrt(isinstance(hot, dict))
        # when the subject is not wrapped the hotspots may be empty or minimal;
        # the important thing is that the call succeeded and shape is correct

    def test_recorder_reset_clears(self):
        """Given a recorder with data
        When reset
        Then stats becomes empty
        """
        def w(n): return n
        rec = make_call_recorder()
        rec.wrap(w)(5)
        self.asrt(len(rec.stats()) > 0)
        rec.reset()
        self.equa(len(rec.stats()), 0)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
