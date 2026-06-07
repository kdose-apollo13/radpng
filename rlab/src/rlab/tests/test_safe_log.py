"""
RADICAL TEST: safe_log
One test file per atom.
"""
import sys
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests
from rlab.safe_log import safe_log


class TestSafeLog(RadicalTestCase):
    def test_positive_logs(self):
        self.asrt(safe_log(1) == 0.0)
        self.asrt(safe_log(8) > 2)

    def test_non_positive_returns_zero(self):
        self.equa(safe_log(0), 0.0)
        self.equa(safe_log(-5), 0.0)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
