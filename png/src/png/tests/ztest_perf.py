"""
RADICAL PNG PERF / BENCH (basic)

Cross-atom perf smoke. GWT on methods. Pure stdlib.
"""
import sys

from png.encoder import encode_png
from png.decoder import decode_png
from png.filters import apply_filter
from png.unfilter import unfilter
from png.synth_png import make_synthetic_png
from png.synth_data import make_synthetic_image_data
from png.tests.png_test_case import PngTestCase
from rlab.run_suite import run_module_tests

from rlab.perf_scale import scale
from rlab.perf_report import format_perf_report


class TestPerfEncodeDecode(PngTestCase):
    def test_basic_perf_sizes_ct0_and_ct6(self):
        """Given the make_synthetic_png helper (on-demand different file sizes)
        When timing encode_png + decode_png on several (w,h) for ct0/6 bd8
        Then all roundtrip + we log elapsed (basic smoke of size scaling)
        """
        for ct in (0, 6):
            with self.subt(ct=ct):
                def builder(wh):
                    w, h = wh
                    png = make_synthetic_png(w, h, ct, 8)
                    return (png,), {}

                def encdec_round(pngb):
                    d = decode_png(pngb)
                    ih = {k: d[k] for k in ('width', 'height', 'bit_depth', 'color_type',
                                            'compression_method', 'filter_method', 'interlace_method')}
                    p2 = encode_png(ih, d['data'], filter_type=0)
                    # roundtrip oracle still exercised for every measurement (Then clause)
                    self.equa(d['data'], decode_png(p2)['data'])
                    return p2

                # modest growth for encode/decode (zlib cost); powers give clear trend
                sizes = [(2**k, 2**(k-1) or 1) for k in range(2, 7)]  # 4x2 ... 64x32
                res = scale(encdec_round, sizes, arg_builder=builder)
                print(format_perf_report(res, title=f'encode+decode ct{ct} (roundtrips asserted)'))

    def test_perf_filter_unfilter_sizes(self):
        """Given make_synthetic_image_data + apply/unfilter
        When timing filter+unfilter round for a couple sizes / fts
        Then recon matches + timings reported (exercises the hot path)
        """
        # larger sizes for filter hot path (pure per-pixel, O(n) expected, visible trend)
        base_sizes = [(2**k, 2**(k-1) or 1) for k in range(4, 9)]  # 16x8 ... 256x128
        for ct, bd in ((0, 8), (6, 8)):
            for ft in (0, 4):
                with self.subt(ct=ct, bd=bd, ft=ft):
                    def builder(wh):
                        w, h = wh
                        raw = make_synthetic_image_data(w, h, ct, bd)
                        return (raw, w, h, ct, bd, ft), {}

                    def filter_roundtrip(raw, w, h, ct, bd, ft):
                        filt = apply_filter(raw, w, h, ct, bd, filter_type=ft)
                        recon = unfilter(filt, w, h, ct, bd)
                        # recon oracle (Then) for every timed iteration
                        self.equa(recon, raw)
                        return recon

                    res = scale(filter_roundtrip, base_sizes, arg_builder=builder, repeats=2)
                    print(format_perf_report(res, title=f'filter+unfilter ct{ct} bd{bd} ft{ft}'))


if __name__ == '__main__':
    result = run_module_tests(sys.modules[__name__])
    sys.exit(0 if result.wasSuccessful() else 1)
