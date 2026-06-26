from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ASSET_PROFILES = ("auto", "icon", "character", "sprite", "web", "ui", "sticker")


@dataclass(frozen=True)
class BoundingBox:
    """Integer bounding box in x, y, width, height form."""

    x: int
    y: int
    w: int
    h: int

    @classmethod
    def from_xyxy(cls, x1: int, y1: int, x2: int, y2: int) -> "BoundingBox":
        return cls(int(x1), int(y1), max(0, int(x2) - int(x1)), max(0, int(y2) - int(y1)))

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def area(self) -> int:
        return max(0, self.w) * max(0, self.h)

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2.0, self.y + self.h / 2.0

    @property
    def aspect(self) -> float:
        return self.w / max(1, self.h)

    def expand(self, px: int | float) -> "BoundingBox":
        amount = int(round(px))
        return BoundingBox(self.x - amount, self.y - amount, self.w + amount * 2, self.h + amount * 2)

    def clamp(self, width: int, height: int) -> "BoundingBox":
        x1 = max(0, min(width, self.x))
        y1 = max(0, min(height, self.y))
        x2 = max(x1, min(width, self.x2))
        y2 = max(y1, min(height, self.y2))
        return BoundingBox.from_xyxy(x1, y1, x2, y2)

    def intersects(self, other: "BoundingBox") -> bool:
        return self.x < other.x2 and self.x2 > other.x and self.y < other.y2 and self.y2 > other.y

    def union(self, other: "BoundingBox") -> "BoundingBox":
        return BoundingBox.from_xyxy(
            min(self.x, other.x),
            min(self.y, other.y),
            max(self.x2, other.x2),
            max(self.y2, other.y2),
        )

    def to_tuple(self) -> tuple[int, int, int, int]:
        return self.x, self.y, self.w, self.h

    def to_dict(self) -> dict[str, int]:
        return {"x": self.x, "y": self.y, "width": self.w, "height": self.h}


@dataclass
class AssetCandidate:
    """Detected source asset region before cleanup and normalization."""

    index: int
    box: BoundingBox
    confidence: float = 0.0
    row: int | None = None
    column: int | None = None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "bounding_box": self.box.to_dict(),
            "confidence": round(float(self.confidence), 4),
            "row": self.row,
            "column": self.column,
            "notes": self.notes,
        }


@dataclass
class InputAnalysis:
    """Source sheet analysis metadata."""

    width: int
    height: int
    background: dict[str, Any]
    estimated_asset_count: int = 0
    estimated_rows: int | None = None
    estimated_columns: int | None = None
    spacing: dict[str, float | None] = field(default_factory=dict)
    possible_text: bool = False
    decorations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "background": self.background,
            "estimated_asset_count": self.estimated_asset_count,
            "estimated_rows": self.estimated_rows,
            "estimated_columns": self.estimated_columns,
            "spacing": self.spacing,
            "possible_text": self.possible_text,
            "decorations": self.decorations,
            "warnings": self.warnings,
        }


@dataclass
class PipelineConfig:
    """User-facing pipeline options."""

    profile: str = "auto"
    sizes: tuple[int, ...] = (128, 256, 512, 1024)
    padding_ratio: float = 0.16
    min_area_ratio: float = 0.00018
    expected_count: int | None = None
    prompt: str | None = None
    names_file: Path | None = None
    webp: bool = True
    sprite: bool = True
    zip_output: bool = True
    svg: bool = False
    repair: bool = False
    duplicate_threshold: int = 7
    category: str | None = None

    def normalized_sizes(self) -> tuple[int, ...]:
        return tuple(sorted({int(size) for size in self.sizes if int(size) > 0}))

    def normalized_profile(self) -> str:
        profile = self.profile.lower().strip()
        if profile not in ASSET_PROFILES:
            return "auto"
        return profile

    def effective_padding_ratio(self) -> float:
        """Tune canvas padding by asset class while keeping a user override respected."""

        if self.padding_ratio != 0.16:
            return self.padding_ratio
        defaults = {
            "icon": 0.16,
            "character": 0.12,
            "sprite": 0.08,
            "web": 0.10,
            "ui": 0.10,
            "sticker": 0.18,
            "auto": 0.16,
        }
        return defaults[self.normalized_profile()]


@dataclass
class ValidationIssue:
    code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "severity": self.severity, "message": self.message}


@dataclass
class AssetRecord:
    """Fully processed visual asset and metadata used during packaging."""

    candidate: AssetCandidate
    name: str
    clean_width: int
    clean_height: int
    normalized_images: dict[int, Any]
    dominant_colors: list[str]
    tags: list[str]
    issues: list[ValidationIssue] = field(default_factory=list)
    duplicate_of: str | None = None
    cleanup_notes: list[str] = field(default_factory=list)

    def quality_score(self) -> float:
        penalty = sum(3.0 if issue.severity == "error" else 1.0 for issue in self.issues)
        return self.candidate.confidence + (self.candidate.box.area / 100000.0) - penalty
