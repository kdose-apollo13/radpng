"""
RADICAL PNG TEST: signature

One test file per atomic (signature.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys

import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.signature import PNG_SIGNATURE


class TestSignature(RadicalTestCase):
    def test_signature_constant(self):
        """Given the PNG magic constant
        When inspected
        Then it is exactly the 8-byte spec value
        """
        self.equa(PNG_SIGNATURE, b'\x89PNG\r\n\x1a\n')
        self.equa(len(PNG_SIGNATURE), 8)


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
