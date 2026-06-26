from __future__ import annotations

import json
import re
from pathlib import Path


def infer_count(prompt: str, default: int = 24) -> int:
    match = re.search(r"\b(\d{1,3})\b", prompt)
    if not match:
        return default
    return max(1, min(256, int(match.group(1))))


def build_generation_brief(prompt: str, count: int | None = None) -> dict[str, object]:
    """Build a deterministic icon-sheet generation brief for an image model."""

    icon_count = count or infer_count(prompt)
    return {
        "title": "Icon asset sheet generation brief",
        "source_prompt": prompt,
        "target_icon_count": icon_count,
        "sheet_prompt": (
            f"Create one clean high-resolution icon sheet containing exactly {icon_count} separate icons. "
            f"User concept: {prompt}. Place icons on a plain light background with generous spacing. "
            "No captions, no numbers, no labels, no watermark, no decorative frame. "
            "Each icon should be complete, visually centered, separated from neighbors, and consistent in style, "
            "stroke weight, lighting, perspective, and palette. Preserve transparent-friendly edges, shadows, glows, "
            "and outlines. Use a layout that makes each icon easy to crop into individual square assets."
        ),
        "negative_prompt": (
            "text, captions, numbers, labels, cropped icons, touching icons, overlapping icons, inconsistent styles, "
            "busy background, strong paper texture, watermark, logo, mockup frame"
        ),
        "recommended_generation_size": "2048x2048 or larger",
        "next_step": "Generate the sheet, then run scripts/run_icon_pipeline.py extract on the resulting image.",
    }


def write_generation_brief(prompt: str, output_dir: Path, count: int | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    brief = build_generation_brief(prompt, count=count)
    path = output_dir / "generation_brief.json"
    path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

