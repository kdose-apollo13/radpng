"""
RADICAL PNG TEST: check_signature

One test file per atomic (check_signature.py). GWT on every method.
Reuses RadicalTestCase + short aliases from test_helpers.
Pure stdlib only.
"""
import os
import sys


import io
import unittest
from test_helpers import RadicalTestCase, RadicalTextTestRunner
from png.signature import PNG_SIGNATURE
from png.check_signature import check_signature


class TestCheckSignature(RadicalTestCase):
    def test_signature_good_bad(self):
        """Given good and bad signature bytes via BytesIO
        When check_signature
        Then ok or ValueError('bad PNG signature')
        """
        good = PNG_SIGNATURE + b'\0'*4
        with io.BytesIO(good) as f:
            check_signature(f)  # no raise
        bad = b'NOTAPNG!' + b'\0'*4
        with io.BytesIO(bad) as f:
            self.assert_raises_value_err('signature', check_signature, f)


def run_all_tests(verbosity=2):
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
