# Icon Asset Pipeline

Generate, extract, repair, normalize, validate, name, and package production-ready icon assets from either a text prompt or a single image sheet.

This repository contains two deliverables:

- A Python package and CLI for deterministic icon extraction and packaging.
- A bundled Codex Skill under `skill/icon-asset-pipeline` for AI-assisted workflows.

## Current Status

Alpha-quality architecture with a working local computer-vision pipeline. The default implementation uses conservative heuristics so it can run without hosted services. Production deployments can replace individual modules with SAM, rembg, CLIP/DINOv2, OCR, or a vectorization service.

## Features

- Analyze icon sheets: background, layout hints, spacing, possible text, estimated count.
- Locate icons visually without relying purely on equal grids.
- Smart crop with adaptive padding for glows, outlines, shadows, and antialiasing.
- Remove simple backgrounds and export transparent PNG.
- Cleanup text-like captions, guide lines, tiny noise, and background residue.
- Normalize to square canvases at `128`, `256`, `512`, `1024`, or custom sizes.
- Validate edge cropping, blur, duplicate icons, text-like artifacts, style variance, and alpha quality.
- Generate semantic filenames from prompt/category/color/shape hints.
- Export PNG, WebP, sprite sheets, metadata, validation reports, contact sheet, and ZIP archive.
- Optionally attempt SVG export when a vectorizer such as `vtracer` is installed.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## CLI Usage

Create a generation brief:

```bash
icon-asset-pipeline brief \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --output work/forest-icons
```

Extract a generated or supplied icon sheet:

```bash
icon-asset-pipeline extract \
  --input work/forest-icons/generated-sheet.png \
  --output work/forest-icons/export \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --expected-count 48 \
  --sizes 128,256,512,1024
```

Normalize a folder of already-separated icons:

```bash
icon-asset-pipeline normalize \
  --input work/raw-icons \
  --output work/normalized-icons \
  --sizes 256,512
```

## Project Structure

```text
.
├── src/icon_asset_pipeline/      # Replaceable pipeline modules
├── tests/                        # Smoke tests and future quality tests
├── scripts/                      # Thin CLI wrapper for local runs
├── docs/                         # Architecture, library recommendations, naming notes
└── skill/icon-asset-pipeline/    # Codex Skill bundle
```

## Module Boundaries

- `analysis`: input inspection and layout metadata.
- `detection`: icon localization from visual components.
- `segmentation`: foreground masks and background removal.
- `cleanup`: captions, guide lines, artifacts, and noise removal.
- `normalization`: optical centering and canvas export.
- `validation`: quality gates, duplicates, and style consistency checks.
- `naming`: deterministic semantic filename generation.
- `packaging`: image exports, sprite sheets, metadata, reports, and ZIP archive.

## Tests

```bash
pytest
```

## Codex Skill

The installable Skill is in `skill/icon-asset-pipeline`. To use it as a local Codex Skill, copy that folder into your Codex skills directory:

```bash
cp -R skill/icon-asset-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## Naming

The working repository name is `icon-asset-pipeline` because it is descriptive and search-friendly. See `docs/name-candidates.md` for stronger product/open-source name options.

## Roadmap

- Model-backed semantic naming and duplicate detection.
- SAM/rembg segmentation adapter.
- OCR-backed caption removal.
- True SVG/vector export pipeline.
- Figma component export.
- React, Flutter, iOS asset catalog, Android drawable, Unity, Godot, and TexturePacker codegen.
- Visual regression benchmark suite for real-world icon sheets.
