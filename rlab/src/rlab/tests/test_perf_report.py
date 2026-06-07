"""
RADICAL TEST: perf_report
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_report import format_perf_report


class TestPerfReport(RadicalTestCase):
    def test_format_includes_subject_variant_and_complexity(self):
        """Given sample scale() rows for one subject/variant with growing sizes
        When format_perf_report
        Then output contains subject, variant, table header-ish, and Complexity line
        """
        rows = [
            {'subject': 'enc', 'variant': 'base', 'size': (4, 2), 'pixels': 8,
             'times': {'wall': 0.001, 'min': 0.0009}},
            {'subject': 'enc', 'variant': 'base', 'size': (8, 2), 'pixels': 16,
             'times': {'wall': 0.002, 'min': 0.0018}},
        ]
        txt = format_perf_report(rows, title='t')
        self.isin('subject: enc', txt)
        self.isin('variant:  base', txt)
        self.isin('Complexity:', txt)
        self.isin('wall', txt.lower() or 'min' in txt.lower())

    def test_empty_results(self):
        """Given no rows
        When format
        Then produces a (no data) report
        """
        txt = format_perf_report([])
        self.isin('no data', txt.lower())

    def test_report_uses_primary_for_complexity_and_ratios(self):
        """Given multiple timers and increasing times
        When format
        Then ratios appear and complexity is computed (not error)
        """
        rows = [
            {'subject': 'f', 'variant': 'v', 'size': 10, 'pixels': 10, 'times': {'wall': 0.01, 'cpu': 0.009}},
            {'subject': 'f', 'variant': 'v', 'size': 20, 'pixels': 20, 'times': {'wall': 0.021, 'cpu': 0.019}},
        ]
        txt = format_perf_report(rows)
        self.isin('2.10x', txt)  # rough ratio
        self.isin('Complexity:', txt)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
