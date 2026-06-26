from __future__ import annotations

import math

import numpy as np

from .models import BoundingBox, AssetCandidate, PipelineConfig
from .segmentation import connected_boxes, foreground_mask


def _is_noise_or_caption(box: BoundingBox, image_size: tuple[int, int]) -> bool:
    width, height = image_size
    if box.w < 4 or box.h < 4:
        return True
    area_ratio = box.area / max(1, width * height)
    if area_ratio < 0.00001:
        return True
    aspect = box.aspect
    if aspect > 10 and box.h < height * 0.08:
        return True
    if aspect < 0.1 and box.w < width * 0.04:
        return True
    if aspect > 4.5 and box.h < height * 0.045 and box.y > height * 0.08:
        return True
    return False


def _merge_boxes(boxes: list[BoundingBox], gap: int, image_size: tuple[int, int]) -> list[BoundingBox]:
    width, height = image_size
    merged = [box.clamp(width, height) for box in boxes]
    changed = True
    while changed:
        changed = False
        result: list[BoundingBox] = []
        used = [False] * len(merged)
        for i, box in enumerate(merged):
            if used[i]:
                continue
            current = box
            used[i] = True
            local_changed = True
            while local_changed:
                local_changed = False
                for j, other in enumerate(merged):
                    if used[j]:
                        continue
                    if current.expand(gap).intersects(other.expand(gap)):
                        current = current.union(other).clamp(width, height)
                        used[j] = True
                        changed = True
                        local_changed = True
            result.append(current)
        merged = result
    return merged


def _score_boxes(boxes: list[BoundingBox], expected_count: int | None) -> float:
    if not boxes:
        return -1e9
    areas = np.array([box.area for box in boxes], dtype=np.float32)
    variance_penalty = float(np.std(np.log1p(areas)))
    count_score = -0.12 * len(boxes)
    if expected_count:
        count_score = -abs(len(boxes) - expected_count)
    return count_score - variance_penalty


def _assign_grid_positions(candidates: list[AssetCandidate]) -> None:
    if not candidates:
        return
    heights = [candidate.box.h for candidate in candidates]
    widths = [candidate.box.w for candidate in candidates]
    row_tolerance = max(8.0, float(np.median(heights)) * 0.55)
    col_tolerance = max(8.0, float(np.median(widths)) * 0.55)

    row_centers: list[float] = []
    for candidate in sorted(candidates, key=lambda item: item.box.center[1]):
        cy = candidate.box.center[1]
        for idx, center in enumerate(row_centers):
            if abs(cy - center) <= row_tolerance:
                row_centers[idx] = (center + cy) / 2.0
                candidate.row = idx
                break
        else:
            row_centers.append(cy)
            candidate.row = len(row_centers) - 1

    col_centers: list[float] = []
    for candidate in sorted(candidates, key=lambda item: item.box.center[0]):
        cx = candidate.box.center[0]
        for idx, center in enumerate(col_centers):
            if abs(cx - center) <= col_tolerance:
                col_centers[idx] = (center + cx) / 2.0
                candidate.column = idx
                break
        else:
            col_centers.append(cx)
            candidate.column = len(col_centers) - 1


def _candidate_confidence(box: BoundingBox, image_size: tuple[int, int]) -> float:
    width, height = image_size
    area_ratio = box.area / max(1, width * height)
    size_balance = min(box.aspect, 1.0 / max(0.01, box.aspect))
    edge_penalty = 0.0
    if box.x <= 1 or box.y <= 1 or box.x2 >= width - 1 or box.y2 >= height - 1:
        edge_penalty = 0.18
    return max(0.05, min(1.0, math.sqrt(area_ratio) * 5.0 + size_balance * 0.35 - edge_penalty))


def detect_asset_candidates(image, config: PipelineConfig, mask: np.ndarray | None = None) -> tuple[list[AssetCandidate], np.ndarray]:
    """Locate asset candidates from visual foreground components, not equal grid cells."""

    width, height = image.size
    if mask is None:
        mask = foreground_mask(image)
    min_area = max(12, int(width * height * config.min_area_ratio))
    raw_boxes = connected_boxes(mask, min_area=min_area)
    raw_boxes = [box for box in raw_boxes if not _is_noise_or_caption(box, (width, height))]

    if not raw_boxes:
        fallback_boxes = connected_boxes(mask, min_area=max(4, min_area // 8))
        if fallback_boxes:
            raw_boxes = [box for box in fallback_boxes if not _is_noise_or_caption(box, (width, height))]

    if not raw_boxes:
        candidates = [AssetCandidate(index=0, box=BoundingBox(0, 0, width, height), confidence=0.1, notes=["fallback_full_image"])]
        return candidates, mask

    min_dim = min(width, height)
    gap_ratios = [0.006, 0.012, 0.018, 0.026, 0.036]
    attempts: list[list[BoundingBox]] = []
    for ratio in gap_ratios:
        gap = max(3, int(round(min_dim * ratio)))
        merged = _merge_boxes(raw_boxes, gap, (width, height))
        merged = [box for box in merged if not _is_noise_or_caption(box, (width, height))]
        attempts.append(merged)

    selected = max(attempts, key=lambda boxes: _score_boxes(boxes, config.expected_count))
    if config.expected_count and len(selected) > int(config.expected_count * 1.45):
        selected = sorted(selected, key=lambda box: box.area, reverse=True)[: config.expected_count]

    selected = sorted(selected, key=lambda box: (box.center[1], box.center[0]))
    candidates = [
        AssetCandidate(index=i, box=box, confidence=_candidate_confidence(box, (width, height)))
        for i, box in enumerate(selected)
    ]
    _assign_grid_positions(candidates)

    if config.expected_count and len(candidates) != config.expected_count:
        note = f"expected_count_mismatch:{config.expected_count}->{len(candidates)}"
        for candidate in candidates:
            candidate.notes.append(note)
    return candidates, mask
