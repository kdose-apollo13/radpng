"""
RADICAL TEST: perf_complexity
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_complexity import guess_complexity


class TestPerfComplexity(RadicalTestCase):
    def test_linear_series_yields_o_n_or_best_linear(self):
        """Given strictly increasing sizes with near-linear times
        When guess_complexity
        Then guess contains O(n) or best_model is O(n); exponent near 1
        """
        ns = [100, 200, 400, 800]
        ts = [1.0, 2.1, 4.0, 7.9]
        g = guess_complexity(ns, ts)
        self.isin('O(n)', g['guess'] + ' ' + g.get('best_model', ''))
        self.asrt(0.7 < g['exponent'] < 1.4)

    def test_constant_times_prefers_o_1(self):
        """Given flat times across growing n
        When guess
        Then guess O(1) or low exponent
        """
        ns = [10, 20, 40, 80]
        ts = [0.005, 0.005, 0.0048, 0.0051]
        g = guess_complexity(ns, ts)
        self.asrt(g['guess'] in ('O(1)', 'O(n)') or g['exponent'] < 0.4)

    def test_insufficient_data_is_unclear(self):
        """Given <2 points or mismatched lists
        When guess_complexity
        Then 'unclear' + note about data
        """
        g = guess_complexity([5], [0.1])
        self.equa(g['guess'], 'unclear')
        self.isin('insufficient', g['note'].lower())

        g2 = guess_complexity([1, 2], [0.1])
        self.equa(g2['guess'], 'unclear')

    def test_quadratic_tendency(self):
        """Given sizes with ~n^2 time growth
        When guess
        Then exponent high and guess O(n^2) or O(n log n)
        """
        ns = [8, 16, 32, 64]
        ts = [0.001, 0.004, 0.017, 0.068]
        g = guess_complexity(ns, ts)
        self.asrt(g['exponent'] > 1.7)
        self.asrt(g['guess'] in ('O(n^2)', 'O(n log n)'))


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
