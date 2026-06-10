from encoder import encode_png
from decoder import decode_png

from png.baselines import *


bit_depth_for_color_type = {
    0: [1, 2, 4, 8, 16],
    2: [8, 16],
    3: [1, 2, 4, 8],
    4: [8, 16],
    6: [8, 16]
}

generators = {
    0: gen_grey,
    # 2: gen_rgb,
    # 3: gen_indexed,
    4: gen_greya,
    # 6: gen_rgba
}


