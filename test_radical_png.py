"""
RADICAL PNG TESTS (pure stdlib unittest wrappers)

Goal: tests only (no lib changes). Individual test outputs are informative/readable
via GWT (Given/When/Then) parsing from docstrings + subclassed TextTestRunner/Result.

- parse_gwt(doc) + beautify_unittest_output(raw) : helpers to turn typical output/docs
  into sensible 3-line (or equiv) scenario descriptions.
- RadicalTestResult / RadicalTextTestRunner : beauty + radical nature for output.
- RadicalTestCase : light domain helpers (roundtrips etc).
- All cases exercise atoms + full paths + errors + matrix (incl low bd + 16b + split IDAT).
- One purpose of tests: surface refinements (see SUGGESTIONS.md companion file).

Run all (the convenient way):
    python test_radical_png.py

Also works with:
    python -m unittest test_radical_png -v
    python -c 'import test_radical_png as t; t.run_all_tests()'

Pure stdlib only (unittest, io, sys, os, re, zlib, struct). Deserted-island python.
Follows radical style: small focused tests, explicit, synthetic data, full coverage of
current raises/paths, GWT docs on every test method.
"""

import unittest
import io
import sys
import os
import re
import zlib
import struct

# Local imports (flat project, run from root or with . on path)
from signature import PNG_SIGNATURE
from check_signature import check_signature
from iter_chunks import iter_chunks
from make_chunk import make_chunk
from ihdr import parse_ihdr, make_ihdr
from plte import parse_plte, make_plte
from row_bytes import get_row_bytes
from bpp import get_bpp
from paeth import paeth_predictor
from filters import apply_filter
from unfilter import unfilter
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
    """Light unittest.TestCase wrapper supplying radical/PNG conveniences."""

    def assert_png_roundtrip(self, ihdr, data, palette=None, filter_type=0):
        """Encode then decode; assert data and core ihdr fields match."""
        png = encode_png(ihdr, data, palette=palette, filter_type=filter_type)
        dec = decode_png(png)
        self.assertEqual(dec['data'], bytes(data))
        for k in ('width', 'height', 'bit_depth', 'color_type'):
            self.assertEqual(dec[k], ihdr[k])
        if palette is not None:
            self.assertEqual(dec.get('palette'), palette)

    def assert_rgba_roundtrip(self, pixels, filter_type=0):
        """High-level rgba 2d roundtrip."""
        png = encode_rgba(pixels, filter_type=filter_type)
        back = decode_rgba(png)
        self.assertEqual(back, pixels)

    def assert_raises_value_err(self, msg_substr, func, *a, **k):
        """Assert ValueError whose str contains substr (case-insens)."""
        with self.assertRaises(ValueError) as ctx:
            func(*a, **k)
        self.assertIn(msg_substr.lower(), str(ctx.exception).lower())


# --- Tiny packers (test-only) for low-bd data to feed encode/decode ---

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


# --- Test classes (every method has GWT docstring; focused + subTest where good) ---

class TestPaeth(RadicalTestCase):
    def test_paeth_known_and_edges(self):
        """Given the paeth predictor (a+b-c choose closest)
        When calling with the demo cases + 0/255 edges
        Then returns exactly the documented closest value
        """
        self.assertEqual(paeth_predictor(10, 20, 5), 20)
        self.assertEqual(paeth_predictor(5, 20, 10), 20)
        self.assertEqual(paeth_predictor(10, 5, 20), 5)
        self.assertEqual(paeth_predictor(0, 0, 0), 0)
        self.assertEqual(paeth_predictor(255, 255, 255), 255)
        self.assertEqual(paeth_predictor(10, 0, 255), 0)  # p=-245, closest is b=0


