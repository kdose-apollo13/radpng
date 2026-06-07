"""
RADICAL PNG TEST: plte

One test file per atomic (plte.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.plte import parse_plte, make_plte


class TestPLTE(RadicalTestCase):
    def test_plte_make_parse_roundtrip_and_errors(self):
        """Given palette lists (good + bad)
        When make_plte / parse_plte
        Then roundtrips; raises ValueError on bad len / entry shape
        """
        pal = [(0,0,0), (255,0,0), (0,255,0)]
        data = make_plte(pal)
        self.equa(parse_plte(data), pal)
        self.equa(len(data), 9)

        self.assert_raises_value_err('1..256', make_plte, [])
        self.assert_raises_value_err('1..256', make_plte, [(1,2,3)] * 257)
        self.assert_raises_value_err('entry', make_plte, [(1,2)])
        self.assert_raises_value_err('multiple', parse_plte, b'\0\0')


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
