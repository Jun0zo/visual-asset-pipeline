from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from statistics import mean

import numpy as np
from PIL import Image
from skimage import filters, measure

from .models import IconRecord, ValidationIssue
from .segmentation import rgba_array


def dominant_colors(image: Image.Image, count: int = 5) -> list[str]:
    arr = rgba_array(image)
    alpha = arr[:, :, 3]
    rgb = arr[:, :, :3]
    pixels = rgb[alpha > 24]
    if pixels.size == 0:
        return []
    pil = Image.fromarray(pixels.reshape(-1, 1, 3).astype(np.uint8), mode="RGB")
    quantized = pil.quantize(colors=max(1, count), method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette() or []
    color_counts = quantized.getcolors(maxcolors=4096) or []
    color_counts.sort(reverse=True)
    result: list[str] = []
    for _, idx in color_counts[:count]:
        offset = idx * 3
        if offset + 2 < len(palette):
            r, g, b = palette[offset : offset + 3]
            result.append(f"#{r:02x}{g:02x}{b:02x}")
    return result


def _edge_contact(alpha: np.ndarray) -> float:
    border = np.concatenate([alpha[0, :], alpha[-1, :], alpha[:, 0], alpha[:, -1]])
    return float(np.mean(border > 16))


def _blur_score(image: Image.Image) -> float:
    arr = rgba_array(image)
    gray = np.dot(arr[:, :, :3].astype(np.float32), [0.299, 0.587, 0.114]) / 255.0
    alpha = arr[:, :, 3] > 16
    if alpha.sum() < 16:
        return 0.0
    laplace = filters.laplace(gray)
    return float(np.var(laplace[alpha]))


def _textlike_component_count(alpha: np.ndarray) -> int:
    mask = alpha > 16
    labels = measure.label(mask, connectivity=2)
    height, width = alpha.shape
    count = 0
    for region in measure.regionprops(labels):
        min_row, min_col, max_row, max_col = region.bbox
        box_w = max_col - min_col
        box_h = max_row - min_row
        if box_h <= 0:
            continue
        aspect = box_w / box_h
        if aspect > 2.8 and box_h < height * 0.14 and (min_row + max_row) / 2.0 > height * 0.66:
            count += 1
    return count


def validate_icon(name: str, image: Image.Image) -> list[ValidationIssue]:
    arr = rgba_array(image)
    alpha = arr[:, :, 3]
    issues: list[ValidationIssue] = []
    if int((alpha > 16).sum()) == 0:
        issues.append(ValidationIssue("empty_alpha", "error", f"{name} has no visible foreground."))
        return issues

    edge = _edge_contact(alpha)
    if edge > 0.018:
        issues.append(ValidationIssue("edge_contact", "warning", f"{name} may be cropped or has shadow touching canvas edge."))

    blur = _blur_score(image)
    if blur < 0.00022 and image.size[0] >= 128:
        issues.append(ValidationIssue("possible_blur", "warning", f"{name} has low edge variance; inspect for blur."))

    if float(np.mean(alpha[[0, -1], :] > 8)) > 0.01 or float(np.mean(alpha[:, [0, -1]] > 8)) > 0.01:
        issues.append(ValidationIssue("nontransparent_border", "warning", f"{name} has nontransparent pixels on the border."))

    if _textlike_component_count(alpha) > 0:
        issues.append(ValidationIssue("textlike_artifact", "warning", f"{name} may still contain caption or label fragments."))
    return issues


def dhash(image: Image.Image, hash_size: int = 8) -> int:
    gray = image.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    pixels = np.asarray(gray, dtype=np.int16)
    diff = pixels[:, 1:] > pixels[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bool(bit))
    return value


def hamming_distance(a: int, b: int) -> int:
    return int((a ^ b).bit_count())


def find_duplicates(records: list[IconRecord], threshold: int = 7) -> dict[str, list[str]]:
    hashes = {
        record.name: dhash(record.normalized_images[max(record.normalized_images.keys())])
        for record in records
        if record.normalized_images
    }
    groups: dict[str, list[str]] = defaultdict(list)
    for left, right in combinations(records, 2):
        if left.name not in hashes or right.name not in hashes:
            continue
        if hamming_distance(hashes[left.name], hashes[right.name]) <= threshold:
            keep, duplicate = sorted([left, right], key=lambda item: item.quality_score(), reverse=True)
            groups[keep.name].append(duplicate.name)
    return dict(groups)


def style_validation(records: list[IconRecord]) -> dict[str, object]:
    if not records:
        return {"status": "empty", "warnings": ["no_icons"]}
    coverages: list[float] = []
    color_counts: list[int] = []
    edge_scores: list[float] = []
    for record in records:
        image = record.normalized_images[max(record.normalized_images.keys())]
        arr = rgba_array(image)
        alpha = arr[:, :, 3] > 16
        coverages.append(float(alpha.mean()))
        color_counts.append(len(record.dominant_colors))
        gray = np.dot(arr[:, :, :3].astype(np.float32), [0.299, 0.587, 0.114]) / 255.0
        edges = filters.sobel(gray)
        edge_scores.append(float(edges[alpha].mean()) if alpha.any() else 0.0)

    warnings: list[str] = []
    if len(coverages) > 1 and np.std(coverages) > 0.09:
        warnings.append("inconsistent_visual_weight")
    if len(edge_scores) > 1 and np.std(edge_scores) > max(0.035, mean(edge_scores) * 0.75):
        warnings.append("inconsistent_stroke_or_detail_density")
    if len(color_counts) > 1 and np.std(color_counts) > 2.5:
        warnings.append("inconsistent_palette_complexity")

    return {
        "status": "warning" if warnings else "pass",
        "warnings": warnings,
        "metrics": {
            "mean_alpha_coverage": round(float(mean(coverages)), 4),
            "alpha_coverage_std": round(float(np.std(coverages)), 4),
            "edge_density_std": round(float(np.std(edge_scores)), 4),
            "palette_count_std": round(float(np.std(color_counts)), 4),
        },
    }

