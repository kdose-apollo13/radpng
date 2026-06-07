"""
RADICAL TEST: model_error
One test file per atom.
"""
import sys
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests
from rlab.model_error import model_error


class TestModelError(RadicalTestCase):
    def test_perfect_linear_is_near_zero(self):
        def lin(n): return float(n)
        e = model_error([10, 20], [10.0, 20.0], lin)
        self.asrt(e < 0.01)

    def test_insufficient_data(self):
        self.equa(model_error([5], [1.0], lambda n: n), 1.0)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
