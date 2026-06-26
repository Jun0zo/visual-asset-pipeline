from __future__ import annotations

import numpy as np
from PIL import Image
from skimage import measure, morphology

from .segmentation import remove_background, rgba_array


def _remove_textlike_components(alpha: np.ndarray) -> tuple[np.ndarray, list[str]]:
    mask = alpha > 8
    height, width = mask.shape
    total = max(1, int(mask.sum()))
    labels = measure.label(mask, connectivity=2)
    keep = np.zeros_like(mask, dtype=bool)
    notes: list[str] = []

    for region in measure.regionprops(labels):
        min_row, min_col, max_row, max_col = region.bbox
        box_w = max_col - min_col
        box_h = max_row - min_row
        if box_w <= 0 or box_h <= 0:
            continue
        aspect = box_w / box_h
        area = int(region.area)
        center_y = (min_row + max_row) / 2.0
        near_bottom = center_y > height * 0.68
        tiny = area < max(6, total * 0.0012)
        caption_like = aspect > 2.6 and box_h < height * 0.16 and near_bottom and area < total * 0.28
        guide_line = (aspect > 7.5 and box_h <= max(3, height * 0.035)) or (
            aspect < 0.13 and box_w <= max(3, width * 0.035)
        )
        if tiny or caption_like or guide_line:
            if caption_like:
                notes.append("removed_textlike_component")
            elif guide_line:
                notes.append("removed_guideline_component")
            continue
        keep[labels == region.label] = True

    if not keep.any():
        return alpha, ["cleanup_preserved_original_no_components"]
    cleaned = np.where(keep, alpha, 0).astype(np.uint8)
    cleaned_mask = morphology.remove_small_holes(cleaned > 8, area_threshold=max(12, int(total * 0.002)))
    cleaned = np.where(cleaned_mask, cleaned, 0).astype(np.uint8)
    return cleaned, sorted(set(notes))


def clean_icon_crop(image: Image.Image, repair: bool = False) -> tuple[Image.Image, list[str]]:
    """Remove crop background, text-like artifacts, guide lines, and tiny noise."""

    transparent = remove_background(image)
    arr = rgba_array(transparent).copy()
    alpha = arr[:, :, 3]
    notes: list[str] = []
    cleaned_alpha, cleanup_notes = _remove_textlike_components(alpha)
    notes.extend(cleanup_notes)

    if repair:
        mask = cleaned_alpha > 8
        mask = morphology.binary_closing(mask, morphology.disk(1))
        mask = morphology.remove_small_holes(mask, area_threshold=max(16, int(mask.size * 0.0006)))
        cleaned_alpha = np.where(mask, cleaned_alpha, 0).astype(np.uint8)
        notes.append("repair_alpha_smoothing")

    arr[:, :, 3] = cleaned_alpha
    arr[cleaned_alpha == 0, :3] = 0
    return Image.fromarray(arr, mode="RGBA"), sorted(set(notes))