class TestBppAndRowBytes(RadicalTestCase):
    def test_bpp_and_row_bytes_matrix_and_edges(self):
        """Given the ct/bd matrix from spec + ihdr
        When calling get_bpp / get_row_bytes for valid + invalid
        Then correct byte counts (incl bit-packed) + ValueError on bad ct
        """
        # bpp
        self.assertEqual(get_bpp(0, 8), 1)
        self.assertEqual(get_bpp(0, 1), 1)
        self.assertEqual(get_bpp(2, 8), 3)
        self.assertEqual(get_bpp(6, 8), 4)
        self.assertEqual(get_bpp(2, 16), 6)
        self.assertEqual(get_bpp(0, 16), 2)
        self.assertEqual(get_bpp(3, 4), 1)
        # row bytes
        self.assertEqual(get_row_bytes(1, 0, 8), 1)
        self.assertEqual(get_row_bytes(200, 0, 8), 200)
        self.assertEqual(get_row_bytes(1, 2, 8), 3)
        self.assertEqual(get_row_bytes(1, 6, 8), 4)
        self.assertEqual(get_row_bytes(9, 0, 1), 2)  # 9 bits -> 2 bytes
        self.assertEqual(get_row_bytes(1, 0, 1), 1)
        self.assertEqual(get_row_bytes(1, 6, 16), 8)
        with self.assertRaises(ValueError):
            get_bpp(99, 8)
        with self.assertRaises(ValueError):
            get_row_bytes(10, 99, 8)


class TestIHDR(RadicalTestCase):
    def test_ihdr_make_parse_roundtrip_valid(self):
        """Given valid ihdr dicts for several ct/bd (incl defaults)
        When make_ihdr then parse_ihdr
        Then roundtrips exactly (methods defaulted to 0)
        """
        d = {
            'width': 4, 'height': 2,
            'bit_depth': 8, 'color_type': 0,
            'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
        }
        self.assertEqual(parse_ihdr(make_ihdr(d)), d)

        d2 = {'width': 1, 'height': 1, 'bit_depth': 1, 'color_type': 3}
        made = make_ihdr(d2)
        p = parse_ihdr(made)
        self.assertEqual(p['width'], 1)
        self.assertEqual(p['bit_depth'], 1)
        self.assertEqual(p['color_type'], 3)

    def test_ihdr_parse_errors(self):
        """Given bad ihdr bytes (len, zero dim, bad methods, bad ct/bd combo)
        When parse_ihdr
        Then ValueError with informative message
        """
        self.assert_raises_value_err('13 bytes', parse_ihdr, b'abc')
        self.assert_raises_value_err('> 0', parse_ihdr, make_ihdr({'width': 0, 'height': 1, 'bit_depth': 8, 'color_type': 0}))
        self.assert_raises_value_err('> 0', parse_ihdr, make_ihdr({'width': 1, 'height': 0, 'bit_depth': 8, 'color_type': 0}))
        # w=1 h=1 bd=8 ct=0 comp=1 -> hits comp check (before ct/bd matrix)
        self.assert_raises_value_err('compression', parse_ihdr, b'\0\0\0\1\0\0\0\1\x08\x00\x01\x00\x00')
        self.assert_raises_value_err('color_type', parse_ihdr, make_ihdr({'width':1,'height':1,'bit_depth':8,'color_type':1}))
        self.assert_raises_value_err('bit_depth', parse_ihdr, make_ihdr({'width':1,'height':1,'bit_depth':2,'color_type':2}))


class TestPLTE(RadicalTestCase):
    def test_plte_make_parse_roundtrip_and_errors(self):
        """Given palette lists (good + bad)
        When make_plte / parse_plte
        Then roundtrips; raises ValueError on bad len / entry shape
        """
        pal = [(0,0,0), (255,0,0), (0,255,0)]
        data = make_plte(pal)
        self.assertEqual(parse_plte(data), pal)
        self.assertEqual(len(data), 9)

        self.assert_raises_value_err('1..256', make_plte, [])
        self.assert_raises_value_err('1..256', make_plte, [(1,2,3)] * 257)
        self.assert_raises_value_err('entry', make_plte, [(1,2)])
        self.assert_raises_value_err('multiple', parse_plte, b'\0\0')


