from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Metadata:
    title: str
    byline: str
    date_mmddyyyy: str
    dek: str
    source: str
    slug: str
    last_name: str
    stem: str


@dataclass(slots=True)
class CropRegion:
    start_pt: float
    end_pt: float
    score: float


@dataclass(slots=True)
class OutputPaths:
    canonical_pdf: Path
    main_jpg: Path
    email_jpg: Path
    ppt_working_pdf: Path
    ppt_working_ai: Path
    ppt_assets_dir: Path
    ppt_segments_json: Path
    pptx: Path


@dataclass(slots=True)
class SlideSpec:
    image_path: Path
    title: str = ""
    subtitle: str = ""
