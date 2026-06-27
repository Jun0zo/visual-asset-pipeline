# Visual Asset Pipeline

![Visual Asset Pipeline hero](../assets/hero.png)

**Visual Asset Pipeline** 可以把提示词、素材图集、网页截图、草图或图片文件夹转换为可直接用于生产环境的视觉素材包。

[English](../../README.md) | [한국어](../../README.ko.md) | [日本語](README.ja.md) | [简体中文](README.zh-CN.md) | [Español](README.es.md)

## 支持的素材

它不只处理图标。图标只是其中一个 profile，还支持角色、精灵图、网页视觉素材、UI 素材、贴纸和游戏引擎素材。

![Asset profiles](../assets/asset-profiles.png)

## 差异化特点

- 不只依赖完美网格，而是根据视觉 foreground component 检测素材。
- 输出 PNG、WebP、可选 SVG、sprite sheet、metadata、validation report、crop preview 和 ZIP。
- 尽量保留抗锯齿、阴影、outline、glow 和 optical centering。
- 把命名、验证、重复检测和风格一致性检查放进同一条流水线。

## 安装

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

## 快速开始

```bash
visual-asset-pipeline extract \
  --input work/asset-sheet.png \
  --output work/export \
  --profile icon \
  --expected-count 48 \
  --sizes 128,256,512,1024
```

## 输出

![Output package](../assets/package-outputs.png)

输出包包含 PNG、WebP、可选 SVG、sprite sheet、`metadata.json`、`validation_report.json`、contact sheet 和 ZIP 压缩包。

## Codex Skill

```bash
cp -R skill/visual-asset-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
```
