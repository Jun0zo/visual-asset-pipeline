#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from textwrap import wrap

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"

BG = "#0b1118"
PANEL = "#111a24"
PANEL_2 = "#142130"
LINE = "#2b3a4c"
TEXT = "#edf4fb"
MUTED = "#9fb0c3"
BLUE = "#4aa3ff"
MINT = "#6ee7c8"
CORAL = "#ff7f6e"
YELLOW = "#ffd166"
PURPLE = "#a78bfa"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    name = "Arial Bold.ttf" if bold else "Arial.ttf"
    path = Path("/System/Library/Fonts/Supplemental") / name
    return ImageFont.truetype(str(path), size=size)


def canvas(width: int = 1600, height: int = 900) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    for i in range(height):
        shade = int(12 + i / height * 10)
        draw.line((0, i, width, i), fill=(shade, shade + 6, shade + 13))
    return image, draw


def rr(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill: str, outline: str | None = LINE, width: int = 2) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def centered(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, fnt: ImageFont.FreeTypeFont, fill: str = TEXT) -> None:
    box = draw.textbbox((0, 0), text, font=fnt)
    draw.text((xy[0] - (box[2] - box[0]) / 2, xy[1] - (box[3] - box[1]) / 2), text, font=fnt, fill=fill)


def text_block(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt: ImageFont.FreeTypeFont, fill: str, max_chars: int, gap: int = 10) -> int:
    line_y = y
    for line in wrap(text, width=max_chars):
        draw.text((x, line_y), line, font=fnt, fill=fill)
        line_y += fnt.size + gap
    return line_y


