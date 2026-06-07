"""
RADICAL PNG PERF / BENCH (basic)

Cross-atom perf smoke. GWT on methods. Pure stdlib.
"""
import sys
import time

from png.encoder import encode_png
from png.decoder import decode_png
from png.filters import apply_filter
from png.unfilter import unfilter
from png.synth_png import make_synthetic_png
from png.synth_data import make_synthetic_image_data
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests


class TestPerfEncodeDecode(PngTestCase):
    def test_basic_perf_sizes_ct0_and_ct6(self):
        """Given the make_synthetic_png helper (on-demand different file sizes)
        When timing encode_png + decode_png on several (w,h) for ct0/6 bd8
        Then all roundtrip + we log elapsed (basic smoke of size scaling)
        """
        cases = [(1, 1), (8, 4), (16, 8), (32, 16)]
        for w, h in cases:
            for ct in (0, 6):
                with self.subt(w=w, h=h, ct=ct):
                    png = make_synthetic_png(w, h, ct, 8)
                    t0 = time.perf_counter()
                    d = decode_png(png)
                    t1 = time.perf_counter()
                    ih = {k: d[k] for k in ('width', 'height', 'bit_depth', 'color_type',
                                            'compression_method', 'filter_method', 'interlace_method')}
                    p2 = encode_png(ih, d['data'], filter_type=0)
                    t2 = time.perf_counter()
                    self.equa(d['data'], decode_png(p2)['data'])
                    dt_dec = (t1 - t0) * 1000
                    dt_enc = (t2 - t1) * 1000
                    print(f'    size {w}x{h} ct{ct}: decode {dt_dec:.2f}ms '
                          f'encode {dt_enc:.2f}ms  png_len={len(png)}')

    def test_perf_filter_unfilter_sizes(self):
        """Given make_synthetic_image_data + apply/unfilter
        When timing filter+unfilter round for a couple sizes / fts
        Then recon matches + timings reported (exercises the hot path)
        """
        cases = [(16, 8, 0, 8), (32, 16, 6, 8)]
        for w, h, ct, bd in cases:
            raw = make_synthetic_image_data(w, h, ct, bd)
            for ft in (0, 4):
                with self.subt(w=w, h=h, ct=ct, ft=ft):
                    t0 = time.perf_counter()
                    filt = apply_filter(raw, w, h, ct, bd, filter_type=ft)
                    recon = unfilter(filt, w, h, ct, bd)
                    t1 = time.perf_counter()
                    self.equa(recon, raw)
                    dt = (t1 - t0) * 1000
                    print(f'    filter+unfilter {w}x{h} ct{ct} ft{ft}: {dt:.2f}ms')


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
