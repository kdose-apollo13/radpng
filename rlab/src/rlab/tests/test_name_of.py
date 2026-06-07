"""
RADICAL TEST: name_of
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.name_of import name_of


class TestNameOf(RadicalTestCase):
    def test_str_passes_through(self):
        """Given a string
        When name_of
        Then the string is returned unchanged
        """
        self.equa(name_of('my_subject'), 'my_subject')

    def test_callable_uses_dunder_name(self):
        """Given a function or other __name__-bearing object
        When name_of
        Then __name__ is used
        """
        def my_func(): pass
        self.equa(name_of(my_func), 'my_func')

    def test_fallback_for_unnamed(self):
        """Given something without __name__ and a fallback
        When name_of
        Then the fallback is used
        """
        self.equa(name_of(42, fallback='unknown'), 'unknown')
        self.equa(name_of(None), 'subject')  # default fallback


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
