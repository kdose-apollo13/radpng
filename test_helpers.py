"""
    parse_gwt
    beautify_unittest_output
    RadicalTestResult
    RadicalTextTestRunner
    RadicalTestCase
    _pack_1bit
    _pack_2bit
    _pack_4bit

    Reusable radical test infrastructure extracted from test_radical_png.py:
    GWT docstring parser + beautify for informative output, custom runner/result
    for beauty (bypasses default unittest noise), RadicalTestCase base (domain
    roundtrip helpers + short aliases for less visual noise: asrt/equa/rais/subt
    etc instead of long assert* names), and the test-only low-bd packers (MSB-first,
    deliberately kept out of lib per design).

    Follows radical style for its module (first lines = exportables; terse docs).
    Pure stdlib (unittest, re). Intended for reuse in this or other radical tests.
"""
import unittest
import re

# Lib atoms needed only by the domain helpers in RadicalTestCase (test support)
from encoder import encode_png, encode_rgba
from decoder import decode_png, decode_rgba


# --- GWT + beautify helpers (parse typical test output / docs into sensible lines) ---

def parse_gwt(doc):
    """Parse docstring into (given, when, then) sensible lines (3-part scenarios).

    Tolerates:
      Given foo
      When: bar
      Then baz
    Multi-line continuations until next keyword. Case-insensitive match on keywords.
    Returns clean stripped strings ('' if absent).
    """
    if not doc:
        return '', '', ''
    text = doc.strip()
    if not text:
        return '', '', '',

    # Normalize line starts for keywords
    lines = text.splitlines()
    given_parts = []
    when_parts = []
    then_parts = []
    current = None

    for raw in lines:
        ln = raw.strip()
        low = ln.lower()
        if low.startswith('given'):
            current = 'given'
            rest = ln[5:].lstrip(':').strip()
            if rest:
                given_parts.append(rest)
            continue
        elif low.startswith('when'):
            current = 'when'
            rest = ln[4:].lstrip(':').strip()
            if rest:
                when_parts.append(rest)
            continue
        elif low.startswith('then'):
            current = 'then'
            rest = ln[4:].lstrip(':').strip()
            if rest:
                then_parts.append(rest)
            continue
        elif current == 'given' and ln:
            given_parts.append(ln)
        elif current == 'when' and ln:
            when_parts.append(ln)
        elif current == 'then' and ln:
            then_parts.append(ln)

    return (
        ' '.join(given_parts).strip(),
        ' '.join(when_parts).strip(),
        ' '.join(then_parts).strip(),
    )


def beautify_unittest_output(raw):
    """Parse typical default unittest output into sensible grouped lines.

    Turns lines like:
      test_foo (mod.Class) ... ok
      test_bar (mod.Class) ... FAIL
    into blocks with status and (if we can) scenario feel. Used to demonstrate
    "helpers to parse the typical test output".
    """
    if not raw:
        return ''
    out_lines = []
    # tolerant match for "test_xxx ... ok" (docstring may be on same line in -v)
    pat = re.compile(r'^(test_\w+).*?\.{2,}\s*(ok|FAIL|ERROR|skipped)(.*)$', re.I)
    for line in raw.splitlines():
        m = pat.match(line.strip())
        if m:
            name, status, extra = m.groups()
            out_lines.append(f'SCENARIO: {name}')
            out_lines.append(f'  Status: {status.upper()}')
            if extra and extra.strip():
                out_lines.append(f'  Detail: {extra.strip()}')
            out_lines.append('')
        else:
            if line.strip():
                out_lines.append(line.rstrip())
    return '\n'.join(out_lines).rstrip() + '\n'


# --- Radical wrappers for beauty + readable per-test output ---

