from typing import cast

from PIL import Image
import pytest

from fixed_plugin import FixedPluginError, ProcessParams, run, ui


def create_params(width=64, height=64) -> ProcessParams:
    return ProcessParams(width=width, height=height, init_images=[Image.new("RGB", (width, height), "#ffffff")])


def test_ui_returns_components_in_expected_order():
    info, overlap, upscaler, scale_factor = ui()
    overlap.value = 32
    upscaler.value = 1
    scale_factor.value = 3.0

    params = create_params()
    result = run(params, info, overlap.value, upscaler.value, scale_factor.value)

    assert result["upscaler"] == "MockUpscaler"
    assert result["validated_overlap"] == 32
    assert result["scaled"] is True
    assert result["width"] == 192
    assert result["height"] == 192


def test_run_rejects_non_integer_upscaler_index():
    info, overlap, upscaler, scale_factor = ui()
    params = create_params()

    with pytest.raises(FixedPluginError):
        run(params, info, overlap.value, cast(int, "not-an-index"), scale_factor.value)


def test_none_upscaler_preserves_image_size():
    info, overlap, upscaler, scale_factor = ui()
    upscaler.value = 0
    params = create_params(width=32, height=32)

    result = run(params, info, overlap.value, upscaler.value, scale_factor.value)

    assert result["upscaler"] == "None"
    assert result["scaled"] is False
    assert result["width"] == 32
    assert result["height"] == 32


def test_overlap_clamps_to_tile_size():
    info, overlap, upscaler, scale_factor = ui()
    overlap.value = 128
    params = create_params(width=16, height=16)

    result = run(params, info, overlap.value, upscaler.value, scale_factor.value)

    assert result["validated_overlap"] == 15
