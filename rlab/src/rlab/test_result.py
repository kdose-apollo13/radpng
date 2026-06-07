"""
    RadicalTestResult
    unittest result that prints GWT scenario lines per test
"""
import unittest

from rlab.parse_gwt import parse_gwt


class RadicalTestResult(unittest.TextTestResult):
    """
        stream
            : file-like
        descriptions
            : bool
        verbosity
            : int

        emits per test
            > [TEST] name
            > Given / When / Then (from docstring)
            > [PASS] / [FAIL] / [ERROR] / [SKIP]
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.separator1 = ' '
        self.separator2 = ''

    def getDescription(self, test):
        return test._testMethodName

    def _emit_gwt(self, test):
        doc = getattr(test, '_testMethodDoc', None)
        g, w, t = parse_gwt(doc)
        self.stream.writeln(f'  [TEST] {test._testMethodName}')
        if g:
            self.stream.writeln(f'    Given: {g}')
        if w:
            self.stream.writeln(f'    When:  {w}')
        if t:
            self.stream.writeln(f'    Then:  {t}')

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        if self.showAll:
            self._emit_gwt(test)

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        if self.showAll:
            self.stream.writeln('    [PASS]\n')

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        if self.showAll:
            self.stream.writeln('    [FAIL]')
            self.stream.writeln(f'    {err[1]}\n')

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        if self.showAll:
            self.stream.writeln('    [ERROR]')
            self.stream.writeln(f'    {err[1]}\n')

    def addSkip(self, test, reason):
        unittest.TestResult.addSkip(self, test, reason)
        if self.showAll:
            self.stream.writeln(f'    [SKIP] {reason}\n')
