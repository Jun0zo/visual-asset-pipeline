from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image
from skimage import color, filters, measure, morphology

from .models import BoundingBox


def ensure_rgba(image: Image.Image) -> Image.Image:
    if image.mode == "RGBA":
        return image
    return image.convert("RGBA")


def rgba_array(image: Image.Image) -> np.ndarray:
    return np.asarray(ensure_rgba(image), dtype=np.uint8)


def estimate_background(image: Image.Image) -> dict[str, Any]:
    """Estimate background color and complexity from border pixels."""

    arr = rgba_array(image)
    height, width = arr.shape[:2]
    strip = max(2, min(18, min(width, height) // 32))
    border = np.concatenate(
        [
            arr[:strip, :, :].reshape(-1, 4),
            arr[-strip:, :, :].reshape(-1, 4),
            arr[:, :strip, :].reshape(-1, 4),
            arr[:, -strip:, :].reshape(-1, 4),
        ],
        axis=0,
    )
    opaque = border[border[:, 3] > 8]
    sample = opaque if len(opaque) else border.reshape(-1, 4)
    rgb = sample[:, :3].astype(np.float32)
    alpha = sample[:, 3].astype(np.float32)
    median = np.median(rgb, axis=0)
    std = np.std(rgb, axis=0)
    transparent_ratio = float(np.mean(border[:, 3] < 8))
    complexity = float(np.mean(std))
    if transparent_ratio > 0.2:
        kind = "transparent"
    elif complexity < 8:
        kind = "solid"
    elif complexity < 22:
        kind = "gradient_or_texture"
    else:
        kind = "complex"
    return {
        "type": kind,
        "rgb": [int(round(v)) for v in median.tolist()],
        "alpha": int(round(float(np.median(alpha)))),
        "border_std": round(complexity, 3),
        "transparent_ratio": round(transparent_ratio, 4),
    }


def _safe_otsu(values: np.ndarray, fallback: float) -> float:
    values = values[np.isfinite(values)]
    if values.size < 32 or float(values.max() - values.min()) < 1e-4:
        return fallback
    try:
        return float(filters.threshold_otsu(values))
    except ValueError:
        return fallback


def foreground_mask(image: Image.Image, background: dict[str, Any] | None = None, sensitivity: float = 0.45) -> np.ndarray:
    """Build a binary foreground mask using alpha, color distance, saturation, and edge cues."""

    arr = rgba_array(image)
    alpha = arr[:, :, 3].astype(np.float32) / 255.0
    if background is None:
        background = estimate_background(image)

    if background["type"] == "transparent" and np.mean(alpha < 0.05) > 0.01:
        mask = alpha > 0.05
    else:
        bg = np.array(background["rgb"], dtype=np.float32) / 255.0
        rgb = arr[:, :, :3].astype(np.float32) / 255.0
        dist = np.linalg.norm(rgb - bg, axis=2) / np.sqrt(3.0)
        gray = color.rgb2gray(rgb)
        edge = filters.sobel(gray)
        saturation = rgb.max(axis=2) - rgb.min(axis=2)
        otsu = _safe_otsu(dist, 0.11)
        threshold = max(0.035, min(0.22, otsu * (0.9 - sensitivity * 0.25)))
        strong_edge = edge > max(0.025, float(np.percentile(edge, 91)))
        mask = (dist > threshold) | ((saturation > 0.14) & (dist > threshold * 0.55)) | (
            strong_edge & (dist > threshold * 0.35)
        )
        mask &= alpha > 0.02

    min_dim = min(arr.shape[0], arr.shape[1])
    min_size = max(8, int(arr.shape[0] * arr.shape[1] * 0.000006))
    mask = morphology.remove_small_objects(mask.astype(bool), min_size=min_size)
    radius = max(1, min(4, min_dim // 500))
    mask = morphology.binary_closing(mask, morphology.disk(radius))
    return mask.astype(bool)


def connected_boxes(mask: np.ndarray, min_area: int) -> list[BoundingBox]:
    labels = measure.label(mask.astype(bool), connectivity=2)
    boxes: list[BoundingBox] = []
    for region in measure.regionprops(labels):
        if region.area < min_area:
            continue
        min_row, min_col, max_row, max_col = region.bbox
        boxes.append(BoundingBox.from_xyxy(min_col, min_row, max_col, max_row))
    return boxes


def alpha_from_background(
    image: Image.Image,
    mask: np.ndarray | None = None,
    background: dict[str, Any] | None = None,
) -> np.ndarray:
    """Create a soft alpha matte from estimated background distance."""

    arr = rgba_array(image)
    existing_alpha = arr[:, :, 3].astype(np.float32)
    if background is None:
        background = estimate_background(image)
    if mask is None:
        mask = foreground_mask(image, background)

    if background["type"] == "transparent" and np.mean(existing_alpha < 12) > 0.01:
        alpha = existing_alpha
    else:
        bg = np.array(background["rgb"], dtype=np.float32)
        rgb = arr[:, :, :3].astype(np.float32)
        dist = np.linalg.norm(rgb - bg, axis=2) / (255.0 * np.sqrt(3.0))
        border_low = max(0.02, float(np.percentile(dist, 55)))
        fg_values = dist[mask]
        high = float(np.percentile(fg_values, 72)) if fg_values.size else 0.18
        high = max(high, border_low + 0.08)
        soft = np.clip((dist - border_low) / (high - border_low), 0.0, 1.0) * 255.0
        soft = filters.gaussian(soft, sigma=0.45, preserve_range=True)
        alpha = np.maximum(soft, mask.astype(np.float32) * 120.0)
        alpha = np.minimum(alpha, existing_alpha)

    alpha[alpha < 4] = 0
    return np.clip(alpha, 0, 255).astype(np.uint8)


def remove_background(
    image: Image.Image,
    mask: np.ndarray | None = None,
    background: dict[str, Any] | None = None,
) -> Image.Image:
    """Return an RGBA image with background converted to transparency."""

    arr = rgba_array(image).copy()
    alpha = alpha_from_background(image, mask=mask, background=background)
    arr[:, :, 3] = alpha
    arr[alpha == 0, :3] = 0
    return Image.fromarray(arr, mode="RGBA")


def alpha_bbox(image: Image.Image, threshold: int = 8) -> BoundingBox | None:
    arr = rgba_array(image)
    alpha = arr[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if xs.size == 0 or ys.size == 0:
        return None
    return BoundingBox.from_xyxy(int(xs.min()), int(ys.min()), int(xs.max() + 1), int(ys.max() + 1))
