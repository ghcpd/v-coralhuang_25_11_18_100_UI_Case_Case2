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
        
        Fixes:
        - Parameter order matches run() signature: [info, overlap, upscaler_index, scale_factor]
        - Upscaler Radio uses type="index" to return integer index instead of string name
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

        scale_factor = gr.Slider(
            minimum=1.0,
            maximum=4.0,
            step=0.05,
            label="Scale Factor",
            value=2.0,
            elem_id=self.elem_id("scale_factor"),
        )

        # Fix 1: Restore type="index" so Radio returns integer index, not string name
        upscaler_index = gr.Radio(
            label="Upscaler",
            choices=[x.name for x in shared.sd_upscalers],
            value=shared.sd_upscalers[0].name if shared.sd_upscalers else None,
            type="index",
            elem_id=self.elem_id("upscaler_index"),
        )

        # Fix 2: Correct parameter order to match run() signature
        # Returns: [info, overlap, upscaler_index, scale_factor]
        return [info, overlap, upscaler_index, scale_factor]

    def run(self, p, _, overlap, upscaler_index, scale_factor):
        """
        Fixed run() implementation.
        
        Fixes:
        1) Parameter order now matches ui() return order
        2) Added defensive type check for upscaler_index (handles both int and string)
        3) When upscaler is "None", skip scaling entirely (no unexpected resize)
        4) Added validation/clamping for overlap vs tile size
        """

        processing.fix_seed(p)

        # Fix 2: Defensive type check - handle both integer index and string name
        # This provides robustness even if UI returns a string
        if isinstance(upscaler_index, str):
            # Find upscaler by name
            upscaler = None
            for idx, upscaler_obj in enumerate(shared.sd_upscalers):
                if upscaler_obj.name == upscaler_index:
                    upscaler = upscaler_obj
                    break
            if upscaler is None:
                # Fallback to first upscaler if name not found
                upscaler = shared.sd_upscalers[0] if shared.sd_upscalers else None
        else:
            # Use as integer index
            if upscaler_index < 0 or upscaler_index >= len(shared.sd_upscalers):
                # Fallback to first upscaler if index out of range
                upscaler_index = 0
            upscaler = shared.sd_upscalers[upscaler_index] if shared.sd_upscalers else None

        if upscaler is None:
            raise ValueError("No upscaler available")

        # Fix 4: Validate and clamp overlap to prevent it from being >= tile dimensions
        # This prevents pathological behavior in images.split_grid
        max_overlap = min(p.width, p.height) - 1
        if overlap >= max_overlap:
            overlap = max(0, max_overlap)
            print(f"Warning: Tile overlap clamped to {overlap} (tile size: {p.width}x{p.height})")

        p.extra_generation_params["SD upscale overlap"] = overlap
        p.extra_generation_params["SD upscale upscaler"] = upscaler.name

        initial_info = None
        seed = p.seed

        init_img = p.init_images[0]
        init_img = images.flatten(init_img, opts.img2img_background_color)

        # Fix 3: When upscaler is "None", skip scaling entirely
        # This matches user expectation that "None" means no upscaling
        if upscaler.name != "None":
            img = upscaler.scaler.upscale(init_img, scale_factor, upscaler.data_path)
        else:
            # When "None" is selected, return the original image without any scaling
            img = init_img

        devices.torch_gc()

        # Overlap is now validated/clamped above, so split_grid should work safely
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
            f"SD upscaling will process a total of {len(work)} images "
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


