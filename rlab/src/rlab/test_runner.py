"""
    RadicalTextTestRunner
    austere unittest runner using RadicalTestResult
"""
import unittest

from rlab.test_result import RadicalTestResult


class RadicalTextTestRunner(unittest.TextTestRunner):
    """
        verbosity
            : int
            : default 2

        prints
            > rlab (one line at start)
            > per-test GWT output via RadicalTestResult
            > Ran N tests. F failures. (one line at end)
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('verbosity', 2)
        super().__init__(**kwargs)

    def _makeResult(self):
        return RadicalTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        self.stream.writeln('rlab')
        result = super().run(test)
        n = result.testsRun
        fails = len(result.failures) + len(result.errors)
        self.stream.writeln(f'Ran {n} tests. {fails} failures.')
        return result
