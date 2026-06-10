"""
RADICAL PNG TEST: paeth

One test file per atomic (paeth.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.paeth import paeth_predictor
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestPaeth(RadicalTestCase):
    def test_paeth_known_and_edges(self):
        """Given the paeth predictor (a+b-c choose closest)
        When calling with the demo cases + 0/255 edges
        Then returns exactly the documented closest value
        """
        self.equa(paeth_predictor(10, 20, 5), 20)
        self.equa(paeth_predictor(5, 20, 10), 20)
        self.equa(paeth_predictor(10, 5, 20), 5)
        self.equa(paeth_predictor(0, 0, 0), 0)
        self.equa(paeth_predictor(255, 255, 255), 255)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
