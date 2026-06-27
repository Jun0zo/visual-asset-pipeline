# Visual Asset Pipeline

![Visual Asset Pipeline hero](docs/assets/hero.png)

**Visual Asset Pipeline** turns prompts, dense asset sheets, webpage captures, sketches, and image folders into production-ready visual asset packages for design tools, apps, websites, and game engines.

[English](README.md) | [한국어](README.ko.md) | [日本語](docs/i18n/README.ja.md) | [简体中文](docs/i18n/README.zh-CN.md) | [Español](docs/i18n/README.es.md)

> Status: alpha. The local computer-vision pipeline works today, while model-backed segmentation, semantic naming, OCR, SVG conversion, and framework codegen are designed as replaceable adapters.

## What It Handles

Visual Asset Pipeline is not limited to icons. Icons are one profile among several production asset workflows.

- Icons, symbol packs, badges, and app assets
- Character sheets, mascots, pose boards, and transparent cutouts
- Sprite sheets, game props, effects, and atlas-ready frames
- Webpage captures, landing-page visuals, logos, and illustrations
- UI buttons, state variants, sticker packs, decals, and emotes
- Existing image folders that need normalization, naming, validation, and packaging

![Asset profiles](docs/assets/asset-profiles.png)

## Why It Is Different

- It works from messy visual inputs, not only perfect grids.
- It packages assets for real downstream use: PNG, WebP, optional SVG, sprites, metadata, validation reports, contact sheets, crop previews, and ZIP archives.
- It preserves visual quality details such as antialiasing, shadows, outlines, glows, and optical centering.
- It treats naming, validation, duplicate detection, and style consistency as part of the pipeline, not manual cleanup after export.
- It is installable as a Codex skill, Python CLI, npm global CLI, and one-off `npx` command.

## Pipeline

![Pipeline flow](docs/assets/pipeline-flow.png)

Korean process walkthrough: [Visual Asset Pipeline 프로세스 설명](docs/process.ko.md)

1. Analyze the input: layout, background, text, spacing, grid hints, and expected asset count.
2. Locate assets visually: use foreground components instead of trusting equal grid cells.
3. Segment foreground: remove backgrounds while preserving antialiasing, shadows, outlines, and glows.
4. Clean crops: remove captions, labels, numbers, guide lines, and small artifacts.
5. Normalize exports: apply profile-aware padding, optical centering, and requested sizes.
6. Validate quality: flag cropped edges, blur, duplicates, text residue, background artifacts, and style variance.
7. Package outputs: write PNG, WebP, optional SVG, sprite sheets, metadata, validation reports, contact sheet, crop preview, and ZIP.

## Install

### Python

```bash
git clone https://github.com/Jun0zo/visual-asset-pipeline.git
cd visual-asset-pipeline
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

Verify:

```bash
visual-asset-pipeline --help
pytest
```

The short alias is also available:

```bash
vap --help
```

### npm / npx

The npm package provides a small Node.js CLI wrapper around the Python pipeline. During install, it tries to create a package-local Python virtual environment and install the Python dependencies there.

```bash
npm install -g github:Jun0zo/visual-asset-pipeline
vap --help
```

For one-off use:

```bash
npx --yes github:Jun0zo/visual-asset-pipeline --help
```

Set `VAP_SKIP_PYTHON_INSTALL=1` before `npm install` if you want to manage the Python environment yourself.

## Quick Start

Create a generation brief from a prompt:

```bash
visual-asset-pipeline brief \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --profile icon \
  --output work/forest-assets
```

Generate an image sheet from `work/forest-assets/generation_brief.json` with your image model, then extract assets:

```bash
visual-asset-pipeline extract \
  --input work/forest-assets/generated-sheet.png \
  --output work/forest-assets/export \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --profile icon \
  --expected-count 48 \
  --sizes 128,256,512,1024
```

Normalize a folder of already-separated images:

```bash
visual-asset-pipeline normalize \
  --input work/raw-assets \
  --output work/normalized-assets \
  --profile web \
  --sizes 256,512
```

## Output Package

![Output package](docs/assets/package-outputs.png)

Each extraction can produce:

- `png/<size>/*.png`
- `webp/<size>/*.webp`
- `svg/*.svg` when a vectorizer is available
- `sprites/sprite_<size>.png`
- `sprites/sprite_<size>.json`
- `metadata.json`
- `validation_report.json`
- `contact_sheet.png`
- `crop_preview.png`
- `visual_asset_package.zip`

The output is designed for Figma, React, Flutter, iOS, Android, web apps, Unity, Godot, and other game engines.

## Crop Preview Overlay

![Crop preview overlay](docs/assets/crop-preview-overlay.png)

Extraction runs write `crop_preview.png` beside the exported assets. Red boxes show the final padded crop area, faint white boxes show the raw visual detection, and numbered labels map the preview back to `metadata.json`. This makes tight cuts visible before the files move into Figma, apps, or game engines.

## Codex Skill

The installable Codex skill is included at `skill/visual-asset-pipeline`.

```bash
cp -R skill/visual-asset-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Then invoke it in Codex:

```text
Use $visual-asset-pipeline to extract this character sheet into transparent PNG, WebP, sprite sheet, ZIP, and metadata.
```

## Asset Profiles

| Profile | Best For | Normalization Intent |
| --- | --- | --- |
| `icon` | Symbol packs, app icons, badges | Square canvas, centered symbol, consistent padding |
| `character` | Character poses, mascots, avatar sheets | Preserve full body, align visual weight, avoid cropped limbs |
| `sprite` | Game frames, props, effects | Frame-ready scale, sprite sheet export, atlas metadata |
| `web` | Landing-page images, logos, illustrations | Preserve useful shape, responsive export sizes |
| `ui` | Buttons, badges, states, app visuals | Group variants and keep state-friendly naming |
| `sticker` | Stickers, emotes, decals | Preserve outline/glow and generous transparent padding |
| `auto` | Unknown or mixed sheets | Use conservative general-purpose extraction |

## Architecture

```text
src/visual_asset_pipeline/
├── analysis.py        # input inspection and layout metadata
├── detection.py       # visual asset localization
├── segmentation.py    # foreground masks and background removal
├── cleanup.py         # captions, guide lines, artifacts, and noise
├── normalization.py   # optical centering and profile-aware canvas export
├── validation.py      # quality gates, duplicates, and style checks
├── naming.py          # deterministic semantic filenames
├── packaging.py       # image exports, metadata, reports, sprites, ZIP
└── cli.py             # command line interface
```

More detail:

- [Architecture](docs/architecture.md)
- [Library recommendations](docs/library-recommendations.md)
- [Name candidates](docs/name-candidates.md)

## Optional Enhancements

The default pipeline runs locally with Pillow, NumPy, and scikit-image. Production deployments can swap in:

- SAM, RMBG, or rembg for segmentation
- CLIP, SigLIP, DINOv2, or a multimodal LLM for semantic naming and duplicate detection
- OCR for stronger caption and label removal
- vtracer, potrace, Illustrator, or a hosted vectorization service for SVG output
- Figma, React, Flutter, iOS, Android, Unity, Godot, and TexturePacker code generators

## Development

```bash
python3 -m pip install -e ".[dev]"
pytest
npm pack --dry-run
```

## Roadmap

- Profile-specific metadata: pivots, hitboxes, 9-slice, state groups, animation groups
- Model-backed extraction adapters
- True vector export pipeline
- Multimodal semantic naming review UI
- Figma plugin export
- Framework and game-engine codegen
- Visual regression benchmark suite with real-world asset sheets
