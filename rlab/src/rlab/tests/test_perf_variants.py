"""
RADICAL TEST: perf_variants
One test file per atom. GWT on every method.
"""
import sys
import importlib

from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_variants import using_impls, check_signature_compat

# module-level dummies (so they become attrs on __main__ or the real module when run directly)
# identical sigs for swap demos
def _var_demo_target(x, y, z):
    return x + y + z

def _var_demo_alt(x, y, z):
    return (x + y + z) + 1000

def _var_t(a):
    return a * 2

def _var_alt(a):
    return a * 3


class TestPerfVariants(RadicalTestCase):
    def test_using_impls_swaps_and_restores(self):
        """Given two funcs with identical (a,b,c)->int sig at module level
        When using_impls on the dotted name for the duration of a block
        Then inside block the swapped func is live; after exit original is restored
        """
        key = __name__ + '._var_demo_target'
        before = _var_demo_target(1, 2, 3)
        self.equa(before, 6)

        with using_impls({key: _var_demo_alt}):
            mod = importlib.import_module(__name__)
            during = getattr(mod, '_var_demo_target')(1, 2, 3)
            self.equa(during, 1006)

        after = _var_demo_target(1, 2, 3)
        self.equa(after, 6)

    def test_using_impls_restores_on_exception(self):
        """Given a swap ctx that raises inside the block
        When exiting via exception
        Then original is still restored (finally path)
        """
        key = __name__ + '._var_t'
        try:
            with using_impls({key: _var_alt}):
                mod = importlib.import_module(__name__)
                self.equa(getattr(mod, '_var_t')(5), 15)
                raise ValueError('boom inside swap')
        except ValueError:
            pass

        self.equa(_var_t(5), 10)  # restored

    def test_check_signature_compat_basic(self):
        """Given two callables
        When check_signature_compat
        Then returns True for same arity (advisory)
        """
        def f1(a, b):
            return a + b

        def f2(a, b):
            return a * b

        self.asrt(check_signature_compat(f1, f2))

    def test_using_impls_bad_key_raises_early(self):
        """Given a non-dotted key
        When entering using_impls
        Then ValueError before any replacement
        """
        def dummy(x):
            return x
        with self.rais(ValueError):
            with using_impls({'badkey': dummy}):
                pass

    def test_rlab_perf_variants_has_no_png_dependency(self):
        """Given the perf_variants module (layering)
        When inspecting its source
        Then it contains no 'import png' or 'from png' (rlab must not depend on png)
        """
        import rlab.perf_variants as pv
        # read the file that was imported
        with open(pv.__file__, 'r', encoding='utf-8') as f:
            src = f.read()
        self.nota('import png' in src)
        self.nota('from png' in src)


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