class TestChunksAndSig(RadicalTestCase):
    def test_signature_good_bad(self):
        """Given good and bad signature bytes via BytesIO
        When check_signature
        Then ok or ValueError('bad PNG signature')
        """
        good = PNG_SIGNATURE + b'\0'*4
        with io.BytesIO(good) as f:
            check_signature(f)  # no raise
        bad = b'NOTAPNG!' + b'\0'*4
        with io.BytesIO(bad) as f:
            self.assert_raises_value_err('signature', check_signature, f)

    def test_make_chunk_basic_and_crc(self):
        """Given typ+data
        When make_chunk
        Then length correct + crc32(typ+data) matches the trailer
        """
        ch = make_chunk(b'IHDR', b'\0'*13)
        self.assertEqual(len(ch), 4+4+13+4)
        self.assertEqual(ch[4:8], b'IHDR')
        crc = struct.unpack('>I', ch[-4:])[0]
        expected = zlib.crc32(b'IHDR' + b'\0'*13) & 0xffffffff
        self.assertEqual(crc, expected)

        self.assert_raises_value_err('4 bytes', make_chunk, b'ABC', b'')

    def test_iter_chunks_good_and_bad_crc_trunc(self):
        """Given minimal good png bytes + corrupted/truncated variants
        When iter_chunks (after sig)
        Then yields expected (IHDR,IDAT,IEND); raises on crc / trunc
        """
        # build a tiny valid png using our encoder (ct0 1x1)
        ih = {'width':1,'height':1,'bit_depth':8,'color_type':0,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        p = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
            make_chunk(b'IDAT', zlib.compress(b'\0\xff')) + make_chunk(b'IEND', b'')
        with io.BytesIO(p) as f:
            check_signature(f)
            chunks = list(iter_chunks(f))
            self.assertEqual([t for t,d in chunks], [b'IHDR', b'IDAT', b'IEND'])

        # bad crc
        bad = bytearray(p)
        bad[-5] ^= 0xff  # flip in IEND crc area-ish
        with io.BytesIO(bad) as f:
            check_signature(f)
            with self.assertRaises(ValueError) as ctx:
                list(iter_chunks(f))
            self.assertIn('CRC', str(ctx.exception))

        # trunc
        short = p[:-10]
        with io.BytesIO(short) as f:
            check_signature(f)
            with self.assertRaises(ValueError):
                list(iter_chunks(f))


class TestFilterUnfilter(RadicalTestCase):
    def test_filter_unfilter_symmetry_ct0_various_ft(self):
        """Given 4x2 gray8 synthetic raw bytes (same as lib demos)
        When filter(..., filter_type=ft) for ft in 0..4 then unfilter the result
        Then recon bytes exactly == orig for every ft (proves symmetry + paeth edges)
        """
        W, H = 4, 2
        orig = bytearray((x + y * 3) * 40 % 256 for y in range(H) for x in range(W))
        for ft in range(5):
            with self.subTest(filter_type=ft):
                filt = apply_filter(orig, W, H, 0, 8, filter_type=ft)
                recon = unfilter(filt, W, H, 0, 8)
                self.assertEqual(recon, bytes(orig))

    def test_filter_type0_is_identity_plus_ft_errors(self):
        """Given raw + ft=0
        When filter
        Then first byte of each row is 0 and payload == raw; bad ft raises
        """
        raw = b'\x01\x02\x03\x04'
        filt = apply_filter(raw, 4, 1, 0, 8, filter_type=0)
        self.assertEqual(filt[0], 0)
        self.assertEqual(filt[1:], raw)
        self.assert_raises_value_err('0-4', apply_filter, raw, 4, 1, 0, 8, filter_type=5)
        self.assert_raises_value_err('length', apply_filter, b'abc', 4, 1, 0, 8, 0)

    def test_filter_unfilter_other_ct_bd(self):
        """Given ct=2/6/4 and bd=1/16 cases (bpp >1 or packed)
        When filter+unfilter round
        Then exact match (exercises bpp stride)
        """
        # ct6 bd8 (w=2 h=1 to keep small; rowb=8)
        raw6 = bytes(list(range(8)))
        f6 = apply_filter(raw6, 2, 1, 6, 8, 4)
        self.assertEqual(unfilter(f6, 2, 1, 6, 8), raw6)
        # ct0 bd1 (w=8 rowb=1)
        raw1 = _pack_1bit([1,0,1,0,1,0,1,0], 8)
        f1 = apply_filter(raw1, 8, 1, 0, 1, 1)
        self.assertEqual(unfilter(f1, 8, 1, 0, 1), raw1)


class TestEncoder(RadicalTestCase):
    def test_encode_rgba_validations(self):
        """Given bad pixel structures
        When encode_rgba
        Then ValueError for empty / ragged / bad tuple len
        """
        self.assert_raises_value_err('non-empty', encode_rgba, [])
        self.assert_raises_value_err('same width', encode_rgba, [[(1,2,3,4)], [(1,2,3,4),(5,6,7,8)]])
        self.assert_raises_value_err('4-tuple', encode_rgba, [[(1,2,3)]])

    def test_encode_png_errors(self):
        """Given bad inputs to encode_png
        When called
        Then appropriate ValueError or NotImplemented (interlace)
        """
        ih = {'width':2,'height':1,'bit_depth':8,'color_type':0,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        self.assert_raises_value_err('length', encode_png, ih, b'abc')  # wrong len
        ih3 = dict(ih, color_type=3)
        self.assert_raises_value_err('palette', encode_png, ih3, b'\0\0')
        ih_i = dict(ih, interlace_method=1)
        with self.assertRaises(NotImplementedError):
            encode_png(ih_i, b'\0\0')


class TestDecoder(RadicalTestCase):
    def test_decode_known_minimals_ct0_2_3_6(self):
        """Given the hardcoded 1x1 minimal PNGs (ct 0/2/3/6 bd8)
        When decode_png + decode_rgba (for ct6)
        Then correct fields, data, palette (ct3), and rgba pixels
        """
        # ct0
        p0 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d49484452000000010000000108000000003a7e9b55'
            '0000000a49444154789c63f80f0001010100b138f6140000000049454e44ae426082'
        )
        d0 = decode_png(p0)
        self.assertEqual(d0['width'], 1)
        self.assertEqual(d0['color_type'], 0)
        self.assertEqual(d0['data'], b'\xff')
        self.assertIsNone(d0['palette'])

        # ct3
        p3 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d494844520000000100000001080300000028cb34bb'
            '00000003504c5445ff000019e209370000000a49444154789c636000000002000148afa4710000000049454e44ae426082'
        )
        d3 = decode_png(p3)
        self.assertEqual(d3['color_type'], 3)
        self.assertEqual(d3['palette'], [(255, 0, 0)])

        # ct6 + rgba
        p6 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d49484452000000010000000108060000001f15c489'
            '0000000d49444154789c63606060f80f00010401005fe5c34b0000000049454e44ae426082'
        )
        d6 = decode_png(p6)
        self.assertEqual(d6['color_type'], 6)
        pix = decode_rgba(p6)
        self.assertEqual(pix, [[(0, 0, 0, 255)]])

    def test_decode_rgba_wrong_ct_raises(self):
        """Given non-ct6/8 png (ct2)
        When decode_rgba
        Then ValueError mentioning 6
        """
        p2 = PNG_SIGNATURE + bytes.fromhex(
            '0000000d4948445200000001000000010802000000907753de'
            '0000000c49444154789c63606060000000040001f61738550000000049454e44ae426082'
        )
        self.assert_raises_value_err('6', decode_rgba, p2)

    def test_decode_errors_missing_multi_bad_zlib(self):
        """Given truncated / missing / multi / corrupt-zlib cases
        When decode_png
        Then ValueError as documented
        """
        # missing ihdr (only sig + iend-ish)
        bad = PNG_SIGNATURE + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('IHDR', decode_png, bad)

        # multi ihdr (build two)
        ihb = make_ihdr({'width':1,'height':1,'bit_depth':8,'color_type':0})
        bad2 = PNG_SIGNATURE + make_chunk(b'IHDR', ihb) + make_chunk(b'IHDR', ihb) + make_chunk(b'IDAT', zlib.compress(b'\0')) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('multiple IHDR', decode_png, bad2)

        # ct3 no plte
        ih3 = make_ihdr({'width':1,'height':1,'bit_depth':8,'color_type':3})
        bad3 = PNG_SIGNATURE + make_chunk(b'IHDR', ih3) + make_chunk(b'IDAT', zlib.compress(b'\0')) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('PLTE', decode_png, bad3)

        # zlib fail: corrupt the idat payload
        good_id = zlib.compress(b'\0\xff')
        badz = bytearray(good_id)
        if badz: badz[0] ^= 0xff
        bad4 = PNG_SIGNATURE + make_chunk(b'IHDR', ihb) + make_chunk(b'IDAT', bytes(badz)) + make_chunk(b'IEND', b'')
        self.assert_raises_value_err('zlib', decode_png, bytes(bad4))


