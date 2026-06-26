# Icon Asset Pipeline Architecture

## Folder Structure

```text
icon-asset-pipeline/
├── SKILL.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── architecture.md
│   └── library-recommendations.md
└── scripts/
    ├── requirements.txt
    ├── run_icon_pipeline.py
    ├── icon_asset_pipeline/
    │   ├── analysis.py
    │   ├── cleanup.py
    │   ├── detection.py
    │   ├── generation.py
    │   ├── models.py
    │   ├── naming.py
    │   ├── normalization.py
    │   ├── packaging.py
    │   ├── pipeline.py
    │   ├── segmentation.py
    │   └── validation.py
    └── tests/
        └── test_pipeline_smoke.py
```

## Function Descriptions

- `generation.build_generation_brief`: Convert a user prompt into a sheet-generation prompt and export spec.
- `analysis.analyze_input`: Estimate background, layout, row/column hints, possible text, and icon count.
- `segmentation.foreground_mask`: Build a foreground mask from alpha, background distance, saturation, and edge cues.
- `segmentation.remove_background`: Convert sheet or crop backgrounds into transparent alpha while preserving antialiasing.
- `detection.detect_icon_candidates`: Find icon bounding boxes from visual components, not equal grid cells.
- `cleanup.clean_icon_crop`: Remove text-like captions, guide lines, tiny noise, and background residue from a crop.
- `normalization.normalize_icon`: Place the cleaned icon on square transparent canvases at requested sizes using optical center.
- `validation.validate_icon`: Detect cropped edges, blur, caption residue, nontransparent borders, and alpha quality issues.
- `validation.find_duplicates`: Use a deterministic perceptual hash to flag duplicate icons.
- `validation.style_validation`: Compare palette, alpha coverage, stroke-density proxy, and lighting/shadow proxies across the pack.
- `naming.generate_icon_names`: Create stable semantic filenames from optional names, prompt/category hints, and visual descriptors.
- `packaging.write_package`: Export PNG, WebP, optional SVG, sprite sheets, metadata, validation reports, contact sheet, and ZIP.
- `pipeline.run_extract_pipeline`: Orchestrate analysis, detection, cleanup, normalization, validation, naming, and packaging.

## Replaceable Components

The default implementation intentionally uses conservative local computer-vision heuristics. In a production deployment, replace individual modules without changing the CLI contract:

- Detection: replace `detection.detect_icon_candidates` with SAM, GroundingDINO, YOLO, or a custom detector.
- Segmentation: replace `segmentation.remove_background` with rembg, RMBG, SAM masks, or Photoshop API.
- Naming: replace `naming.generate_icon_names` with a multimodal LLM/CLIP captioner.
- Duplicate detection: replace deterministic dHash with CLIP/DINOv2 embeddings.
- SVG export: replace optional CLI vectorizers with a house vectorization service.

## Example Workflow

```bash
python3 scripts/run_icon_pipeline.py brief \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --output work/forest-icons

# Generate the sheet from work/forest-icons/generation_brief.json with the active image model.

python3 scripts/run_icon_pipeline.py extract \
  --input work/forest-icons/generated-sheet.png \
  --output work/forest-icons/export \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --expected-count 48 \
  --sizes 128,256,512,1024 \
  --padding 0.16 \
  --webp \
  --sprite \
  --zip
```

## Error Handling Strategy

- Non-grid layouts: use connected foreground grouping and grid only as metadata.
- Overlapping icons: keep a merged candidate and emit `overlap_or_merge` warning.
- Partial icons: preserve source crop, add edge padding, and flag `edge_contact`.
- Hand-drawn icons: use lenient antialiasing and cleanup thresholds.
- Uneven spacing: adaptive padding and component grouping.
- Mixed styles: export all icons but flag style variance in `validation_report.json`.
