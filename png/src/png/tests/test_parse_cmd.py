"""
RADICAL PNG TEST: parse_cmd
"""
import sys

from png.parse_cmd import parse_viewer_command, parse_win_spec
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestParseCmd(RadicalTestCase):
    def test_load_and_resize(self):
        """Given plain commands
        When parsed
        Then correct verb and payload
        """
        self.equa(parse_viewer_command('load waves.png'),
                  {'verb': 'load', 'path': 'waves.png'})
        self.equa(parse_viewer_command('200x100'),
                  {'verb': 'resize', 'w': 200, 'h': 100})
        self.equa(parse_viewer_command('  400 X 300  '),
                  {'verb': 'resize', 'w': 400, 'h': 300})

    def test_win_and_quit(self):
        self.equa(parse_viewer_command('win max'), {'verb': 'win', 'spec': 'max'})
        self.equa(parse_viewer_command('win 500x300'), {'verb': 'win', 'spec': '500x300'})
        self.equa(parse_viewer_command('q'), {'verb': 'quit'})
        self.equa(parse_viewer_command(''), None)

    def test_bad_input(self):
        with self.rais(ValueError):
            parse_viewer_command('win ')
        with self.rais(ValueError):
            parse_viewer_command('0x100')
        self.equa(parse_viewer_command('nope')['verb'], 'unknown')

    def test_parse_win_spec(self):
        self.equa(parse_win_spec('max'), ('max',))
        self.equa(parse_win_spec('min'), ('min',))
        self.equa(parse_win_spec('500x300'), ('size', 500, 300))
        with self.rais(ValueError):
            parse_win_spec('bad')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)