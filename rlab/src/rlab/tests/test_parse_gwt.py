"""
RADICAL TEST: parse_gwt

One test file per atom. GWT on every method.
"""
import sys

from rlab.parse_gwt import parse_gwt
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestParseGwt(RadicalTestCase):
    def test_full_gwt_multiline(self):
        """Given a multiline GWT docstring
        When parse_gwt
        Then return sensible given/when/then strings
        """
        doc = """Given foo bar
        When do thing
        Then expect good
        and more
        """
        g, w, t = parse_gwt(doc)
        self.isin('foo bar', g)
        self.isin('do thing', w)
        self.isin('expect good', t)
        self.isin('and more', t)

    def test_colon_variants(self):
        """Given docstrings with colons after keywords
        When parse_gwt
        Then strip colons and parse correctly
        """
        g, w, t = parse_gwt('Given: alpha\nWhen: beta\nThen: gamma')
        self.equa(g, 'alpha')
        self.equa(w, 'beta')
        self.equa(t, 'gamma')

    def test_empty_and_partial(self):
        """Given empty or partial docstrings
        When parse_gwt
        Then return empty strings for missing parts
        """
        self.equa(parse_gwt(None), ('', '', ''))
        self.equa(parse_gwt(''), ('', '', ''))
        self.equa(parse_gwt('   '), ('', '', ''))
        g, w, t = parse_gwt('Given only this')
        self.equa(g, 'only this')
        self.equa(w, '')
        self.equa(t, '')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
