from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from .analysis import analyze_input
from .cleanup import clean_asset_crop
from .detection import detect_asset_candidates
from .models import BoundingBox, AssetCandidate, AssetRecord, InputAnalysis, PipelineConfig, ValidationIssue
from .naming import generate_asset_names, tags_for_asset
from .normalization import normalize_asset
from .packaging import write_package
from .segmentation import foreground_mask
from .validation import dominant_colors, find_duplicates, style_validation, validate_asset


def _crop_with_adaptive_padding(image: Image.Image, box: BoundingBox) -> tuple[Image.Image, BoundingBox]:
    width, height = image.size
    pad = max(8, int(round(max(box.w, box.h) * 0.18)))
    padded = box.expand(pad).clamp(width, height)
    return image.crop((padded.x, padded.y, padded.x2, padded.y2)), padded


def _dedupe(records: list[AssetRecord], threshold: int) -> tuple[list[AssetRecord], list[dict[str, str]]]:
    groups = find_duplicates(records, threshold=threshold)
    duplicate_names = {name for names in groups.values() for name in names}
    kept = [record for record in records if record.name not in duplicate_names]
    excluded = []
    for keeper, duplicates in groups.items():
        for duplicate in duplicates:
            excluded.append({"name": duplicate, "duplicate_of": keeper})
    return kept, excluded


def _record_from_candidate(
    candidate: AssetCandidate,
    crop_box: BoundingBox,
    clean_crop: Image.Image,
    normalized_images: dict[int, Image.Image],
    name: str,
    prompt: str | None,
    cleanup_notes: list[str],
) -> AssetRecord:
    largest = normalized_images[max(normalized_images.keys())]
    colors = dominant_colors(largest)
    issues = validate_asset(name, largest)
    return AssetRecord(
        candidate=candidate,
        crop_box=crop_box,
        name=name,
        clean_width=clean_crop.size[0],
        clean_height=clean_crop.size[1],
        normalized_images=normalized_images,
        dominant_colors=colors,
        tags=tags_for_asset(name, prompt, colors),
        issues=issues,
        cleanup_notes=cleanup_notes,
    )


def run_extract_pipeline(input_path: Path, output_dir: Path, config: PipelineConfig) -> dict[str, object]:
    """Run full sheet extraction, normalization, validation, naming, and packaging."""

    image = Image.open(input_path).convert("RGBA")
    initial_mask = foreground_mask(image)
    candidates, mask = detect_asset_candidates(image, config, mask=initial_mask)
    analysis = analyze_input(image, mask=mask, candidates=candidates)

    clean_crops: list[Image.Image] = []
    normalized_sets: list[dict[int, Image.Image]] = []
    cleanup_notes_by_index: list[list[str]] = []
    crop_boxes: list[BoundingBox] = []
    for candidate in candidates:
        crop, crop_box = _crop_with_adaptive_padding(image, candidate.box)
        clean_crop, cleanup_notes = clean_asset_crop(crop, repair=config.repair)
        normalized = normalize_asset(clean_crop, config.normalized_sizes(), config.effective_padding_ratio())
        clean_crops.append(clean_crop)
        crop_boxes.append(crop_box)
        normalized_sets.append(normalized)
        cleanup_notes_by_index.append(cleanup_notes)

    representative_images = [images[max(images.keys())] for images in normalized_sets]
    names = generate_asset_names(candidates, representative_images, prompt=config.prompt, names_file=config.names_file)
    records = [
        _record_from_candidate(
            candidate,
            crop_box,
            clean_crop,
            normalized,
            name,
            config.prompt,
            cleanup_notes,
        )
        for candidate, crop_box, clean_crop, normalized, name, cleanup_notes in zip(
            candidates, crop_boxes, clean_crops, normalized_sets, names, cleanup_notes_by_index
        )
    ]

    preview_records = records[:]
    records, excluded_duplicates = _dedupe(records, threshold=config.duplicate_threshold)
    style_report = style_validation(records)
    return write_package(
        records=records,
        excluded_duplicates=excluded_duplicates,
        analysis=analysis,
        output_dir=output_dir,
        config=config,
        source_path=str(input_path),
        style_report=style_report,
        preview_records=preview_records,
    )


def _load_directory_images(input_dir: Path) -> list[Path]:
    extensions = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
    return sorted(path for path in input_dir.iterdir() if path.suffix.lower() in extensions and path.is_file())


def run_directory_pipeline(input_dir: Path, output_dir: Path, config: PipelineConfig, normalize: bool = True) -> dict[str, object]:
    """Normalize and package an existing directory of individual asset files."""

    image_paths = _load_directory_images(input_dir)
    records: list[AssetRecord] = []
    candidates: list[AssetCandidate] = []
    representative_images: list[Image.Image] = []
    normalized_sets: list[dict[int, Image.Image]] = []
    clean_crops: list[Image.Image] = []

    for index, path in enumerate(image_paths):
        image = Image.open(path).convert("RGBA")
        clean_crop, cleanup_notes = clean_asset_crop(image, repair=config.repair)
        normalized = normalize_asset(clean_crop, config.normalized_sizes(), config.effective_padding_ratio()) if normalize else {
            size: clean_crop.resize((size, size)) for size in config.normalized_sizes()
        }
        candidate = AssetCandidate(index=index, box=BoundingBox(0, 0, image.size[0], image.size[1]), confidence=1.0)
        candidates.append(candidate)
        representative_images.append(normalized[max(normalized.keys())])
        normalized_sets.append(normalized)
        clean_crops.append(clean_crop)

    if not image_paths:
        analysis = InputAnalysis(
            width=0,
            height=0,
            background={"type": "none", "rgb": [0, 0, 0], "alpha": 0, "border_std": 0, "transparent_ratio": 1},
            warnings=["no_input_images"],
        )
        return write_package([], [], analysis, output_dir, config, str(input_dir), style_validation([]))

    output_dir.mkdir(parents=True, exist_ok=True)
    names_from_files = output_dir / "_source_names.json"
    names_from_files.write_text(json.dumps([path.stem for path in image_paths], indent=2), encoding="utf-8")
    original_names_file = config.names_file
    if original_names_file is None:
        config.names_file = names_from_files
    names = generate_asset_names(candidates, representative_images, prompt=config.prompt, names_file=config.names_file)
    config.names_file = original_names_file

    for candidate, clean_crop, normalized, name in zip(candidates, clean_crops, normalized_sets, names):
        records.append(_record_from_candidate(candidate, candidate.box, clean_crop, normalized, name, config.prompt, []))

    records, excluded_duplicates = _dedupe(records, threshold=config.duplicate_threshold)
    first = Image.open(image_paths[0]).convert("RGBA")
    analysis = analyze_input(first, candidates=candidates)
    style_report = style_validation(records)
    return write_package(records, excluded_duplicates, analysis, output_dir, config, str(input_dir), style_report)
