"""
filter method and compression method always 0

greyscale [Y, ...]
truecolor [(R, G, B), ...]
indexed-color [I, ...]
greyscale + alpha [(Y, A), ...]
truecolor + alpha [(R, G, B, A), ...]
"""


if __name__ == '__main__':
    # The baselines subpackage provides one coherent facility for synthetic
    # PNG sample data across the full ct/bd matrix. Import the public generators
    # and exercise them (this demo is intentionally self-contained and runnable
    # with the standard project PYTHONPATH).
    from png.baselines import (
        gen_grey, gen_greya, gen_rgb, gen_rgba, gen_indexed,
    )
    from png.encoder import encode_png
    from png.decoder import decode_png
    
    sizes = [(2, 2), (10, 10), (31, 31), (50, 50)]
    
    bit_depth_for_color_type = {
        0: [1, 2, 4, 8, 16],
        2: [8, 16],
        3: [1, 2, 4, 8],
        4: [8, 16],
        6: [8, 16]
    }
    
    generators = {
        0: gen_grey,
        2: gen_rgb,
        3: gen_indexed,
        4: gen_greya,
        6: gen_rgba
    }

    print('=== Full Matrix Test (via png.baselines public API) ===')
    tests_run = 0

    for (w, h) in sizes:
        for ct, depths in bit_depth_for_color_type.items():
            for bd in depths:
                for ft in [0, 1, 2, 3, 4]:
                    
                    # 1. Generate the raw data for the current configuration
                    if ct == 3:
                        data, palette = generators[ct](w, h, bd)
                    else:
                        data = generators[ct](w, h, bd)
                        palette = None
                        
                    # 2. Build the exact IHDR dict your encoder expects
                    ihdr = {
                        'width': w, 
                        'height': h,
                        'bit_depth': bd, 
                        'color_type': ct,
                        'compression_method': 0, 
                        'filter_method': 0, 
                        'interlace_method': 0
                    }
                    
                    # 3. Fire it through encode_png
                    try:
                        pngb = encode_png(ihdr, bytes(data), palette=palette, filter_type=ft)
                        
                        # 4. Optional: Pipe it back into your decoder
                        back = decode_png(pngb)
                        # assert back['width'] == w and back['data'] == bytes(data)
                        
                        tests_run += 1
                        
                        # Optional: write out to disk to inspect the gradients visually!
                        with open(f"test_{w}x{h}_ct{ct}_bd{bd}_ft{ft}.png", "wb") as f:
                            f.write(pngb)
                            
                    except Exception as e:
                        print(f"FAILED: {w}x{h} CT:{ct} BD:{bd} FT:{ft} -> {e}")

    print(f'Successfully ran {tests_run} matrix combinations.')

