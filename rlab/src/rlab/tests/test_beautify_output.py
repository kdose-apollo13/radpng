"""
RADICAL TEST: beautify_output

One test file per atom. GWT on every method.
"""
import sys

from rlab.beautify_output import beautify_unittest_output
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestBeautifyOutput(RadicalTestCase):
    def test_ok_and_fail_lines(self):
        """Given typical unittest verbose output lines
        When beautify_unittest_output
        Then group into SCENARIO blocks with Status
        """
        raw = 'test_foo (TestBar) ... ok\ntest_bar (TestBar) ... FAIL\n'
        nice = beautify_unittest_output(raw)
        self.isin('SCENARIO: test_foo', nice)
        self.isin('Status: OK', nice)
        self.isin('SCENARIO: test_bar', nice)
        self.isin('Status: FAIL', nice)

    def test_error_and_empty(self):
        """Given ERROR lines and empty input
        When beautify_unittest_output
        Then parse ERROR status or return empty string
        """
        raw = 'test_baz (Mod) ... ERROR\n'
        nice = beautify_unittest_output(raw)
        self.isin('Status: ERROR', nice)
        self.equa(beautify_unittest_output(''), '')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
