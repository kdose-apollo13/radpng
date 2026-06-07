"""
RADICAL TEST: primary_label
One test file per atom. GWT on every method.
"""
import sys

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.primary_label import primary_label


class TestPrimaryLabel(RadicalTestCase):
    def test_prefers_known_prefixes(self):
        """Given times dict with wall/perf/min/repeated labels
        When primary_label
        Then the first preferred one in order
        """
        self.equa(primary_label({'cpu': 1, 'wall': 0.1}), 'wall')
        self.equa(primary_label({'foo': 1, 'min_of_3': 0.9}), 'min_of_3')

    def test_falls_back_to_first_key(self):
        """Given no preferred label
        When primary_label
        Then first key or None
        """
        self.equa(primary_label({'only': 5}), 'only')
        self.equa(primary_label({}), None)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
