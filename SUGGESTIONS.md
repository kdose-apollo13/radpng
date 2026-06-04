# Suggestions & Refinements from Radical PNG Tests

Companion to `test_radical_png.py`. One goal of writing (and running) the tests was to
suggest improvements or refinements to consider in the code.

All tests pass against the current implementation. These are forward-looking observations
surfaced by exercising every public function, all ct/bd/filter matrix corners, error paths,
chunk construction, low-level symmetry, real files (canvas_output.png), and integration.

Tone: appreciative of the radical minimal / pure-stdlib / tiny-file style. Suggestions are
concrete and optional.

## Observations from Test Authoring
- The lib is impressively small, correct for the supported subset, and very explicit. Roundtrips
  (filter/unfilter, encode/decode, make/parse) are rock-solid for the exercised paths.
- Demos in `__main__` already covered the happy 8-bit ct0 + 5 filters case well; tests extended
  that to the full matrix (ct 0/2/3/4/6, bd 1/2/4/8/16, all ft) + negatives + chunk edges.
- Writing the GWT-structured tests + custom runner made gaps (and strengths) obvious immediately.
- The custom `Radical*` wrappers + `parse_gwt` / `beautify...` are themselves tested (TestHelpers)
  and produce the required informative per-test output (3 sensible lines).

## Refinements & Improvements to Consider
- Low bit-depth (1/2/4) and 16-bit usability (TestFullRoundtrips + internal `_pack_*` helpers):
  Lib correctly handles packed bytes via `row_bytes`/`bpp` + bytewise filters (per PNG spec
  "filters on bytes, not pixels"), but callers must pack samples themselves for `encode_png`
  on bd<8 (and use 2-byte big-endian for 16-bit). Tests had to implement tiny MSB-first packers.
  Suggestion: consider adding small pure helpers (`pack_gray1`, `pack_indexed2` etc + unpack
  equivalents) in a new or existing module (e.g. next to row_bytes)? Would make low-bd
  first-class without growing the encoder. Or at minimum document in `encode_png` docstring:
  "data must be pre-packed scanline bytes per PNG rules for the ct/bd".

- Logic duplication in sample counts (row_bytes.py:20, bpp.py:18, ihdr.py:40 `allowed`):
  Three places encode "ct 0/3 -> 1 sample, ct2->3, ct4->2, ct6->4" (plus bd scaling).
  A tiny shared `_samples_per_pixel(ct)` (private) would dedup; current explicitness is
  very "radical" (no hidden magic) but a private helper + reuse in the three spots is a
  low-risk refinement that would also make future ct additions safer.

- Chunk order leniency in decoder (TestDecoder + TestChunkEdges):
  `decode_png` collects IHDR/PLTE/IDAT without enforcing PNG chunk ordering rules
  (IHDR must appear first, PLTE before IDAT for ct=3, etc.). Current succeeds on some
  misordered constructs (as long as the required pieces are present before IEND).
  Tests explicitly cover split IDAT + extra ancillary (which works). Consider adding
  light order validation (or at least warnings) for better spec conformance in the future?

- Filter choice surface (TestFullRoundtrips + encoder):
  `encode_png` / `encode_rgba` require the caller to pick a uniform `filter_type` (0-4);
  0 is always valid and simplest. No per-row or "best filter" auto-selection.
  This is a deliberate radical/minimal choice (keeps encoder thin). Suggestion: the
  module doc + README-ish comments could note that real-world encoders often adapt
  per scanline for size; here the user-specified approach is intentional and sufficient.

- `decode_rgba` is narrow (only ct=6/bd=8) while `decode_png` is general:
  This is documented and tested. If a future "decode any to rgba8 with scaling" is desired,
  it would be a bigger addition (sample depth scaling, ct conversion). Tests highlight
  the current boundary clearly via the ValueError path.

- Error messages are mostly excellent (include got/expected, specific). The zlib wrapper
  is a bit generic; minor polish opportunity only.

- `iter_chunks` + `make_chunk` + crc are solid and fully exercised (bad crc, trunc, split IDAT).
  No changes suggested.

- No adam7 support (raises NotImpl in en/de) is correctly tested; parse_ihdr accepts
  interlace=1 (as it should). If Adam7 ever added, filter/unfilter + row_bytes would
  need significant per-pass changes. Not a current gap.

## Coverage Notes (what tests now exercise that demos didn't)
- All 5 color types (incl ct=4 gray+alpha).
- bd=1,2,4,16 (demos were 8-bit only).
- `encode_png` direct for non-rgba cts + palette roundtrips.
- Every documented `raise ValueError` / `NotImplementedError` site has a test.
- `make_*` symmetry + error cases for ihdr/plte (demos had some but not all).
- Split IDAT (multiple consecutive), extra ancillary chunks (ignored), bad CRC, zlib corrupt,
  missing/multi IHDR/PLTE/IDAT, truncations, path vs bytes/bytearray for decode.
- Real file `canvas_output.png` (400x300 ct6/8) + re-encode roundtrip of its data.
- Self-tests of the GWT parser + beautify helper.
- bpp/row_bytes full matrix + invalid ct.
- paeth + filter/unfilter on bpp>1 and packed low-bd cases.

~22 focused test methods (many with subTest) give per-test GWT output that is readable
and pinpoints the scenario (Given/When/Then) when something breaks.

## Intentional Scope (explicitly not tested / not suggested as missing)
- Huge images, perf, memory (the pure-py loops are fine for the sizes that matter here).
- tRNS, gamma, color management, text, other ancillary (decoder correctly ignores; iter_chunks
  yields them for anyone who wants to walk full structure).
- Writing interlaced / reading Adam7 (NotImpl is the current contract).
- Auto filter selection or per-row filters.
- Any non-stdlib (no PIL verification of produced PNGs; we rely on our own decode roundtrips
  + known minimal vectors + construction via make_chunk).

## How to Use These Suggestions
- Good source of "next radical increment" ideas if extending the lib.
- The test file itself (with its packers, GWT, runner) can stay as-is even if lib gains
  helpers; the packers are deliberately test-only to keep lib surface unchanged.
- Re-run `python test_radical_png.py` after any future lib change to ensure the beauty
  and coverage remain.

Written as part of the testing effort (pure stdlib, no deps).
