from __future__ import annotations

import json
import math
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

from .models import AssetRecord, InputAnalysis, PipelineConfig

try:
    RESAMPLE_LANCZOS = Image.Resampling.LANCZOS
except AttributeError:  # pragma: no cover
    RESAMPLE_LANCZOS = Image.LANCZOS


def _category_from_prompt(prompt: str | None) -> str:
    if not prompt:
        return "visual-assets"
    lower = prompt.lower()
    for keyword in ["forest", "travel", "finance", "medical", "game", "weather", "food", "education", "social"]:
        if keyword in lower:
            return keyword
    return "visual-assets"


def _write_sprite(records: list[AssetRecord], size: int, output_dir: Path) -> dict[str, Any] | None:
    if not records:
        return None
    columns = max(1, math.ceil(math.sqrt(len(records))))
    rows = math.ceil(len(records) / columns)
    sheet = Image.new("RGBA", (columns * size, rows * size), (0, 0, 0, 0))
    frames: dict[str, Any] = {}
    for index, record in enumerate(records):
        x = (index % columns) * size
        y = (index // columns) * size
        sheet.alpha_composite(record.normalized_images[size], (x, y))
        frames[record.name] = {"x": x, "y": y, "w": size, "h": size}
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"sprite_{size}.png"
    json_path = output_dir / f"sprite_{size}.json"
    sheet.save(image_path)
    json_path.write_text(json.dumps({"image": image_path.name, "size": size, "frames": frames}, indent=2), encoding="utf-8")
    return {"size": size, "image": str(image_path), "atlas": str(json_path), "frames": frames}


def _try_vectorize(png_path: Path, svg_path: Path) -> tuple[bool, str | None]:
    vtracer = shutil.which("vtracer")
    if vtracer:
        result = subprocess.run([vtracer, "--input", str(png_path), "--output", str(svg_path)], capture_output=True, text=True)
        if result.returncode == 0 and svg_path.exists():
            return True, None
        return False, result.stderr.strip() or "vtracer failed"
    return False, "no vectorizer installed"


def _write_contact_sheet(records: list[AssetRecord], output_path: Path, size: int = 160) -> None:
    if not records:
        return
    columns = min(6, max(1, math.ceil(math.sqrt(len(records)))))
    label_h = 28
    rows = math.ceil(len(records) / columns)
    sheet = Image.new("RGBA", (columns * size, rows * (size + label_h)), (248, 248, 248, 255))
    draw = ImageDraw.Draw(sheet)
    for index, record in enumerate(records):
        x = (index % columns) * size
        y = (index // columns) * (size + label_h)
        thumb = record.normalized_images[max(record.normalized_images.keys())].resize((size, size), RESAMPLE_LANCZOS)
        sheet.alpha_composite(thumb, (x, y))
        draw.text((x + 6, y + size + 6), record.name[:24], fill=(30, 30, 30, 255))
    sheet.save(output_path)


def _zip_dir(source_dir: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path == zip_path or not path.is_file():
                continue
            archive.write(path, path.relative_to(source_dir))


def write_package(
    records: list[AssetRecord],
    excluded_duplicates: list[dict[str, str]],
    analysis: InputAnalysis,
    output_dir: Path,
    config: PipelineConfig,
    source_path: str | None,
    style_report: dict[str, Any],
) -> dict[str, Any]:
    """Export images, sprite sheets, metadata, reports, contact sheet, and ZIP."""

    output_dir.mkdir(parents=True, exist_ok=True)
    png_root = output_dir / "png"
    webp_root = output_dir / "webp"
    svg_root = output_dir / "svg"
    sprite_root = output_dir / "sprites"
    files_by_asset: dict[str, dict[str, Any]] = {}
    svg_warnings: list[str] = []

    for record in records:
        files_by_asset[record.name] = {"png": {}, "webp": {}, "svg": None}
        for size, image in record.normalized_images.items():
            png_dir = png_root / str(size)
            png_dir.mkdir(parents=True, exist_ok=True)
            png_path = png_dir / f"{record.name}.png"
            image.save(png_path)
            files_by_asset[record.name]["png"][str(size)] = str(png_path)

            if config.webp:
                webp_dir = webp_root / str(size)
                webp_dir.mkdir(parents=True, exist_ok=True)
                webp_path = webp_dir / f"{record.name}.webp"
                image.save(webp_path, format="WEBP", lossless=True, quality=100)
                files_by_asset[record.name]["webp"][str(size)] = str(webp_path)

        if config.svg:
            svg_root.mkdir(parents=True, exist_ok=True)
            largest = max(record.normalized_images.keys())
            png_path = Path(files_by_asset[record.name]["png"][str(largest)])
            svg_path = svg_root / f"{record.name}.svg"
            ok, error = _try_vectorize(png_path, svg_path)
            if ok:
                files_by_asset[record.name]["svg"] = str(svg_path)
            else:
                svg_warnings.append(f"{record.name}: {error}")

    sprite_outputs = []
    if config.sprite:
        for size in config.normalized_sizes():
            sprite = _write_sprite(records, size, sprite_root)
            if sprite:
                sprite_outputs.append(sprite)

    contact_sheet = output_dir / "contact_sheet.png"
    _write_contact_sheet(records, contact_sheet)

    category = config.category or _category_from_prompt(config.prompt)
    metadata = {
        "title": f"{category.title()} Visual Asset Package",
        "description": config.prompt or "Visual assets extracted and normalized from source imagery.",
        "category": category,
        "asset_profile": config.normalized_profile(),
        "source": source_path,
        "canvas_sizes": list(config.normalized_sizes()),
        "analysis": analysis.to_dict(),
        "exports": {
            "png": str(png_root),
            "webp": str(webp_root) if config.webp else None,
            "svg": str(svg_root) if config.svg and svg_root.exists() else None,
            "sprites": sprite_outputs,
            "contact_sheet": str(contact_sheet),
        },
        "assets": [],
        "excluded_duplicates": excluded_duplicates,
        "svg_warnings": svg_warnings,
    }

    validation_report = {
        "status": "pass",
        "asset_count": len(records),
        "excluded_duplicate_count": len(excluded_duplicates),
        "style": style_report,
        "assets": {},
        "warnings": [],
    }

    for record in records:
        asset_meta = {
            "name": record.name,
            "filename_base": record.name,
            "title": record.name.replace("_", " ").title(),
            "description": config.prompt or f"Normalized visual asset: {record.name}",
            "category": category,
            "tags": record.tags,
            "dominant_colors": record.dominant_colors,
            "bounding_box": record.candidate.box.to_dict(),
            "canvas_size": list(config.normalized_sizes()),
            "source_candidate": record.candidate.to_dict(),
            "cleanup_notes": record.cleanup_notes,
            "files": files_by_asset[record.name],
        }
        metadata["assets"].append(asset_meta)
        validation_report["assets"][record.name] = [issue.to_dict() for issue in record.issues]
        for issue in record.issues:
            if issue.severity in {"warning", "error"}:
                validation_report["warnings"].append(issue.to_dict())
                validation_report["status"] = "warning" if validation_report["status"] == "pass" else validation_report["status"]
            if issue.severity == "error":
                validation_report["status"] = "error"

    metadata_path = output_dir / "metadata.json"
    report_path = output_dir / "validation_report.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    report_path.write_text(json.dumps(validation_report, indent=2, ensure_ascii=False), encoding="utf-8")

    zip_path = None
    if config.zip_output:
        zip_path = output_dir / "visual_asset_package.zip"
        _zip_dir(output_dir, zip_path)

    return {
        "output_dir": str(output_dir),
        "metadata": str(metadata_path),
        "validation_report": str(report_path),
        "zip": str(zip_path) if zip_path else None,
        "contact_sheet": str(contact_sheet),
        "asset_count": len(records),
        "warnings": validation_report["warnings"] + [{"code": "svg", "message": warning} for warning in svg_warnings],
    }
