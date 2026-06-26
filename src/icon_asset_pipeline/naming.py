from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from .models import IconCandidate
from .segmentation import rgba_array

STOPWORDS = {
    "a",
    "an",
    "and",
    "asset",
    "assets",
    "create",
    "for",
    "icon",
    "icons",
    "in",
    "of",
    "pack",
    "set",
    "style",
    "the",
    "to",
    "with",
}

STYLE_WORDS = {
    "watercolor",
    "flat",
    "outline",
    "outlined",
    "filled",
    "line",
    "hand",
    "drawn",
    "minimal",
    "isometric",
    "pixel",
    "vector",
    "cartoon",
    "3d",
}

COLOR_NAMES = [
    ("black", (20, 20, 20)),
    ("white", (242, 242, 242)),
    ("gray", (128, 128, 128)),
    ("red", (204, 52, 52)),
    ("orange", (229, 132, 38)),
    ("yellow", (230, 205, 56)),
    ("green", (64, 154, 82)),
    ("teal", (48, 166, 150)),
    ("blue", (62, 112, 204)),
    ("purple", (128, 84, 190)),
    ("pink", (214, 95, 155)),
    ("brown", (132, 89, 55)),
]


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "asset_symbol"


def _load_names(names_file: Path | None) -> list[str] | dict[str, str] | None:
    if not names_file:
        return None
    data = json.loads(names_file.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [slugify(str(item)) for item in data]
    if isinstance(data, dict):
        return {str(key): slugify(str(value)) for key, value in data.items()}
    raise ValueError("names_file must be a JSON list or object")


def _prompt_terms(prompt: str | None) -> list[str]:
    if not prompt:
        return ["asset"]
    terms = []
    for token in re.findall(r"[a-zA-Z0-9]+", prompt.lower()):
        if token.isdigit() or token in STOPWORDS or token in STYLE_WORDS:
            continue
        if len(token) <= 2:
            continue
        terms.append(token)
    deduped: list[str] = []
    for term in terms:
        if term not in deduped:
            deduped.append(term)
    return deduped[:4] or ["asset"]


def _nearest_color_name(rgb: tuple[int, int, int]) -> str:
    color = np.array(rgb, dtype=np.float32)
    best_name = "color"
    best_distance = float("inf")
    for name, target in COLOR_NAMES:
        distance = float(np.linalg.norm(color - np.array(target, dtype=np.float32)))
        if distance < best_distance:
            best_name = name
            best_distance = distance
    return best_name


def _visual_descriptors(image) -> tuple[str, str]:
    arr = rgba_array(image)
    alpha = arr[:, :, 3]
    visible = alpha > 24
    if not visible.any():
        return "transparent", "symbol"

    rgb = arr[:, :, :3][visible]
    median = tuple(int(v) for v in np.median(rgb, axis=0).tolist())
    color_name = _nearest_color_name(median)

    ys, xs = np.where(visible)
    width = max(1, int(xs.max() - xs.min() + 1))
    height = max(1, int(ys.max() - ys.min() + 1))
    fill_ratio = float(visible.sum()) / float(width * height)
    aspect = width / height
    if fill_ratio > 0.56:
        shape = "badge"
    elif aspect > 1.35:
        shape = "wide_symbol"
    elif aspect < 0.75:
        shape = "tall_symbol"
    else:
        shape = "symbol"
    return color_name, shape


def _position_name(candidate: IconCandidate) -> str:
    row = "r" + str((candidate.row or 0) + 1).zfill(2)
    col = "c" + str((candidate.column or 0) + 1).zfill(2)
    return f"{row}_{col}"


def _unique(base: str, used: set[str]) -> str:
    name = slugify(base)
    if name not in used:
        used.add(name)
        return name
    suffix = "b"
    while f"{name}_{suffix}" in used:
        suffix = chr(ord(suffix) + 1)
    final = f"{name}_{suffix}"
    used.add(final)
    return final


def generate_icon_names(
    candidates: list[IconCandidate],
    representative_images: list,
    prompt: str | None = None,
    names_file: Path | None = None,
) -> list[str]:
    """Generate stable semantic filenames. Never returns icon1/icon2 style names."""

    provided = _load_names(names_file)
    terms = _prompt_terms(prompt)
    category = terms[0]
    secondary = terms[1] if len(terms) > 1 else "asset"
    used: set[str] = set()
    names: list[str] = []

    for idx, candidate in enumerate(candidates):
        if isinstance(provided, list) and idx < len(provided):
            names.append(_unique(provided[idx], used))
            continue
        if isinstance(provided, dict):
            key_options = [str(idx), str(candidate.index), _position_name(candidate)]
            found = next((provided[key] for key in key_options if key in provided), None)
            if found:
                names.append(_unique(found, used))
                continue

        image = representative_images[idx] if idx < len(representative_images) else None
        if image is not None:
            color, shape = _visual_descriptors(image)
            base = f"{category}_{color}_{shape}"
        else:
            base = f"{category}_{secondary}_{_position_name(candidate)}"
        if base in used:
            base = f"{base}_{_position_name(candidate)}"
        names.append(_unique(base, used))
    return names


def tags_for_icon(name: str, prompt: str | None, colors: list[str]) -> list[str]:
    tags = [part for part in slugify(name).split("_") if part]
    tags.extend(_prompt_terms(prompt)[:5])
    if colors:
        tags.extend(colors[:3])
    deduped: list[str] = []
    for tag in tags:
        if tag not in deduped:
            deduped.append(tag)
    return deduped[:12]

