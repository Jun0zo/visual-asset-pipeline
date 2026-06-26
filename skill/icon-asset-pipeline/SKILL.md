---
name: icon-asset-pipeline
description: Generate, extract, repair, normalize, validate, name, and package production icon assets from a natural-language icon pack prompt or from a single image containing many icons. Use when the user needs a complete icon asset pipeline for Figma, React, Flutter, iOS, Android, web, game engines, sprite sheets, transparent PNG/WebP exports, optional SVG/vectorization, ZIP packaging, metadata.json, duplicate detection, style validation, semantic filenames, or icon sheet cleanup.
---

# Icon Asset Pipeline

## Overview

Use this skill to turn an icon-pack prompt or a source icon sheet into production-ready assets. Prefer the bundled Python pipeline for deterministic extraction, cleanup, normalization, validation, and packaging; use the active image-generation or vision tools only where semantic generation/naming benefits from model judgment.

## Workflow

1. Determine mode: `generate`, `extract`, `repair`, `normalize`, or `package`.
2. For prompt-only generation, create an icon sheet with the available image-generation tool, then run the extracted sheet through the bundled pipeline.
3. For image input, inspect the image first. Note likely rows, columns, background, text/captions, decorations, and expected count.
4. Run `scripts/run_icon_pipeline.py` on the source image. Pass the user's original prompt with `--prompt` whenever available to improve naming and metadata.
5. Review `metadata.json`, `validation_report.json`, and the contact sheet. If validation reports cropped icons, captions, or background artifacts, rerun with adjusted `--padding`, `--min-area-ratio`, or `--expected-count`.
6. Return the output ZIP plus key warnings. Do not claim SVG vectorization unless actual SVG files were produced.

## Quick Start

Extract and package an icon sheet:

```bash
python3 scripts/run_icon_pipeline.py extract \
  --input /path/to/icon-sheet.png \
  --output /path/to/export \
  --sizes 128,256,512,1024 \
  --prompt "48 forest exploration icons in watercolor style" \
  --expected-count 48
```

Create a generation brief when only a prompt is available:

```bash
python3 scripts/run_icon_pipeline.py brief \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --output /path/to/export
```

The brief gives a sheet-generation prompt. Generate the sheet with the available image model, then run `extract`.

## Modes

- **Generate icon pack**: Build a generation brief, generate a high-resolution sheet, then extract/package.
- **Extract icons**: Detect foreground components visually, group non-grid layouts, crop with adaptive padding, remove background, and export individual icons.
- **Repair icons**: Use `--repair` for conservative alpha cleanup, edge padding, and artifact removal. For missing parts or severe damage, use image editing/generative repair before rerunning extraction.
- **Normalize**: Produce square transparent canvases at requested sizes using optical centering and proportional scaling.
- **Package assets**: Export PNG, WebP, sprite sheets, metadata, validation reports, and a ZIP archive. Optional SVG is attempted only when a supported vectorizer is installed.

## Pipeline Contract

The implementation separates concerns into replaceable modules:

- `generation.py`: prompt-to-sheet brief construction.
- `analysis.py`: input analysis, grid estimate, background estimate, and layout metadata.
- `segmentation.py`: foreground mask and background removal.
- `detection.py`: visual icon candidate localization without relying purely on grids.
- `cleanup.py`: caption, guide-line, and noise removal.
- `normalization.py`: optical centering and multi-size canvas export.
- `validation.py`: cropped-edge, blur, duplicate, text-like artifact, background, and style checks.
- `naming.py`: semantic filename generation from prompt, optional names file, and visual descriptors.
- `packaging.py`: PNG/WebP/SVG, sprite sheets, metadata, reports, contact sheet, and ZIP export.

## Quality Rules

- Never crop tightly. Preserve glow, outlines, shadows, and antialiasing.
- Treat grid detection as a hint, not the source of truth.
- Ignore labels and captions whenever possible.
- Prefer transparent PNG/WebP outputs for application use.
- Use semantic names. If semantic vision naming is unavailable, use prompt/category/color/shape names such as `forest_green_round_badge.png`; never use `icon1.png`.
- Keep validation warnings visible in the final answer.

## References

- Read `references/architecture.md` before modifying the pipeline internals.
- Read `references/library-recommendations.md` when choosing optional production dependencies.