class RadicalTestResult(unittest.TextTestResult):
    """Custom result that emits informative GWT 3-line blocks per test.
    We bypass TextTestResult's default name+ok printing for clean radical output.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # suppress the default "desc ... ok" noise; we control all output
        self.separator1 = ' '
        self.separator2 = ''

    def getDescription(self, test):
        return test._testMethodName  # short; we emit full GWT ourselves

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
        # call only TestResult (no printing) so we fully control
        unittest.TestResult.startTest(self, test)
        if self.showAll:
            self._emit_gwt(test)

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)  # record only
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


class RadicalTextTestRunner(unittest.TextTestRunner):
    """Runner that uses RadicalTestResult and adds radical banners/summary."""

    def __init__(self, **kwargs):
        kwargs.setdefault('verbosity', 2)
        super().__init__(**kwargs)

    def _makeResult(self):
        return RadicalTestResult(self.stream, self.descriptions, self.verbosity)

    def run(self, test):
        self.stream.writeln('')
        self.stream.writeln('=' * 58)
        self.stream.writeln('  RADICAL PNG TESTS  (stdlib + GWT wrappers + beauty)')
        self.stream.writeln('  pure python | no deps | informative per-test output')
        self.stream.writeln('=' * 58)
        result = super().run(test)
        self.stream.writeln('-' * 58)
        n = result.testsRun
        fails = len(result.failures) + len(result.errors)
        if fails == 0:
            self.stream.writeln(f'  Ran {n} tests. ALL PASS. Radical!')
        else:
            self.stream.writeln(f'  Ran {n} tests. {fails} failures/errors.')
        self.stream.writeln('  (See SUGGESTIONS.md for refinements surfaced by tests)')
        self.stream.writeln('=' * 58)
        self.stream.writeln('')
        return result


class RadicalTestCase(unittest.TestCase):
    """Light unittest.TestCase wrapper supplying radical/PNG conveniences.

    Includes short aliases (set in __init__) to reduce visual noise vs long
    self.assertEqual etc:
        self.asrt = self.assertTrue
        self.equa = self.assertEqual
        self.rais = self.assertRaises
        self.subt = self.subTest
        self.nota = self.assertFalse
        self.isin = self.assertIn
    (Plus domain helpers below; aliases available for subclass test methods too.)
    """

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        # short aliases for less noisy / visually lighter tests (per radical style)
        self.asrt = self.assertTrue
        self.equa = self.assertEqual
        self.rais = self.assertRaises
        self.subt = self.subTest
        self.nota = self.assertFalse
        self.isin = self.assertIn

    def assert_png_roundtrip(self, ihdr, data, palette=None, filter_type=0):
        """Encode then decode; assert data and core ihdr fields match."""
        png = encode_png(ihdr, data, palette=palette, filter_type=filter_type)
        dec = decode_png(png)
        self.equa(dec['data'], bytes(data))
        for k in ('width', 'height', 'bit_depth', 'color_type'):
            self.equa(dec[k], ihdr[k])
        if palette is not None:
            self.equa(dec.get('palette'), palette)

    def assert_rgba_roundtrip(self, pixels, filter_type=0):
        """High-level rgba 2d roundtrip."""
        png = encode_rgba(pixels, filter_type=filter_type)
        back = decode_rgba(png)
        self.equa(back, pixels)

    def assert_raises_value_err(self, msg_substr, func, *a, **k):
        """Assert ValueError whose str contains substr (case-insens)."""
        with self.rais(ValueError) as ctx:
            func(*a, **k)
        self.isin(msg_substr.lower(), str(ctx.exception).lower())


# --- Tiny packers (test-only) for low-bd data to feed encode/decode ---
# Deliberately test-only (keep lib surface thin, per design in SUGGESTIONS.md).

def _pack_1bit(values, width):
    """Pack list of 0/1 ints (left-to-right) into bytes, MSB first per PNG."""
    rowb = (width + 7) // 8
    data = bytearray(rowb)
    for x, v in enumerate(values):
        if v:
            byte_i = x // 8
            bit = 7 - (x % 8)
            data[byte_i] |= (1 << bit)
    return bytes(data)


def _pack_2bit(values, width):
    """Pack 0-3 ints, 4 samples/byte, high bits first."""
    rowb = (width + 3) // 4
    data = bytearray(rowb)
    for x, v in enumerate(values):
        byte_i = x // 4
        shift = 6 - 2 * (x % 4)
        data[byte_i] |= ((v & 3) << shift)
    return bytes(data)


def _pack_4bit(values, width):
    """Pack 0-15 ints, 2 samples/byte, high nibble first."""
    rowb = (width + 1) // 2
    data = bytearray(rowb)
    for x, v in enumerate(values):
        byte_i = x // 2
        if x % 2 == 0:
            data[byte_i] |= ((v & 15) << 4)
        else:
            data[byte_i] |= (v & 15)
    return bytes(data)
