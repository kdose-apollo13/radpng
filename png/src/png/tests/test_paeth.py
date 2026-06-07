"""
RADICAL PNG TEST: paeth

One test file per atomic (paeth.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.paeth import paeth_predictor


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
        self.equa(paeth_predictor(10, 0, 255), 0)  # p=-245, closest is b=0


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
