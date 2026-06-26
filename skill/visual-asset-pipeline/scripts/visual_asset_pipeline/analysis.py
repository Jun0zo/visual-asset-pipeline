from __future__ import annotations

import numpy as np
from skimage import measure

from .models import BoundingBox, AssetCandidate, InputAnalysis
from .segmentation import estimate_background


def _cluster_positions(values: list[float], tolerance: float) -> list[list[float]]:
    if not values:
        return []
    clusters: list[list[float]] = []
    for value in sorted(values):
        if not clusters or abs(value - np.mean(clusters[-1])) > tolerance:
            clusters.append([value])
        else:
            clusters[-1].append(value)
    return clusters


def _median_spacing(clusters: list[list[float]]) -> float | None:
    if len(clusters) < 2:
        return None
    centers = [float(np.mean(cluster)) for cluster in clusters]
    diffs = np.diff(sorted(centers))
    return float(np.median(diffs)) if diffs.size else None


def _possible_text(mask: np.ndarray | None, width: int, height: int) -> bool:
    if mask is None:
        return False
    labels = measure.label(mask.astype(bool), connectivity=2)
    text_like = 0
    for region in measure.regionprops(labels):
        min_row, min_col, max_row, max_col = region.bbox
        box_w = max_col - min_col
        box_h = max_row - min_row
        if box_h <= 0:
            continue
        aspect = box_w / box_h
        area_ratio = region.area / max(1, width * height)
        if aspect > 3.2 and box_h < height * 0.075 and area_ratio < 0.012:
            text_like += 1
    return text_like >= 2


def analyze_input(
    image,
    mask: np.ndarray | None = None,
    candidates: list[AssetCandidate] | None = None,
) -> InputAnalysis:
    """Analyze source image layout, background, grid hints, text, and decorations."""

    width, height = image.size
    background = estimate_background(image)
    warnings: list[str] = []
    decorations: list[str] = []

    boxes: list[BoundingBox] = [candidate.box for candidate in candidates or []]
    estimated_count = len(boxes)
    rows = columns = None
    spacing = {"x": None, "y": None}

    if boxes:
        widths = [box.w for box in boxes]
        heights = [box.h for box in boxes]
        tolerance_y = max(8.0, float(np.median(heights)) * 0.55)
        tolerance_x = max(8.0, float(np.median(widths)) * 0.55)
        x_clusters = _cluster_positions([box.center[0] for box in boxes], tolerance_x)
        y_clusters = _cluster_positions([box.center[1] for box in boxes], tolerance_y)
        columns = len(x_clusters)
        rows = len(y_clusters)
        spacing = {"x": _median_spacing(x_clusters), "y": _median_spacing(y_clusters)}

        areas = np.array([box.area for box in boxes], dtype=np.float32)
        if areas.size and areas.max() > max(areas.min() * 5, float(np.median(areas)) * 3.5):
            warnings.append("large_candidate_variance")
        if rows and columns and rows * columns > estimated_count * 1.4:
            warnings.append("non_grid_or_missing_cells")

    if background["type"] in {"gradient_or_texture", "complex"}:
        warnings.append("complex_background")
    if mask is not None and _possible_text(mask, width, height):
        decorations.append("possible_text_or_captions")

    return InputAnalysis(
        width=width,
        height=height,
        background=background,
        estimated_asset_count=estimated_count,
        estimated_rows=rows,
        estimated_columns=columns,
        spacing=spacing,
        possible_text="possible_text_or_captions" in decorations,
        decorations=decorations,
        warnings=warnings,
    )

