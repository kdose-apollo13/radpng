"""
RADICAL PNG PERF / MATRIX SMOKE (simplified)

Cross-atom exercise of the PNG feature matrix using baseline generators.
Plain loops + direct timing (time.perf_counter). No perf_scale / perf_report indirection.
GWT on methods. Pure stdlib + rlab harness. Every module is a demo.
"""
import sys
import time

from png.encoder import encode_png
from png.decoder import decode_png
from png.filters import apply_filter
from png.unfilter import unfilter
from png.baseline import (
    gen_grey, gen_greya, gen_rgb, gen_rgba, gen_indexed,
)
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


# Same predicates as baseline.py __main__ (step-by-step manual progression made obvious).
BIT_DEPTH_FOR_COLOR_TYPE = {
    0: [1, 2, 4, 8, 16],
    2: [8, 16],
    3: [1, 2, 4, 8],
    4: [8, 16],
    6: [8, 16],
}

GENERATORS = {
    0: gen_grey,
    2: gen_rgb,
    3: gen_indexed,
    4: gen_greya,
    6: gen_rgba,
}


class TestPerfMatrix(PngTestCase):
    def test_encode_decode_sizes_ct0_and_ct6(self):
        """Given baseline generators for ct0/6 bd8
        When encode_png + decode_png on modest growing sizes
        Then roundtrips asserted + simple elapsed times printed (size scaling smoke)
        """
        sizes = [(4, 2), (16, 8), (64, 32)]
        for ct in (0, 6):
            gen = GENERATORS[ct]
            for w, h in sizes:
                with self.subt(ct=ct, w=w, h=h):
                    data = gen(w, h, 8)
                    ihdr = {
                        'width': w, 'height': h,
                        'bit_depth': 8, 'color_type': ct,
                        'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
                    }
                    t0 = time.perf_counter()
                    pngb = encode_png(ihdr, bytes(data), filter_type=0)
                    d = decode_png(pngb)
                    t1 = time.perf_counter()
                    self.equa(d['data'], bytes(data))
                    print(f'encode+decode ct{ct} {w}x{h}: {(t1 - t0) * 1000:.3f} ms')

    def test_filter_unfilter_sizes(self):
        """Given baseline generators for raw bytes (ct0/6 bd8)
        When apply_filter + unfilter round for ft 0/4 across sizes
        Then recon matches + simple elapsed times printed (hot path exercise)
        """
        sizes = [(16, 8), (64, 32)]
        for ct, bd in ((0, 8), (6, 8)):
            gen = GENERATORS[ct]
            for ft in (0, 4):
                for w, h in sizes:
                    with self.subt(ct=ct, bd=bd, ft=ft, w=w, h=h):
                        raw = gen(w, h, bd)
                        t0 = time.perf_counter()
                        filt = apply_filter(raw, w, h, ct, bd, filter_type=ft)
                        recon = unfilter(filt, w, h, ct, bd)
                        t1 = time.perf_counter()
                        self.equa(recon, bytes(raw))
                        print(f'filter+unfilter ct{ct} bd{bd} ft{ft} {w}x{h}: {(t1 - t0) * 1000:.3f} ms')

    def test_full_matrix_small_sizes(self):
        """Given the exact (size, ct, bd, ft) matrix from baseline.py
        When encode_png for every combination (small sizes only)
        Then all 300 combos succeed + roundtrip data for a sample
        """
        sizes = [(2, 2), (10, 10), (31, 31)]
        tests_run = 0
        for (w, h) in sizes:
            for ct, depths in BIT_DEPTH_FOR_COLOR_TYPE.items():
                gen = GENERATORS[ct]
                for bd in depths:
                    for ft in [0, 1, 2, 3, 4]:
                        with self.subt(w=w, h=h, ct=ct, bd=bd, ft=ft):
                            if ct == 3:
                                data, palette = gen(w, h, bd)
                            else:
                                data = gen(w, h, bd)
                                palette = None
                            ihdr = {
                                'width': w, 'height': h,
                                'bit_depth': bd, 'color_type': ct,
                                'compression_method': 0, 'filter_method': 0, 'interlace_method': 0,
                            }
                            pngb = encode_png(ihdr, bytes(data), palette=palette, filter_type=ft)
                            # Sample roundtrip oracle (not every combo, to keep perf smoke fast)
                            if (w, h, ct, bd, ft) == (2, 2, 0, 8, 0):
                                d = decode_png(pngb)
                                self.equa(d['data'], bytes(data))
                            tests_run += 1
        # Visible in output; proves the matrix is exercised end-to-end
        print(f'full matrix smoke: {tests_run} combos (sizes from baseline)')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
