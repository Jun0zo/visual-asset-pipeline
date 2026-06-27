# Visual Asset Pipeline

![Visual Asset Pipeline hero](../assets/hero.png)

**Visual Asset Pipeline** は、プロンプト、アセットシート、Webページのキャプチャ、スケッチ、画像フォルダを、すぐに使える制作向けアセットパッケージへ変換するパイプラインです。

[English](../../README.md) | [한국어](../../README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Español](README.es.md)

## Supported Assets

Icons are only one profile. The pipeline also targets characters, sprites, web visuals, UI assets, stickers, and game-engine assets.

![Asset profiles](../assets/asset-profiles.png)

## Install

```bash
git clone https://github.com/Jun0zo/visual-asset-pipeline.git
cd visual-asset-pipeline
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

## Quick Start

```bash
visual-asset-pipeline extract \
  --input work/asset-sheet.png \
  --output work/export \
  --profile icon \
  --expected-count 48 \
  --sizes 128,256,512,1024
```

## Output

![Output package](../assets/package-outputs.png)

The package includes PNG, WebP, optional SVG, sprite sheets, `metadata.json`, `validation_report.json`, a contact sheet, and a ZIP archive.

## Codex Skill

```bash
cp -R skill/visual-asset-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
```