class TestFullRoundtrips(RadicalTestCase):
    def test_roundtrips_various_ct_bd_ft_small(self):
        """Given small images across ct 0/2/3/4/6 , bd extremes, all ft
        When encode_png (or rgba) + decode_png/rgba
        Then data + fields roundtrip exactly (via assert_png_roundtrip helper)
        """
        base_ih = lambda ct, bd: {
            'width': 2, 'height': 1,
            'bit_depth': bd, 'color_type': ct,
            'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
        }
        # ct0 bd8
        for ft in range(5):
            with self.subTest(ct=0, bd=8, ft=ft):
                data = b'\x10\x20'
                self.assert_png_roundtrip(base_ih(0, 8), data, filter_type=ft)

        # ct3 bd8 + pal
        pal = [(10,20,30), (40,50,60)]
        data3 = b'\x00\x01'
        self.assert_png_roundtrip(base_ih(3, 8), data3, palette=pal, filter_type=0)

        # ct4 bd8
        data4 = b'\x11\xaa\x22\xbb'
        self.assert_png_roundtrip(base_ih(4, 8), data4, filter_type=2)

        # ct6 bd8 via high level
        pix = [[(1,2,3,255), (4,5,6,128)]]
        self.assert_rgba_roundtrip(pix, filter_type=4)

        # bd16 ct0 (w=2 needs 4 bytes for 16-bit samples)
        ih16 = base_ih(0, 16)
        data16 = b'\x01\x02\x03\x04'
        self.assert_png_roundtrip(ih16, data16, filter_type=0)

        # low bd ct0 (use packers; base w=2 so only 2 samples)
        data1 = _pack_1bit([1,0], 2)
        self.assert_png_roundtrip(base_ih(0, 1), data1, filter_type=1)
        data2 = _pack_2bit([0,3], 2)
        self.assert_png_roundtrip(base_ih(0, 2), data2, filter_type=3)
        data4b = _pack_4bit([15,0], 2)
        self.assert_png_roundtrip(base_ih(0, 4), data4b, filter_type=0)

    def test_1x1_edge_and_rgba(self):
        """Given 1x1 minimal cases
        When encode/decode (png + rgba)
        Then roundtrips and 1x1 decode_rgba works
        """
        p1 = encode_rgba([[(0,0,0,255)]])
        self.assertEqual(decode_rgba(p1), [[(0, 0, 0, 255)]])
        self.assert_png_roundtrip(
            {'width':1,'height':1,'bit_depth':8,'color_type':0,
             'compression_method':0,'filter_method':0,'interlace_method':0},
            b'\x7f'
        )


