from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from visual_asset_pipeline.models import PipelineConfig
from visual_asset_pipeline.pipeline import run_extract_pipeline


def _synthetic_sheet(path: Path) -> None:
    image = Image.new("RGBA", (520, 360), (246, 246, 240, 255))
    draw = ImageDraw.Draw(image)
    shapes = [
        (60, 52, "ellipse", (55, 130, 65, 255)),
        (220, 50, "rect", (60, 100, 190, 255)),
        (380, 56, "triangle", (190, 85, 70, 255)),
        (72, 210, "diamond", (70, 155, 155, 255)),
        (236, 208, "ellipse", (150, 95, 175, 255)),
        (390, 214, "rect", (205, 155, 45, 255)),
    ]
    for x, y, kind, color in shapes:
        if kind == "ellipse":
            draw.ellipse((x, y, x + 72, y + 72), fill=color)
        elif kind == "rect":
            draw.rounded_rectangle((x, y, x + 76, y + 72), radius=12, fill=color)
        elif kind == "triangle":
            draw.polygon([(x + 38, y), (x, y + 72), (x + 76, y + 72)], fill=color)
        elif kind == "diamond":
            draw.polygon([(x + 38, y), (x + 76, y + 38), (x + 38, y + 76), (x, y + 38)], fill=color)
    image.save(path)


def test_extract_pipeline_smoke(tmp_path: Path) -> None:
    source = tmp_path / "sheet.png"
    output = tmp_path / "export"
    _synthetic_sheet(source)
    result = run_extract_pipeline(
        source,
        output,
        PipelineConfig(profile="icon", sizes=(128, 256), expected_count=6, prompt="Create 6 forest exploration icons.", zip_output=True),
    )
    metadata = json.loads(Path(result["metadata"]).read_text(encoding="utf-8"))
    assert result["asset_count"] >= 4
    assert Path(result["zip"]).exists()
    assert result["crop_preview"]
    assert Path(result["crop_preview"]).exists()
    assert metadata["assets"]
    assert metadata["exports"]["crop_preview"]
    assert all("crop_box" in asset for asset in metadata["assets"])
    assert all(not asset["filename_base"].startswith("asset1") for asset in metadata["assets"])
