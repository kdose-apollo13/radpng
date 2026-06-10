"""
RADICAL PNG TEST: plte

One test file per atomic (plte.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.plte import parse_plte, make_plte
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestPLTE(RadicalTestCase):
    def test_plte_make_parse_roundtrip_and_errors(self):
        """Given palette lists (good + bad)
        When make_plte / parse_plte
        Then roundtrips; raises ValueError on bad len / entry shape
        """
        pal = [(0, 0, 0), (255, 0, 0), (0, 255, 0)]
        data = make_plte(pal)
        self.equa(parse_plte(data), pal)
        self.equa(len(data), 9)
        with self.rais(ValueError):
            make_plte([])
        with self.rais(ValueError):
            make_plte([(1, 2, 3)] * 257)
        with self.rais(ValueError):
            make_plte([(1, 2)])
        with self.rais(ValueError):
            parse_plte(b'\0\0')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
