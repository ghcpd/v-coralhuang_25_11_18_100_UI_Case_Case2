import math

import modules.scripts as scripts
import gradio as gr
from PIL import Image

from modules import processing, shared, images, devices
from modules.processing import Processed
from modules.shared import opts, state


class Script(scripts.Script):
    def title(self):
        return "SD upscale (buggy test case)"

    def show(self, is_img2img):
        # Same as original: only show in img2img tab.
        # The main bugs in this test case are UI wiring / value handling bugs in ui() and run().
        return is_img2img

    def ui(self, is_img2img):
        """
        Intentionally buggy UI definition for SD upscale.

        Bugs introduced here:
        - Parameter order mismatch vs run():
          ui() returns [info, upscaler_index, overlap, scale_factor],
          but run(p, _, overlap, upscaler_index, scale_factor) assumes
          [info, overlap, upscaler_index, scale_factor].
          This swaps overlap and upscaler_index at runtime.
        - Upscaler Radio no longer uses type="index",
          so it returns a string (the upscaler name), but run()
          treats the corresponding argument as an index.
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

        # Bug 1: removed type="index"
        # This makes the Radio return the selected upscaler NAME (string),
        # not its index, but run() still expects an index.
        upscaler_index = gr.Radio(
            label="Upscaler",
            choices=[x.name for x in shared.sd_upscalers],
            value=shared.sd_upscalers[0].name if shared.sd_upscalers else None,
            elem_id=self.elem_id("upscaler_index"),
        )

        # Bug 2: parameter order mismatch with run().
        # Original safe order would be: [info, overlap, upscaler_index, scale_factor]
        # Here we deliberately swap upscaler_index and overlap.
        return [info, upscaler_index, overlap, scale_factor]

    def run(self, p, _, overlap, upscaler_index, scale_factor):
        """
        Intentionally buggy run() implementation.

        Bugs combined here:

        1) Parameter order mismatch:
           - ui() returns [info, upscaler_index, overlap, scale_factor]
           - run() expects (_, overlap, upscaler_index, scale_factor)
           At runtime:
             overlap        <- actually receives the value of upscaler_index from UI
             upscaler_index <- actually receives the value of overlap from UI

        2) Upscaler type mismatch:
           - ui() Radio returns a STRING upscaler name.
           - run() no longer has a defensive isinstance(upscaler_index, str) check.
           - It uses 'upscaler_index' as a list index directly:
               upscaler = shared.sd_upscalers[upscaler_index]
             which will break when upscaler_index is a string or a float.

        3) Scale factor behavior inconsistent with user expectation:
           - When upscaler is "None", we still apply a naive resize with scale_factor,
             even though users might expect "None" to disable scaling altogether.
        """

        # In the original implementation, there was a defensive check:
        #   if isinstance(upscaler_index, str):
        #       ...
        # We intentionally remove it to create a UI-value/logic mismatch bug.
        # Now upscaler_index is used directly as an index, even though it is
        # actually the "overlap" value due to parameter order mismatch.
        processing.fix_seed(p)

        # Bug: due to parameter order mismatch and missing type guard,
        # the following line may raise or behave incorrectly.
        upscaler = shared.sd_upscalers[upscaler_index]

        # Note: 'overlap' here is actually the upscaler value from UI,
        # not the numeric overlap slider value.
        p.extra_generation_params["SD upscale overlap"] = overlap
        p.extra_generation_params["SD upscale upscaler"] = upscaler.name

        initial_info = None
        seed = p.seed

        init_img = p.init_images[0]
        init_img = images.flatten(init_img, opts.img2img_background_color)

        # Bug 3: even when upscaler is "None", scale_factor is still applied
        # via a naive Image.resize with NEAREST.
        # This contradicts the UI expectations that Scale Factor is driven by
        # the upscaler; with "None" users may expect no scaling to happen.
        if upscaler.name != "None":
            img = upscaler.scaler.upscale(init_img, scale_factor, upscaler.data_path)
        else:
            # Intentional buggy behavior: still resize the image by scale_factor
            # using a low-quality nearest-neighbor resampling.
            new_w = max(1, int(init_img.width * scale_factor))
            new_h = max(1, int(init_img.height * scale_factor))
            img = init_img.resize((new_w, new_h), resample=Image.NEAREST)

        devices.torch_gc()

        # Bug 4 (UI constraint missing, left as-is on purpose):
        # overlap slider allows values up to 256 with no validation versus p.width / p.height.
        # For small tile sizes, overlap may be >= tile dimension, causing poor behavior
        # or downstream errors in images.split_grid.
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
            f"SD upscaling (buggy) will process a total of {len(work)} images "
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
