import math

import modules.scripts as scripts
import gradio as gr
from PIL import Image

from modules import processing, shared, images, devices
from modules.processing import Processed
from modules.shared import opts, state


class Script(scripts.Script):
    def title(self):
        return "SD upscale (fixed)"

    def show(self, is_img2img):
        # Same as original: only show in img2img tab.
        return is_img2img

    def ui(self, is_img2img):
        """
        Fixed UI definition for SD upscale.

        Fixes applied:
        - Parameter order now matches run() signature exactly
        - Upscaler Radio restored with type="index" to return integer index
        - Clear component ordering for maintainability
        """

        info = gr.HTML(
            "<p style=\"margin-bottom:0.75em\">"
            "Will upscale the image by the selected scale factor; use width and height sliders to set tile size"
            "</p>"
        )

        overlap = gr.Slider(
            minimum=0,
            maximum=256,
            step=16,
            label="Tile overlap",
            value=64,
            elem_id=self.elem_id("overlap"),
        )

        # Fix 1: Restored type="index" to return integer index instead of string name
        upscaler_index = gr.Radio(
            label="Upscaler",
            choices=[x.name for x in shared.sd_upscalers],
            value=shared.sd_upscalers[0].name if shared.sd_upscalers else None,
            type="index",  # FIXED: Now returns index (int), not name (str)
            elem_id=self.elem_id("upscaler_index"),
        )

        scale_factor = gr.Slider(
            minimum=1.0,
            maximum=4.0,
            step=0.05,
            label="Scale Factor",
            value=2.0,
            elem_id=self.elem_id("scale_factor"),
        )

        # Fix 2: Correct parameter order matching run() signature
        # run(p, _, overlap, upscaler_index, scale_factor)
        # Returns: [info, overlap, upscaler_index, scale_factor]
        return [info, overlap, upscaler_index, scale_factor]

    def run(self, p, _, overlap, upscaler_index, scale_factor):
        """
        Fixed run() implementation.

        Fixes applied:
        1) Parameter order now matches ui() return order correctly
        2) Added defensive type check and conversion for upscaler_index
        3) Fixed scale factor behavior when upscaler is "None"
        4) Added validation for overlap vs tile dimensions
        """

        processing.fix_seed(p)

        # Fix 3: Defensive type handling for upscaler_index
        # If somehow a string is passed (e.g., from older code), convert it to index
        if isinstance(upscaler_index, str):
            upscaler_names = [x.name for x in shared.sd_upscalers]
            try:
                upscaler_index = upscaler_names.index(upscaler_index)
            except ValueError:
                # If name not found, default to first upscaler
                upscaler_index = 0
        
        # Ensure upscaler_index is within valid range
        if not isinstance(upscaler_index, int) or upscaler_index < 0 or upscaler_index >= len(shared.sd_upscalers):
            upscaler_index = 0

        upscaler = shared.sd_upscalers[upscaler_index]

        # Fix 4: Validate overlap against tile dimensions
        # Overlap must be less than both tile width and height
        max_safe_overlap = min(p.width, p.height) - 1
        if overlap >= max_safe_overlap:
            print(f"Warning: Overlap {overlap} is too large for tile size {p.width}x{p.height}. Clamping to {max_safe_overlap}.")
            overlap = max(0, max_safe_overlap)

        p.extra_generation_params["SD upscale overlap"] = overlap
        p.extra_generation_params["SD upscale upscaler"] = upscaler.name

        initial_info = None
        seed = p.seed

        init_img = p.init_images[0]
        init_img = images.flatten(init_img, opts.img2img_background_color)

        # Fix 5: Consistent scale factor behavior
        # When upscaler is "None", do NOT apply any scaling
        # Only upscale when a real upscaler is selected
        if upscaler.name != "None":
            img = upscaler.scaler.upscale(init_img, scale_factor, upscaler.data_path)
        else:
            # When "None" is selected, pass through the original image unchanged
            # This is the expected behavior - no upscaling should occur
            img = init_img
            print("Upscaler 'None' selected - bypassing scaling entirely.")

        devices.torch_gc()

        grid = images.split_grid(img, tile_w=p.width, tile_h=p.height, overlap=overlap)

        batch_size = p.batch_size
        upscale_count = p.n_iter
        p.n_iter = 1
        p.do_not_save_grid = True
        p.do_not_save_samples = True

        work = []

        for _y, _h, row in grid.tiles:
            for tiledata in row:
                work.append(tiledata[2])

        batch_count = math.ceil(len(work) / batch_size) if batch_size > 0 else 0
        state.job_count = batch_count * upscale_count

        print(
            f"SD upscaling (fixed) will process a total of {len(work)} images "
            f"tiled as {len(grid.tiles[0][2])}x{len(grid.tiles)} per upscale "
            f"in a total of {state.job_count} batches."
        )

        result_images = []

        for n in range(upscale_count):
            start_seed = seed + n
            p.seed = start_seed

            work_results = []
            for i in range(batch_count):
                p.batch_size = batch_size
                p.init_images = work[i * batch_size:(i + 1) * batch_size]

                state.job = f"Batch {i + 1 + n * batch_count} out of {state.job_count}"
                processed = processing.process_images(p)

                if initial_info is None:
                    initial_info = processed.info

                p.seed = processed.seed + 1
                work_results += processed.images

            image_index = 0
            for _y, _h, row in grid.tiles:
                for tiledata in row:
                    if image_index < len(work_results):
                        tiledata[2] = work_results[image_index]
                    else:
                        tiledata[2] = Image.new("RGB", (p.width, p.height))
                    image_index += 1

            combined_image = images.combine_grid(grid)
            result_images.append(combined_image)

            if opts.samples_save:
                images.save_image(
                    combined_image,
                    p.outpath_samples,
                    "",
                    start_seed,
                    p.prompt,
                    opts.samples_format,
                    info=initial_info,
                    p=p,
                )

        processed = Processed(p, result_images, seed, initial_info)

        return processed
