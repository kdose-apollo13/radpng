"""
RADICAL TEST: normalize_series
One test file per atom.
"""
import sys
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests
from rlab.normalize_series import normalize_series


class TestNormalizeSeries(RadicalTestCase):
    def test_scales_to_unit(self):
        self.equa(normalize_series([0, 50, 100]), [0.0, 0.5, 1.0])

    def test_empty_and_zero_max(self):
        self.equa(normalize_series([]), [])
        self.equa(normalize_series([0, 0]), [0.0, 0.0])


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
