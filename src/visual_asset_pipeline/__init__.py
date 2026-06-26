"""Production-oriented visual asset extraction and packaging pipeline."""

from .models import BoundingBox, PipelineConfig
from .pipeline import run_directory_pipeline, run_extract_pipeline

__all__ = [
    "BoundingBox",
    "PipelineConfig",
    "run_directory_pipeline",
    "run_extract_pipeline",
]
