#!/usr/bin/env python3
from unittest import defaultTestLoader, TextTestRunner
from klab.ututils import Runner

import sys


def main(args):
    file_name, *options = args

    suite = defaultTestLoader.discover('.')
    if '-q' in options:
        runner = TextTestRunner()
    else:
        runner = Runner()

    runner.run(suite)

if __name__ == '__main__':
    sys.exit(main(sys.argv))

