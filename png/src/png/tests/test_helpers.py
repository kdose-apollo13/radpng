"""
    parse_gwt
    beautify_unittest_output
    RadicalTestResult
    RadicalTextTestRunner
    RadicalTestCase
    _pack_1bit
    _pack_2bit
    _pack_4bit
    make_synthetic_image_data
    make_synthetic_png

    Reusable radical test infrastructure extracted from test_radical_png.py:
    GWT docstring parser + beautify for informative output, custom runner/result
    for beauty (bypasses default unittest noise), RadicalTestCase base (domain
    roundtrip helpers + short aliases for less visual noise: asrt/equa/rais/subt
    etc instead of long assert* names), and the test-only low-bd packers (MSB-first,
    deliberately kept out of lib per design).

    Also: on-demand synthetic PNG bytes + raw image data for convenient testing
    of different file sizes / dimensions / ct / bd without fs or external assets.

    Follows radical style for its module (first lines = exportables; terse docs).
    Pure stdlib (unittest, re, time). Intended for reuse in this or other radical tests.
"""
import os
import sys
# Radical flat layout bootstrap: make "from xxx import" of sibling lib atoms and
# "from test_helpers import" work for direct "python tests/test_foo.py" runs as
# well as ktest discover and python -m unittest from project root. Everything
# limited to present dir.

import unittest
import re

# Lib atoms needed only by the domain helpers in RadicalTestCase (test support)
from png.encoder import encode_png, encode_rgba
from png.decoder import decode_png, decode_rgba

# row_bytes atoms for synth data length calc (test support only)
from png.row_bytes import get_row_bytes, _samples_per_pixel


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


# --- On-demand synthetic PNG streams / raw data (for different file sizes) ---
# Pure, deterministic, no fs. Use for perf, scaling, matrix tests of varying
# dimensions / color_type / bit_depth. Returns bytes usable directly as
# "png stream" (decode_png accepts bytes) or wrapped in io.BytesIO if desired.

def make_synthetic_image_data(width, height, color_type, bit_depth):
    """Return correct-length unfiltered raw scanline bytes (deterministic pattern).

    Handles all valid ct (0/2/3/4/6) + bd (1/2/4/8/16). For bd<8 uses the
    test-only packers (MSB-first) so the bytes are exactly what encode_png
    expects. Length == height * get_row_bytes(...).

    Pure stdlib + local test support; no filesystem.
    """
    spp = _samples_per_pixel(color_type)
    samples_per_row = width * spp
    max_sample = (1 << bit_depth) - 1 if bit_depth <= 16 else 255

    def sample_val(i):
        # simple repeating ramp in legal range; different rows vary a bit
        return (i * 37 + (i // samples_per_row) * 11) % (max_sample + 1)

    out = bytearray()
    for y in range(height):
        vals = [sample_val(y * samples_per_row + x) for x in range(samples_per_row)]
        if bit_depth == 1:
            packed = _pack_1bit(vals, samples_per_row)
        elif bit_depth == 2:
            packed = _pack_2bit(vals, samples_per_row)
        elif bit_depth == 4:
            packed = _pack_4bit(vals, samples_per_row)
        elif bit_depth == 8:
            packed = bytes(v & 0xff for v in vals)
        else:  # 16-bit: big-endian per sample (as PNG requires)
            ba = bytearray()
            for v in vals:
                vv = v & 0xffff
                ba.extend(((vv >> 8) & 0xff, vv & 0xff))
            packed = bytes(ba)
        out.extend(packed)

    expected = height * get_row_bytes(width, color_type, bit_depth)
    if len(out) != expected:
        raise AssertionError(f'synth data len {len(out)} != expected {expected}')
    return bytes(out)


def make_synthetic_png(width=8, height=8, color_type=0, bit_depth=8,
                       filter_type=0, palette=None):
    """On-demand complete PNG bytes (sig + chunks) for convenient size/ct/bd/ft testing.

    Builds valid ihdr + correct-length synth raw data (via make_synthetic_image_data)
    then calls the real encode_png. Result can be passed directly to decode_png
    (bytes accepted) or wrapped: decode_png(io.BytesIO(png)).

    For ct=3: if palette is None a minimal sensible gray ramp palette is supplied
    so callers can omit it for quick size sweeps.

    Pure; no fs. Vary (width, height) to get different "file sizes".
    """
    ih = {
        'width': width,
        'height': height,
        'bit_depth': bit_depth,
        'color_type': color_type,
        'compression_method': 0,
        'filter_method': 0,
        'interlace_method': 0,
    }
    data = make_synthetic_image_data(width, height, color_type, bit_depth)

    if color_type == 3 and palette is None:
        # auto minimal valid palette sized for the bd (max 256)
        n = min(1 << bit_depth, 256) or 1
        palette = [( (i * 255) // max(n-1, 1) ,) * 3 for i in range(n)]

    return encode_png(ih, data, palette=palette, filter_type=filter_type)


# --- Self-test of the helpers themselves (GWT style, radical) ---

class TestHelpers(RadicalTestCase):
    def test_parse_gwt_and_beautify_helpers(self):
        """Given GWT docstrings and sample typical unittest text
        When parse_gwt + beautify_unittest_output
        Then return sensible 3-part lines or reformatted blocks
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

        raw_typ = 'test_foo (TestBar) ... ok\nTestHelpers.test_parse... ... FAIL\n'
        nice = beautify_unittest_output(raw_typ)
        self.isin('SCENARIO:', nice)
        self.isin('Status:', nice)


# --- Run entry points (the convenient way, per radical style) ---

def run_all_tests(verbosity=2):
    """Convenient function to run the radical test helpers self-tests."""
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests(verbosity=2)
    sys.exit(0 if result.wasSuccessful() else 1)

