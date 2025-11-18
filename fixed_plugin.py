from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image


@dataclass
class Slider:
    minimum: float
    maximum: float
    step: float
    label: str
    value: float
    elem_id: str


@dataclass
class Radio:
    label: str
    choices: List[str]
    value: int
    elem_id: str
    type: str = "index"


@dataclass
class Upscaler:
    name: str
    scaler: Optional[Any]
    data_path: str = ""


class DummyScaler:
    def upscale(self, image: Image.Image, scale_factor: float, data_path: str) -> Image.Image:
        target_w = max(1, int(image.width * scale_factor))
        target_h = max(1, int(image.height * scale_factor))
        return image.resize((target_w, target_h), Image.LANCZOS)


DEFAULT_UPSCALERS: List[Upscaler] = [
    Upscaler(name="None", scaler=None),
    Upscaler(name="MockUpscaler", scaler=DummyScaler(), data_path="/mock/path"),
]


def elem_id(name: str) -> str:
    return f"fixed_plugin_{name}"


def ui() -> Tuple[str, Slider, Radio, Slider]:
    info = (
        "Will upscale the image using the selected scale factor. "
        "Set tile size via width/height sliders and keep overlap smaller than a tile."
    )

    overlap = Slider(
        minimum=0,
        maximum=256,
        step=16,
        label="Tile overlap",
        value=64,
        elem_id=elem_id("overlap"),
    )

    scale_factor = Slider(
        minimum=1.0,
        maximum=4.0,
        step=0.05,
        label="Scale Factor",
        value=2.0,
        elem_id=elem_id("scale_factor"),
    )

    upscaler_radio = Radio(
        label="Upscaler",
        choices=[upscaler.name for upscaler in DEFAULT_UPSCALERS],
        value=0,
        elem_id=elem_id("upscaler_index"),
    )

    return info, overlap, upscaler_radio, scale_factor


@dataclass
class ProcessParams:
    width: int
    height: int
    init_images: List[Image.Image]
    batch_size: int = 1
    n_iter: int = 1
    seed: int = 42
    prompt: str = ""
    extra_generation_params: Dict[str, Any] = field(default_factory=dict)


class FixedPluginError(ValueError):
    pass


def validate_overlap(overlap: float, tile_w: int, tile_h: int) -> int:
    if tile_w <= 0 or tile_h <= 0:
        return 0

    max_valid = max(0, min(tile_w, tile_h) - 1)
    return max(0, min(int(overlap), max_valid))


def run(
    p: ProcessParams,
    _info: Any,
    overlap: float,
    upscaler_index: int,
    scale_factor: float,
    upscalers: Optional[List[Upscaler]] = None,
) -> Dict[str, Any]:
    if upscalers is None:
        upscalers = DEFAULT_UPSCALERS

    if not isinstance(upscaler_index, int):
        raise FixedPluginError("Upscaler index must be an integer.")

    if upscaler_index < 0 or upscaler_index >= len(upscalers):
        raise FixedPluginError("Upscaler index is out of range.")

    upscaler = upscalers[upscaler_index]
    validated_overlap = validate_overlap(overlap, p.width, p.height)

    p.extra_generation_params["SD upscale overlap"] = validated_overlap
    p.extra_generation_params["SD upscale upscaler"] = upscaler.name

    init_img = p.init_images[0]
    if upscaler.scaler is None or upscaler.name == "None":
        result_img = init_img.copy()
        scaled = False
    else:
        result_img = upscaler.scaler.upscale(init_img, scale_factor, upscaler.data_path)
        scaled = True

    return {
        "upscaler": upscaler.name,
        "scale_factor": scale_factor,
        "width": result_img.width,
        "height": result_img.height,
        "scaled": scaled,
        "validated_overlap": validated_overlap,
    }


def demo() -> None:
    info, overlap, upscaler, scale_factor = ui()

    params = ProcessParams(
        width=64,
        height=64,
        init_images=[Image.new("RGB", (64, 64), "#5a7cfd")],
    )

    result = run(
        params,
        info,
        overlap.value,
        upscaler.value,
        scale_factor.value,
    )

    print("Fixed plugin demo result:")
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    demo()
