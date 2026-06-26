from __future__ import annotations

import numpy as np
from PIL import Image

from .segmentation import alpha_bbox, rgba_array

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover - old Pillow fallback
    RESAMPLE_LANCZOS = Image.LANCZOS


def _optical_center(image: Image.Image) -> tuple[float, float]:
    arr = rgba_array(image)
    alpha = arr[:, :, 3].astype(np.float32)
    total = float(alpha.sum())
    if total <= 0:
        return image.size[0] / 2.0, image.size[1] / 2.0
    yy, xx = np.indices(alpha.shape)
    cx = float((xx * alpha).sum() / total)
    cy = float((yy * alpha).sum() / total)
    bbox = alpha_bbox(image)
    if bbox is None:
        return cx, cy
    bx, by = bbox.center
    return bx * 0.62 + cx * 0.38, by * 0.62 + cy * 0.38


def normalize_asset(image: Image.Image, sizes: tuple[int, ...], padding_ratio: float) -> dict[int, Image.Image]:
    """Center an asset optically and export square transparent canvases."""

    source = image.convert("RGBA")
    bbox = alpha_bbox(source)
    if bbox is None:
        return {size: Image.new("RGBA", (size, size), (0, 0, 0, 0)) for size in sizes}

    crop = source.crop((bbox.x, bbox.y, bbox.x2, bbox.y2))
    optical_x, optical_y = _optical_center(source)
    relative_optical_x = optical_x - bbox.x
    relative_optical_y = optical_y - bbox.y

    outputs: dict[int, Image.Image] = {}
    for size in sizes:
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        inner = max(1, int(round(size * (1.0 - padding_ratio * 2.0))))
        scale = min(inner / max(1, crop.size[0]), inner / max(1, crop.size[1]))
        new_w = max(1, int(round(crop.size[0] * scale)))
        new_h = max(1, int(round(crop.size[1] * scale)))
        resized = crop.resize((new_w, new_h), RESAMPLE_LANCZOS)

        scaled_optical_x = relative_optical_x * scale
        scaled_optical_y = relative_optical_y * scale
        paste_x = int(round(size / 2.0 - scaled_optical_x))
        paste_y = int(round(size / 2.0 - scaled_optical_y))

        min_pad = int(round(size * padding_ratio * 0.55))
        paste_x = max(min_pad, min(size - new_w - min_pad, paste_x))
        paste_y = max(min_pad, min(size - new_h - min_pad, paste_y))
        canvas.alpha_composite(resized, (paste_x, paste_y))
        outputs[size] = canvas
    return outputs
