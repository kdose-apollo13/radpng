"""
baselines
synthetic deterministic image data generators for the full PNG color type /
bit depth / filter matrix.

Public API: the five gen_* functions. Each takes (width, height, bit_depth)
and returns the exact unfiltered scanline bytes (plus palette for indexed).

These are the canonical source for "representative raw data" used by
cross-atom perf/matrix smokes (ztest_perf) and certain unit tests.

The facility is intentionally a modest cluster (power-law "unified semantic
facility") so a newcomer can point to "the baselines" and find everything
together, while each generator remains a tiny readable atom.
"""

from png.baselines.grey import gen_grey
from png.baselines.greya import gen_greya
from png.baselines.rgb import gen_rgb
from png.baselines.rgba import gen_rgba
from png.baselines.indexed import gen_indexed

__all__ = [
    'gen_grey',
    'gen_greya',
    'gen_rgb',
    'gen_rgba',
    'gen_indexed',
]
