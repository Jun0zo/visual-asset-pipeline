---
name: visual-asset-pipeline
description: Generate, extract, repair, normalize, validate, semantically name, and package production-ready visual assets from prompts, image sheets, webpage captures, sketches, character sheets, sprite sheets, icon packs, UI asset boards, sticker sheets, or folders of images. Use for Figma, React, Flutter, iOS, Android, web, and game-engine asset exports including transparent PNG/WebP, optional SVG/vectorization, sprite sheets, ZIP packaging, metadata.json, validation reports, duplicate detection, style validation, and profile-aware normalization.
---

# Visual Asset Pipeline

## Overview

Use this skill to turn prompt-generated sheets or source images containing many visual assets into production-ready asset packages. Icons are only one profile; also support characters, sprites, web assets, UI components, stickers, and mixed sheets.

## Workflow

1. Choose mode: `brief`, `extract`, `repair`, `normalize`, or `package`.
2. Choose profile: `auto`, `icon`, `character`, `sprite`, `web`, `ui`, or `sticker`.
3. For prompt-only work, run `brief`, generate the image sheet with the available image model, then run `extract`.
4. For image input, inspect the image first. Note likely layout, background, text/captions, decorations, asset type, and expected count.
5. Run `scripts/run_visual_pipeline.py`. Pass the user's original prompt with `--prompt` whenever available.
6. Review `metadata.json`, `validation_report.json`, `contact_sheet.png`, and `crop_preview.png`. In `crop_preview.png`, red boxes show the final padded crop area and faint white boxes show the raw detected bounds.
7. If validation flags cropped edges, captions, or artifacts, rerun with adjusted `--profile`, `--padding`, `--min-area-ratio`, or `--expected-count`.
8. Return the ZIP plus important warnings. Do not claim SVG vectorization unless actual SVG files were produced.

## Quick Start

Create a generation brief:

```bash
python3 scripts/run_visual_pipeline.py brief \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --profile icon \
  --output /path/to/export
```

Extract a sheet:

```bash
python3 scripts/run_visual_pipeline.py extract \
  --input /path/to/asset-sheet.png \
  --output /path/to/export \
  --profile character \
  --sizes 256,512,1024 \
  --prompt "12 fantasy character poses" \
  --expected-count 12
```

Normalize an existing folder:

```bash
python3 scripts/run_visual_pipeline.py normalize \
  --input /path/to/raw-assets \
  --output /path/to/package \
  --profile web \
  --sizes 256,512
```

## Profile Rules

- `icon`: square canvas, centered symbol, consistent padding.
- `character`: preserve full body and avoid cropped limbs; future adapters should emit pivots.
- `sprite`: keep frame-ready scale and package atlas JSON.
- `web`: preserve useful shape and responsive export sizes.
- `ui`: keep state/variant-friendly names.
- `sticker`: preserve outline, glow, and generous transparent padding.
- `auto`: use conservative general-purpose extraction.

## Quality Rules

- Never crop tightly. Preserve glows, outlines, shadows, and antialiasing.
- Use `crop_preview.png` to make crop decisions visible before handing assets to Figma, apps, or game engines.
- Treat grid detection as a hint, not truth.
- Ignore labels, captions, and nearby decorative text whenever possible.
- Prefer transparent PNG/WebP outputs for app and design usage.
- Use semantic filenames such as `forest_green_badge.png` or `character_idle_pose.png`; never use `asset1.png` or `icon1.png`.
- Surface validation warnings in the final response.

## References

- Read `references/architecture.md` before modifying pipeline internals.
- Read `references/library-recommendations.md` when choosing optional production dependencies.
