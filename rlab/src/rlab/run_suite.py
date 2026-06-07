"""
    run_module_tests
    load and run all tests from a module via RadicalTextTestRunner
"""
import sys
import unittest

from rlab.test_runner import RadicalTextTestRunner


def run_module_tests(module, verbosity=2):
    """
        module
            : module
            : test module (typically sys.modules[__name__])
        verbosity
            : int

        returns
            > unittest.TestResult
    """
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(module)
    return runner.run(suite)


if __name__ == '__main__':
    print('=== run_suite demo ===')
    print('import and call run_module_tests(sys.modules[__name__]) from test files')
