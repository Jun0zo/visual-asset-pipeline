from __future__ import annotations

import json
import re
from pathlib import Path


def infer_count(prompt: str, default: int = 24) -> int:
    match = re.search(r"\b(\d{1,3})\b", prompt)
    if not match:
        return default
    return max(1, min(256, int(match.group(1))))


def build_generation_brief(prompt: str, count: int | None = None, profile: str = "auto") -> dict[str, object]:
    """Build a deterministic visual-asset sheet generation brief for an image model."""

    asset_count = count or infer_count(prompt)
    asset_type = "visual assets" if profile == "auto" else f"{profile} assets"
    layout_hint = {
        "icon": "Use square-friendly, visually centered symbols.",
        "character": "Use complete character poses with consistent ground/pivot alignment and no cropped limbs.",
        "sprite": "Use animation-frame-friendly poses with consistent scale and spacing.",
        "web": "Use web-ready illustrations, logos, badges, and product/UI assets with original shapes preserved.",
        "ui": "Use clean UI controls, badges, buttons, and state variants.",
        "sticker": "Use expressive sticker-style cutouts with generous padding for glow or outline.",
        "auto": "Keep each asset complete, visually centered, and easy to crop.",
    }.get(profile, "Keep each asset complete, visually centered, and easy to crop.")
    return {
        "title": "Visual asset sheet generation brief",
        "source_prompt": prompt,
        "profile": profile,
        "target_asset_count": asset_count,
        "sheet_prompt": (
            f"Create one clean high-resolution asset sheet containing exactly {asset_count} separate {asset_type}. "
            f"User concept: {prompt}. Place assets on a plain light background with generous spacing. "
            "No captions, no numbers, no labels, no watermark, no decorative frame. "
            "Each asset should be complete, separated from neighbors, and consistent in style, "
            "stroke weight, lighting, perspective, and palette. Preserve transparent-friendly edges, shadows, glows, "
            f"and outlines. {layout_hint}"
        ),
        "negative_prompt": (
            "text, captions, numbers, labels, cropped icons, touching icons, overlapping icons, inconsistent styles, "
            "busy background, strong paper texture, watermark, logo, mockup frame"
        ),
        "recommended_generation_size": "2048x2048 or larger",
        "next_step": "Generate the sheet, then run scripts/run_visual_pipeline.py extract on the resulting image.",
    }


def write_generation_brief(prompt: str, output_dir: Path, count: int | None = None, profile: str = "auto") -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    brief = build_generation_brief(prompt, count=count, profile=profile)
    path = output_dir / "generation_brief.json"
    path.write_text(json.dumps(brief, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
