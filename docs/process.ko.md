# Visual Asset Pipeline 프로세스 설명

이 프로젝트의 핵심은 단순히 이미지를 자르는 것이 아니라, 디자이너나 개발자가 바로 쓸 수 있는 **에셋 패키지**를 자동으로 만드는 것입니다.

## 한 줄 요약

프롬프트나 이미지 시트에서 여러 시각 에셋을 찾아내고, 배경을 제거하고, 크기를 맞추고, 품질을 검사한 뒤, 앱/웹/게임/디자인툴에서 바로 쓰는 파일 묶음으로 내보냅니다.

## 왜 아이콘에만 한정하지 않았나

처음 아이디어는 icon pack 자동화였지만, 실제로 필요한 작업은 더 넓습니다.

- 아이콘 팩
- 캐릭터 시트
- 스프라이트 시트
- 웹페이지 안의 시각 에셋
- UI 버튼/배지/state variant
- 스티커/이모트/투명 컷아웃
- 게임 엔진용 atlas

그래서 프로젝트를 **Icon Asset Pipeline**이 아니라 **Visual Asset Pipeline**으로 확장했습니다. 아이콘은 이제 `profile=icon`인 한 가지 사용 사례입니다.

## 전체 흐름

```text
Prompt / Sheet / Screenshot / Folder
        ↓
Analyze
        ↓
Locate
        ↓
Segment
        ↓
Cleanup / Repair
        ↓
Normalize
        ↓
Validate
        ↓
Name
        ↓
Package
```

## 1. Analyze

입력 이미지를 먼저 분석합니다.

- 배경이 투명한지, 단색인지, 복잡한지
- grid가 있는지
- 몇 개의 에셋이 있을 것 같은지
- 텍스트/번호/캡션이 섞여 있는지
- 아이콘인지 캐릭터인지 스프라이트인지

이 단계는 “무작정 자르기” 전에 판을 읽는 단계입니다.

## 2. Locate

각 에셋의 위치를 찾습니다.

중요한 점은 **균등 grid만 믿지 않는 것**입니다. 실제 이미지 시트는 간격이 들쭉날쭉하거나, 에셋마다 크기가 다르거나, 텍스트가 붙어 있을 수 있습니다.

그래서 기본 구현은 foreground component를 찾고, grid는 참고 정보로만 사용합니다.

## 3. Segment

배경을 제거해서 투명 PNG/WebP로 만들 준비를 합니다.

이때 보존해야 하는 것:

- anti-aliasing
- 얇은 stroke
- outline
- glow
- shadow
- 반투명 edge

## 4. Cleanup / Repair

에셋 주변의 불필요한 요소를 정리합니다.

- 숫자
- 캡션
- 라벨
- guide line
- 작은 노이즈
- 배경 잔여물

심하게 잘린 에셋이나 빠진 부분은 나중에 generative repair adapter로 확장할 수 있게 설계했습니다.

## 5. Normalize

에셋을 일정한 canvas에 맞춥니다.

profile마다 기준이 다릅니다.

- `icon`: 정사각형 canvas, 중앙 정렬, 일정 padding
- `character`: 전체 몸이 잘리지 않게 보존, pose/pivot 확장 가능
- `sprite`: frame scale과 atlas export 중심
- `web`: 원본 비율과 responsive export 중심
- `ui`: 상태 variant와 naming 중심
- `sticker`: outline/glow 보존을 위한 넉넉한 padding

## 6. Validate

자동 품질 검사를 합니다.

- 가장자리에서 잘렸는지
- blur가 심한지
- 중복 에셋이 있는지
- 텍스트 잔여물이 있는지
- 배경 artifact가 남았는지
- 스타일이 너무 섞여 있는지

검증 결과는 `validation_report.json`에 남깁니다.

## 7. Name

파일 이름은 `asset1.png`처럼 만들지 않습니다.

기본 구현은 프롬프트, 색, 형태, 위치 정보를 사용해 의미 있는 이름을 만듭니다. 이후 multimodal model을 붙이면 더 정확한 semantic naming이 가능합니다.

예:

- `forest_green_badge.png`
- `character_idle_pose.png`
- `ui_blue_button.png`
- `sprite_fire_effect.png`

## 8. Package

마지막으로 바로 쓸 수 있는 패키지를 만듭니다.

- PNG
- WebP
- optional SVG
- sprite sheet
- sprite atlas JSON
- `metadata.json`
- `validation_report.json`
- `contact_sheet.png`
- `visual_asset_package.zip`

목표는 Figma, React, Flutter, iOS, Android, Web, Unity, Godot 같은 환경에서 수동 정리 없이 바로 가져다 쓰는 것입니다.

## 설계 원칙

각 단계는 독립 모듈입니다.

- detection만 YOLO/SAM/GroundingDINO로 교체 가능
- segmentation만 rembg/SAM/RMBG로 교체 가능
- naming만 vision model/CLIP/LLM으로 교체 가능
- packaging만 Figma/Unity/Godot exporter로 확장 가능

즉, 지금은 로컬 CV 기반의 안정적인 기본형이고, 나중에 모델 기반 고급형으로 자연스럽게 커질 수 있습니다.
