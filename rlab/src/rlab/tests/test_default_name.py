"""
RADICAL TEST: default_name
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.default_name import default_name


class TestDefaultName(RadicalTestCase):
    def test_explicit_overrides(self):
        """Given explicit label
        When default_name
        Then explicit wins
        """
        def f(): pass
        self.equa(default_name(f, explicit='forced'), 'forced')

    def test_falls_back_to_qualname_or_name(self):
        """Given a function
        When default_name (no explicit)
        Then __qualname__ (or __name__ for top-level)
        """
        # defined at module level so qualname is clean
        self.equa(default_name(_module_level_helper), '_module_level_helper')


def _module_level_helper(): pass


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