def chip(draw: ImageDraw.ImageDraw, x: int, y: int, label: str, color: str) -> int:
    fnt = font(24, True)
    box = draw.textbbox((0, 0), label, font=fnt)
    w = box[2] - box[0] + 34
    rr(draw, (x, y, x + w, y + 48), 18, "#182536", color, 2)
    centered(draw, (x + w // 2, y + 24), label, fnt, TEXT)
    return x + w + 14


def icon_grid(draw: ImageDraw.ImageDraw, x: int, y: int, size: int = 72, gap: int = 22) -> None:
    colors = [MINT, BLUE, CORAL, YELLOW, PURPLE, "#7dd3fc"]
    for i in range(6):
        cx = x + (i % 3) * (size + gap)
        cy = y + (i // 3) * (size + gap)
        rr(draw, (cx, cy, cx + size, cy + size), 18, "#0e1823", "#2d4055", 2)
        color = colors[i]
        if i == 0:
            draw.ellipse((cx + 18, cy + 18, cx + 54, cy + 54), fill=color)
        elif i == 1:
            draw.rounded_rectangle((cx + 18, cy + 20, cx + 54, cy + 52), radius=8, fill=color)
        elif i == 2:
            draw.polygon([(cx + 36, cy + 14), (cx + 58, cy + 56), (cx + 14, cy + 56)], fill=color)
        elif i == 3:
            draw.line((cx + 18, cy + 52, cx + 36, cy + 18, cx + 54, cy + 52), fill=color, width=8, joint="curve")
        elif i == 4:
            draw.pieslice((cx + 14, cy + 14, cx + 58, cy + 58), 25, 320, fill=color)
        else:
            draw.rectangle((cx + 20, cy + 20, cx + 52, cy + 52), fill=color)


def draw_character(draw: ImageDraw.ImageDraw, x: int, y: int, scale: float = 1.0) -> None:
    s = scale
    draw.ellipse((x + 42 * s, y, x + 102 * s, y + 60 * s), fill=YELLOW)
    draw.rounded_rectangle((x + 28 * s, y + 58 * s, x + 118 * s, y + 154 * s), radius=int(28 * s), fill=BLUE)
    draw.line((x + 32 * s, y + 92 * s, x, y + 128 * s), fill=MINT, width=int(12 * s))
    draw.line((x + 112 * s, y + 92 * s, x + 150 * s, y + 130 * s), fill=MINT, width=int(12 * s))
    draw.line((x + 58 * s, y + 150 * s, x + 42 * s, y + 214 * s), fill=CORAL, width=int(14 * s))
    draw.line((x + 88 * s, y + 150 * s, x + 110 * s, y + 214 * s), fill=CORAL, width=int(14 * s))


def hero() -> None:
    image, draw = canvas()
    draw.rectangle((40, 0, 270, 8), fill=CORAL)
    centered(draw, (800, 92), "Visual Asset Pipeline", font(72, True))
    centered(draw, (800, 158), "Prompts, sheets, webpages, and sketches into production-ready asset packs", font(32), MUTED)

    x = 120
    for label, color in [("icons", BLUE), ("characters", MINT), ("sprites", CORAL), ("web assets", YELLOW), ("UI", PURPLE), ("stickers", "#7dd3fc")]:
        x = chip(draw, x, 214, label, color)

    rr(draw, (110, 310, 460, 760), 28, PANEL, "#334155", 2)
    draw.text((145, 346), "Input", font=font(32, True), fill=TEXT)
    text_block(draw, 145, 396, "Prompts, asset sheets, webpage captures, game art boards, or folders of existing images.", font(24), MUTED, 28)
    icon_grid(draw, 150, 585, 76, 18)

    rr(draw, (560, 310, 1010, 760), 28, PANEL, "#334155", 2)
    draw.text((600, 346), "Pipeline", font=font(32, True), fill=TEXT)
    steps = ["analyze", "locate", "segment", "repair", "normalize", "validate", "name"]
    for i, step in enumerate(steps):
        y = 406 + i * 38
        draw.ellipse((604, y + 5, 622, y + 23), fill=[BLUE, MINT, CORAL, YELLOW, PURPLE, BLUE, MINT][i])
        draw.text((642, y), step, font=font(24, True), fill=TEXT)
    draw.line((865, 430, 948, 430), fill=BLUE, width=4)
    draw.line((948, 430, 948, 590), fill=BLUE, width=4)
    draw.line((865, 590, 948, 590), fill=BLUE, width=4)

    rr(draw, (1110, 310, 1490, 760), 28, PANEL, "#334155", 2)
    draw.text((1145, 346), "Output package", font=font(32, True), fill=TEXT)
    text_block(draw, 1145, 400, "PNG/WebP, optional SVG, sprite sheets, metadata.json, validation report, contact sheet, and ZIP.", font(24), MUTED, 28)
    for i, label in enumerate(["Figma", "React", "Flutter", "iOS", "Android", "Web", "Game engines"]):
        yy = 590 + (i // 2) * 46
        xx = 1148 + (i % 2) * 160
        chip(draw, xx, yy, label, [BLUE, MINT, CORAL, YELLOW, PURPLE, "#7dd3fc", MINT][i])

    image.save(OUT / "hero.png", quality=95)


def pipeline_flow() -> None:
    image, draw = canvas()
    centered(draw, (800, 78), "Pipeline Flow", font(60, True))
    centered(draw, (800, 130), "Every stage is replaceable: start with local CV, upgrade with ML models when needed.", font(28), MUTED)
    labels = [
        ("1 Analyze", "Layout, grid hints, background, text, expected count"),
        ("2 Locate", "Visual components, uneven spacing, non-grid sheets"),
        ("3 Segment", "Transparent alpha, preserve antialiasing and shadows"),
        ("4 Cleanup", "Labels, numbers, guide lines, artifacts"),
        ("5 Normalize", "Profile-aware padding, optical center, sizes"),
        ("6 Validate", "Crops, blur, duplicates, style variance"),
        ("7 Package", "PNG, WebP, SVG, sprites, metadata, ZIP"),
    ]
    y = 230
    for i, (title, desc) in enumerate(labels):
        x = 80 + (i % 4) * 380
        row_y = y + (i // 4) * 260
        color = [BLUE, MINT, CORAL, YELLOW, PURPLE, "#7dd3fc", MINT][i]
        rr(draw, (x, row_y, x + 310, row_y + 180), 24, PANEL, color, 3)
        draw.text((x + 24, row_y + 26), title, font=font(31, True), fill=TEXT)
        text_block(draw, x + 24, row_y + 78, desc, font(22), MUTED, 26, 6)
        if i < len(labels) - 1:
            if i == 3:
                start_x = x + 155
                end_x = 235
                mid_y = row_y + 220
                draw.line((start_x, row_y + 180, start_x, mid_y), fill=LINE, width=5)
                draw.line((start_x, mid_y, end_x, mid_y), fill=LINE, width=5)
                draw.line((end_x, mid_y, end_x, row_y + 250), fill=LINE, width=5)
                draw.polygon([(end_x, row_y + 250), (end_x - 10, row_y + 232), (end_x + 10, row_y + 232)], fill=LINE)
            else:
                draw.line((x + 310, row_y + 90, x + 360, row_y + 90), fill=LINE, width=5)
                draw.polygon([(x + 360, row_y + 90), (x + 342, row_y + 80), (x + 342, row_y + 100)], fill=LINE)
    image.save(OUT / "pipeline-flow.png", quality=95)


def profiles() -> None:
    image, draw = canvas(1600, 1000)
    centered(draw, (800, 76), "Asset Profiles", font(60, True))
    centered(draw, (800, 128), "One pipeline, different normalization rules for different asset families.", font(28), MUTED)
    cards = [
        ("icon", "Square canvas, centered symbol, consistent padding.", BLUE),
        ("character", "Pose/feet alignment, no cropped limbs, pivot metadata.", MINT),
        ("sprite", "Frame-ready scale, atlas export, animation groups.", CORAL),
        ("web", "Preserve aspect ratio, responsive sizes, semantic names.", YELLOW),
        ("ui", "States and variants: hover, pressed, disabled, selected.", PURPLE),
        ("sticker", "Transparent cutout, outline/glow safe padding.", "#7dd3fc"),
    ]
    for i, (title, desc, color) in enumerate(cards):
        x = 90 + (i % 3) * 500
        y = 210 + (i // 3) * 350
        rr(draw, (x, y, x + 420, y + 280), 28, PANEL, "#334155", 2)
        display_title = "UI" if title == "ui" else title
        draw.text((x + 32, y + 30), display_title, font=font(38, True), fill=color)
        text_block(draw, x + 32, y + 86, desc, font(24), MUTED, 22, 6)
        if title == "character":
            draw_character(draw, x + 264, y + 98, 0.58)
        elif title == "sprite":
            for j in range(3):
                draw_character(draw, x + 216 + j * 64, y + 148 + (j % 2) * 8, 0.30)
        elif title == "web":
            rr(draw, (x + 238, y + 154, x + 372, y + 232), 16, "#0e1823", color, 3)
            draw.rectangle((x + 258, y + 178, x + 352, y + 190), fill=color)
            draw.rectangle((x + 258, y + 204, x + 328, y + 216), fill=MUTED)
        elif title == "ui":
            for j in range(3):
                rr(draw, (x + 234, y + 150 + j * 42, x + 376, y + 182 + j * 42), 14, "#0e1823", color, 2)
        elif title == "sticker":
            draw.ellipse((x + 255, y + 132, x + 365, y + 242), fill=color, outline=TEXT, width=8)
            draw.ellipse((x + 290, y + 166, x + 330, y + 206), fill=PANEL)
        else:
            icon_grid(draw, x + 254, y + 138, 48, 12)
    image.save(OUT / "asset-profiles.png", quality=95)


def package_outputs() -> None:
    image, draw = canvas()
    centered(draw, (800, 78), "Production Package", font(60, True))
    centered(draw, (800, 130), "Exports are immediately usable in design tools, app frameworks, websites, and game engines.", font(28), MUTED)
    rr(draw, (90, 210, 710, 760), 28, PANEL, "#334155", 2)
    draw.text((130, 250), "visual_asset_package.zip", font=font(34, True), fill=TEXT)
    tree = [
        "png/128/*.png",
        "png/512/*.png",
        "webp/512/*.webp",
        "svg/*.svg (optional)",
        "sprites/sprite_512.png",
        "sprites/sprite_512.json",
        "metadata.json",
        "validation_report.json",
        "contact_sheet.png",
    ]
    for i, item in enumerate(tree):
        y = 320 + i * 42
        draw.text((156, y), item, font=font(25), fill=MUTED)
        draw.line((130, y + 16, 146, y + 16), fill=LINE, width=3)
    rr(draw, (830, 210, 1510, 760), 28, PANEL, "#334155", 2)
    draw.text((870, 250), "Targets", font=font(34, True), fill=TEXT)
    targets = [
        ("Figma", "components, variants, frames"),
        ("React", "typed exports and imports"),
        ("Flutter", "pubspec asset registry"),
        ("iOS", "asset catalogs and @3x"),
        ("Android", "drawable density folders"),
        ("Web", "responsive images and sprites"),
        ("Games", "atlas JSON for engines"),
    ]
    for i, (target, desc) in enumerate(targets):
        x = 870 + (i % 2) * 320
        y = 320 + (i // 2) * 92
        draw.text((x, y), target, font=font(28, True), fill=[BLUE, MINT, CORAL, YELLOW, PURPLE, "#7dd3fc", MINT][i])
        draw.text((x, y + 34), desc, font=font(20), fill=MUTED)
    image.save(OUT / "package-outputs.png", quality=95)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    hero()
    pipeline_flow()
    profiles()
    package_outputs()
    print(f"Wrote README assets to {OUT}")


if __name__ == "__main__":
    main()
