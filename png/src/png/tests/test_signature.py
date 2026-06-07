"""
RADICAL PNG TEST: signature

One test file per atomic (signature.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.signature import PNG_SIGNATURE
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestSignature(PngTestCase):
    def test_signature_constant(self):
        """Given the PNG magic constant
        When inspected
        Then it is exactly the 8-byte spec value
        """
        self.equa(PNG_SIGNATURE, b'\x89PNG\r\n\x1a\n')
        self.equa(len(PNG_SIGNATURE), 8)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
