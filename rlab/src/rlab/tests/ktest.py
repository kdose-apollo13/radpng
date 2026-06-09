#!/usr/bin/env python3
"""
    ktest
    discover and run rlab tests
"""
import sys
from unittest import defaultTestLoader, TextTestRunner

from rlab.test_runner import RadicalTextTestRunner


def main(argv):
    """
        argv
            : list
            : command-line args after script name; pass -q for quiet stdlib runner

        returns
            > int
            > exit code (0 ok, 1 failures)
    """
    options = argv
    suite = defaultTestLoader.discover('.')
    if '-q' in options:
        runner = TextTestRunner()
    else:
        runner = RadicalTextTestRunner()
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))