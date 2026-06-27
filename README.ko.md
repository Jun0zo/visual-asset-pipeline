# Visual Asset Pipeline

![Visual Asset Pipeline hero](docs/assets/hero.png)

**Visual Asset Pipeline**은 프롬프트, 여러 에셋이 들어 있는 이미지 시트, 웹페이지 캡처, 스케치, 이미지 폴더를 바로 쓸 수 있는 프로덕션 에셋 패키지로 변환하는 파이프라인입니다.

[English](README.md) | [한국어](README.ko.md) | [日本語](docs/i18n/README.ja.md) | [简体中文](docs/i18n/README.zh-CN.md) | [Español](docs/i18n/README.es.md)

> 현재 상태: alpha. 로컬 CV 기반 파이프라인은 동작하며, segmentation, semantic naming, OCR, SVG 변환은 교체 가능한 어댑터로 확장하도록 설계되어 있습니다.

## 지원 범위

아이콘만을 위한 도구가 아닙니다. 아이콘은 여러 profile 중 하나입니다.

- 아이콘, 심볼 팩
- 캐릭터 시트, 포즈 보드
- 스프라이트 시트, 게임 오브젝트
- 웹페이지/랜딩페이지 시각 에셋
- UI 배지, 버튼, 상태 variant, 앱 에셋
- 스티커, 이모트, 투명 컷아웃

![Asset profiles](docs/assets/asset-profiles.png)

## 차별점

- 완벽한 grid만 전제로 하지 않고, 지저분한 시각 입력에서도 foreground component를 기준으로 탐지합니다.
- PNG, WebP, 선택 SVG, sprite sheet, metadata, validation report, contact sheet, crop preview, ZIP까지 실제 downstream 사용에 맞게 패키징합니다.
- anti-aliasing, 그림자, outline, glow, optical centering 같은 품질 요소를 보존하도록 설계했습니다.
- 파일명 생성, 검증, 중복 감지, 스타일 일관성 점검을 후처리 잡일이 아니라 파이프라인 일부로 다룹니다.
- Codex skill, Python CLI, npm global CLI, `npx` one-off 실행을 모두 지원합니다.

## 파이프라인

![Pipeline flow](docs/assets/pipeline-flow.png)

더 쉬운 설명은 [Visual Asset Pipeline 프로세스 설명](docs/process.ko.md)에 정리했습니다.

1. 입력 분석: 레이아웃, 배경, 텍스트, 간격, grid 힌트, 예상 개수.
2. 시각적 위치 탐지: 동일 grid만 믿지 않고 foreground component를 찾습니다.
3. 분리/배경 제거: anti-aliasing, 그림자, outline, glow를 최대한 보존합니다.
4. 정리: 캡션, 라벨, 숫자, 가이드라인, 작은 노이즈를 제거합니다.
5. 정규화: profile별 padding, optical center, 요청 size를 적용합니다.
6. 검증: 잘림, blur, duplicate, 텍스트 잔여물, 배경 artifact, 스타일 편차를 감지합니다.
7. 패키징: PNG, WebP, 선택 SVG, sprite sheet, metadata, validation report, contact sheet, ZIP을 만듭니다.

## 설치

### Python

```bash
git clone https://github.com/Jun0zo/visual-asset-pipeline.git
cd visual-asset-pipeline
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

확인:

```bash
visual-asset-pipeline --help
pytest
```

짧은 alias도 제공합니다.

```bash
vap --help
```

### npm / npx

npm 패키지는 Python 파이프라인을 실행하는 작은 Node.js CLI wrapper를 제공합니다. 설치 시 가능하면 패키지 내부 `.venv`를 만들고 Python dependency를 설치합니다.

```bash
npm install -g github:Jun0zo/visual-asset-pipeline
vap --help
```

한 번만 실행하려면:

```bash
npx --yes github:Jun0zo/visual-asset-pipeline --help
```

Python 환경을 직접 관리하고 싶다면 `VAP_SKIP_PYTHON_INSTALL=1`을 설정한 뒤 npm install을 실행하면 됩니다.

## 빠른 사용 예시

프롬프트에서 생성 brief 만들기:

```bash
visual-asset-pipeline brief \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --profile icon \
  --output work/forest-assets
```

생성된 이미지 시트에서 에셋 추출:

```bash
visual-asset-pipeline extract \
  --input work/forest-assets/generated-sheet.png \
  --output work/forest-assets/export \
  --prompt "Create 48 forest exploration icons in watercolor style." \
  --profile icon \
  --expected-count 48 \
  --sizes 128,256,512,1024
```

이미 분리된 이미지 폴더 정규화:

```bash
visual-asset-pipeline normalize \
  --input work/raw-assets \
  --output work/normalized-assets \
  --profile web \
  --sizes 256,512
```

## 출력물

![Output package](docs/assets/package-outputs.png)

- `png/<size>/*.png`
- `webp/<size>/*.webp`
- `svg/*.svg` optional
- `sprites/sprite_<size>.png`
- `sprites/sprite_<size>.json`
- `metadata.json`
- `validation_report.json`
- `contact_sheet.png`
- `crop_preview.png`
- `visual_asset_package.zip`

## Crop Preview Overlay

![Crop preview overlay](docs/assets/crop-preview-overlay.png)

추출을 실행하면 export 폴더에 `crop_preview.png`도 함께 생성됩니다. 빨간 박스는 padding이 적용된 최종 crop 영역이고, 옅은 흰 박스는 원래 detection 영역입니다. 번호는 metadata와 연결되므로 어떤 에셋이 어떻게 잘릴지 바로 확인할 수 있습니다.

## Codex Skill 설치

Skill은 `skill/visual-asset-pipeline`에 포함되어 있습니다.

```bash
cp -R skill/visual-asset-pipeline "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Codex에서 이렇게 사용할 수 있습니다.

```text
Use $visual-asset-pipeline to extract this character sheet into transparent PNG, WebP, sprite sheet, ZIP, and metadata.
```

## Profile

| Profile | 용도 |
| --- | --- |
| `icon` | 아이콘, 심볼, 배지 |
| `character` | 캐릭터 포즈, 마스코트, 아바타 |
| `sprite` | 게임 프레임, prop, effect |
| `web` | 랜딩페이지 이미지, 로고, 일러스트 |
| `ui` | 버튼, 배지, 상태 variant |
| `sticker` | 스티커, 이모트, outline/glow cutout |
| `auto` | 혼합 또는 알 수 없는 시트 |

## 개발

```bash
python3 -m pip install -e ".[dev]"
pytest
npm pack --dry-run
```
