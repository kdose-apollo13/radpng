"""
RADICAL PNG TEST: interlace (Adam7)

One test file per atomic (interlace.py). GWT on every method.
Pure stdlib only.
"""
import sys

from png.interlace import (
    PASS_SPECS,
    compute_pass_dimensions,
    get_adam7_pass_dimensions,
    get_pass_raw,
    place_pass_raw,
    build_adam7_filtered,
    extract_from_adam7_filtered,
)
from png.row_bytes import get_row_bytes
from rlab.test_case import RadicalTestCase
from rlab.run_suite import run_module_tests


class TestInterlaceAdam7(RadicalTestCase):
    def test_pass_specs_has_exactly_seven_entries(self):
        """Given the Adam7 definition
        When inspecting PASS_SPECS
        Then there are exactly the 7 passes in the correct order
        """
        self.equa(len(PASS_SPECS), 7)
        # first and last are the well-known extremes
        self.equa(PASS_SPECS[0], (0, 0, 8, 8))
        self.equa(PASS_SPECS[6], (0, 1, 1, 2))

    def test_compute_pass_dimensions_zero_when_start_beyond_image(self):
        """Given an image smaller than a pass start offset
        When compute_pass_dimensions
        Then the pass reports 0 for the affected dimension(s)
        """
        self.equa(compute_pass_dimensions(3, 3, 4, 0, 8, 8), (0, 0))
        self.equa(compute_pass_dimensions(3, 3, 0, 4, 8, 8), (0, 0))
        self.equa(compute_pass_dimensions(1, 1, 0, 0, 8, 8), (1, 1))

    def test_get_adam7_pass_dimensions_known_cases(self):
        """Given representative image sizes (1x1, 8x8, 9x9, 4x4)
        When get_adam7_pass_dimensions
        Then the 7 (pw, ph) pairs match the expected Adam7 sampling
        """
        self.equa(get_adam7_pass_dimensions(1, 1),
                  [(1, 1), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0), (0, 0)])
        d8 = get_adam7_pass_dimensions(8, 8)
        self.equa(d8[0], (1, 1))
        # pass 7 (step 1x2): 8 cols, 4 rows for an 8x8 image
        self.equa(d8[6], (8, 4))
        d9 = get_adam7_pass_dimensions(9, 9)
        # pass 7 (y_start=1, step=2): y=1,3,5,7 → 4 rows; x-step 1 → 9 cols
        self.equa(d9[6], (9, 4))

    def test_gather_place_raw_identity_ct6(self):
        """Given a ct6 progressive raw buffer (from baseline generator)
        When extracting every Adam7 pass raw and placing them back
        Then the reconstructed buffer is identical to the original
        """
        from png.baselines import gen_rgba
        for (w, h) in [(1, 1), (4, 2), (8, 8), (9, 5)]:
            data = gen_rgba(w, h, 8)
            buf = bytearray(len(data))
            for (xs, ys, xstep, ystep) in PASS_SPECS:
                p = get_pass_raw(data, w, h, 6, 8, xs, ys, xstep, ystep)
                place_pass_raw(buf, p, w, h, 6, 8, xs, ys, xstep, ystep)
            self.equa(bytes(buf), bytes(data))

    def test_gather_place_raw_identity_low_bit_depth(self):
        """Given ct0 / ct3 raw data for the sub-byte bit depths (1/2/4)
        When round-tripping through all Adam7 passes (gather + place)
        Then data is bit-for-bit identical (packing is preserved)
        """
        from png.baselines.pack import pack_row
        for ct, bd in [(0, 1), (0, 2), (0, 4), (3, 4)]:
            # tiny but large enough to hit several passes
            w, h = 8, 4
            spp = 1
            # make a simple ascending sample pattern
            samples = [(x + y * 7) & ((1 << bd) - 1) for y in range(h) for x in range(w)]
            data = bytearray()
            for y in range(h):
                row_s = samples[y * w:(y + 1) * w]
                data.extend(pack_row(row_s, bd))
            buf = bytearray(len(data))
            for (xs, ys, xstep, ystep) in PASS_SPECS:
                p = get_pass_raw(data, w, h, ct, bd, xs, ys, xstep, ystep)
                place_pass_raw(buf, p, w, h, ct, bd, xs, ys, xstep, ystep)
            self.equa(bytes(buf), bytes(data))

    def test_build_and_extract_adam7_filtered_roundtrip(self):
        """Given progressive raw data for several ct/bd
        When build_adam7_filtered then extract_from_adam7_filtered
        Then we recover the exact original progressive data
        """
        from png.baselines import gen_grey, gen_rgb, gen_rgba, gen_indexed
        cases = [
            (0, 8, lambda w, h, bd: gen_grey(w, h, bd)),
            (2, 8, lambda w, h, bd: gen_rgb(w, h, bd)),
            (6, 8, lambda w, h, bd: gen_rgba(w, h, bd)),
            (3, 4, lambda w, h, bd: gen_indexed(w, h, bd)[0]),
        ]
        for ct, bd, gen in cases:
            for (w, h) in [(2, 2), (8, 8), (5, 3)]:
                if ct == 3:
                    raw = gen(w, h, bd)
                else:
                    raw = gen(w, h, bd)
                for ft in (0, 4):
                    filt = build_adam7_filtered(raw, w, h, ct, bd, filter_type=ft)
                    recon = extract_from_adam7_filtered(filt, w, h, ct, bd)
                    self.equa(bytes(recon), bytes(raw))

    def test_public_encode_decode_roundtrip_with_interlace_1(self):
        """Given a valid ihdr dict with interlace_method=1 and matching progressive data
        When encode_png then decode_png
        Then the returned dict has interlace_method=1 and the progressive data roundtrips
        """
        from png.encoder import encode_png
        from png.decoder import decode_png
        from png.baselines import gen_rgba, gen_grey

        for (w, h, ct, bd) in [(1, 1, 6, 8), (4, 4, 6, 8), (3, 2, 6, 8)]:
            data = gen_rgba(w, h, bd)  # ct6 rgba data matches the ihdr we build below
            ih = {
                'width': w, 'height': h,
                'bit_depth': bd, 'color_type': ct,
                'compression_method': 0, 'filter_method': 0, 'interlace_method': 1,
            }
            png_bytes = encode_png(ih, bytes(data), filter_type=0)
            dec = decode_png(png_bytes)
            self.equa(dec['interlace_method'], 1)
            self.equa(dec['width'], w)
            self.equa(dec['height'], h)
            self.equa(dec['data'], bytes(data))


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
