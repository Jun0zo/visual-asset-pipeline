# Visual Asset Pipeline

![Visual Asset Pipeline hero](../assets/hero.png)

**Visual Asset Pipeline** convierte prompts, hojas de assets, capturas de paginas web, bocetos y carpetas de imagenes en paquetes de assets listos para produccion.

[English](../../README.md) | [한국어](../../README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Español](README.es.md)

## Assets Soportados

No se limita a iconos. Los iconos son solo un profile; tambien soporta personajes, sprites, assets web, UI, stickers y assets para motores de juego.

![Asset profiles](../assets/asset-profiles.png)

## Diferenciadores

- Detecta assets visualmente, no solo por una cuadricula perfecta.
- Empaqueta PNG, WebP, SVG opcional, sprite sheets, metadata, reportes de validacion, crop previews y ZIP.
- Preserva antialiasing, sombras, outlines, glows y centrado optico.
- Incluye naming, validacion, deteccion de duplicados y consistencia visual como parte del flujo.

## Instalacion

```bash
git clone https://github.com/Jun0zo/visual-asset-pipeline.git
cd visual-asset-pipeline
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

### npm / npx

```bash
npm install -g github:Jun0zo/visual-asset-pipeline
vap --help
```

```bash
npx --yes github:Jun0zo/visual-asset-pipeline --help
```

## Uso Rapido

```bash
visual-asset-pipeline extract \
  --input work/asset-sheet.png \
  --output work/export \
  --profile icon \
  --expected-count 48 \
  --sizes 128,256,512,1024
```

## Salida

![Output package](../assets/package-outputs.png)

El paquete incluye PNG, WebP, SVG opcional, sprite sheets, `metadata.json`, `validation_report.json`, contact sheet y ZIP.

## Codex Skill

```bash
cp -R skill/visual-asset-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
```
