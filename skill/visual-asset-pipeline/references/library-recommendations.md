# Library Recommendations

## Required Runtime

- Python 3.10+
- Pillow: image loading, alpha compositing, export.
- NumPy: pixel operations.
- scikit-image: morphology, connected components, edges, blur metrics.

Install:

```bash
python3 -m pip install -r scripts/requirements.txt
```

## Optional Production Enhancements

- `rembg` or a house background-removal model for complex photographic backgrounds.
- Segment Anything or RMBG for high-quality segmentation.
- CLIP, SigLIP, DINOv2, or OpenAI vision models for semantic naming and duplicate/style embeddings.
- `pytesseract` or a cloud OCR API for stronger caption and label removal.
- `vtracer`, `potrace`, or Illustrator/Vectorizer.ai integration for true SVG conversion.
- OpenCV for faster contour handling and inpainting.
- `pydantic` for stricter metadata schemas if the package becomes a public library.
- `pytest` and visual regression snapshots for long-term quality gates.

## Suggested Future Improvements

- Add a learned detector trained on visual asset sheets, stickers, app icons, character sheets, sprites, game UI atlases, and hand-drawn packs.
- Add multimodal LLM naming with user-editable review before final packaging.
- Add Figma plugin export: frames, components, variants, and auto-layout metadata.
- Add React/Flutter/iOS/Android codegen: TypeScript exports, Flutter asset registry, iOS asset catalogs, Android drawable folders.
- Add atlas packing algorithms for game engines: TexturePacker-compatible JSON, Unity `.meta`, Godot `.tres`.
- Add iterative repair loop using generative fill for clipped edges or missing strokes.
- Add style clustering to split mixed-style sheets into separate asset packages.
- Add CI visual tests using synthetic and real-world visual asset sheets.
