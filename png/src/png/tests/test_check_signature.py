"""
RADICAL PNG TEST: check_signature

One test file per atomic (check_signature.py). GWT on every method.
Pure stdlib only.
"""
import io
import sys

from png.signature import PNG_SIGNATURE
from png.check_signature import check_signature
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestCheckSignature(RadicalTestCase):
    def test_signature_good_bad(self):
        """Given good and bad signature bytes via BytesIO
        When check_signature
        Then ok or ValueError('bad PNG signature')
        """
        good = PNG_SIGNATURE + b'\0' * 4
        with io.BytesIO(good) as f:
            check_signature(f)
        bad = b'NOTAPNG!' + b'\0' * 4
        with io.BytesIO(bad) as f:
            with self.rais(ValueError):
                check_signature(f)

    def test_signature_truncated(self):
        """Given fewer than 8 signature bytes
        When check_signature
        Then ValueError mentioning signature
        """
        with io.BytesIO(b'\x89PNG\r') as f:
            with self.rais(ValueError):
                check_signature(f)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