class TestChunkEdges(RadicalTestCase):
    def test_split_idat_and_extra_chunks(self):
        """Given png constructed with split IDAT + extra ancillary
        When decode_png
        Then succeeds and data matches (decoder joins IDATs, ignores others)
        """
        ih = {'width':2,'height':1,'bit_depth':8,'color_type':0,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        raw = b'\xaa\xbb'
        comp = zlib.compress(b'\0' + raw)  # filter0
        # split into two idat payloads
        mid = len(comp) // 2 or 1
        id1, id2 = comp[:mid], comp[mid:]
        png = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
              make_chunk(b'IDAT', id1) + make_chunk(b'IDAT', id2) + \
              make_chunk(b'tEXt', b'key\0value from radical test') + \
              make_chunk(b'IEND', b'')
        dec = decode_png(png)
        self.assertEqual(dec['data'], raw)
        self.assertEqual(dec['color_type'], 0)

    def test_decode_accepts_path_and_bytes(self):
        """Given a produced png on disk and as bytes/bytearray
        When decode_png on all three forms
        Then same result
        """
        ih = {'width':1,'height':1,'bit_depth':8,'color_type':2,
              'compression_method':0,'filter_method':0,'interlace_method':0}
        # filtered for ct=2 w=1 h=1: 1 filter byte + 3 data bytes
        pngb = PNG_SIGNATURE + make_chunk(b'IHDR', make_ihdr(ih)) + \
               make_chunk(b'IDAT', zlib.compress(b'\0\0\0\0')) + make_chunk(b'IEND', b'')
        # bytes
        d1 = decode_png(pngb)
        # bytearray
        d2 = decode_png(bytearray(pngb))
        # path (write temp)
        tmp = 'tmp_radical_test.png'
        try:
            with open(tmp, 'wb') as f: f.write(pngb)
            d3 = decode_png(tmp)
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
        self.assertEqual(d1['data'], d2['data'])
        self.assertEqual(d1['data'], d3['data'])


class TestIntegration(RadicalTestCase):
    def test_canvas_output_png_round_and_reencode(self):
        """Given the real canvas_output.png (ct6/8 400x300 produced by current code)
        When decode_png + re-encode its data (ft=0) + decode again
        Then dims/ct match + data roundtrips (integration with real file)
        """
        d = decode_png('canvas_output.png')
        self.assertEqual(d['width'], 400)
        self.assertEqual(d['height'], 300)
        self.assertEqual(d['color_type'], 6)
        self.assertEqual(d['bit_depth'], 8)
        self.assertIsNone(d['palette'])

        # re-encode the extracted data (note: canvas used default ft=0)
        ih = {k: d[k] for k in ('width','height','bit_depth','color_type',
                                'compression_method','filter_method','interlace_method')}
        png2 = encode_png(ih, d['data'], filter_type=0)
        d2 = decode_png(png2)
        self.assertEqual(d2['data'], d['data'])


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
        self.assertIn('foo bar', g)
        self.assertIn('do thing', w)
        self.assertIn('expect good', t)

        raw_typ = 'test_foo (TestBar) ... ok\nTestHelpers.test_parse... ... FAIL\n'
        nice = beautify_unittest_output(raw_typ)
        self.assertIn('SCENARIO:', nice)
        self.assertIn('Status:', nice)


# --- Run entry points (the convenient way) ---

def run_all_tests(verbosity=2):
    """Convenient function to run the full radical test suite."""
    runner = RadicalTextTestRunner(verbosity=verbosity)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    return runner.run(suite)


if __name__ == '__main__':
    result = run_all_tests(verbosity=2)
    sys.exit(0 if result.wasSuccessful() else 1)
