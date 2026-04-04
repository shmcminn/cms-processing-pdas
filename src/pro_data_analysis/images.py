from __future__ import annotations

from pathlib import Path

import fitz
import numpy as np
from PIL import Image

from .models import CropRegion
from .pdf_extract import PageText


def render_pdf_page(pdf_path: Path, target_width: int) -> Image.Image:
    doc = fitz.open(pdf_path)
    page = doc[0]
    zoom = target_width / page.rect.width
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
    return image


def save_main_jpeg(image: Image.Image, output_path: Path) -> None:
    image.save(output_path, format="JPEG", quality=92, optimize=True)


def save_email_jpeg(main_image: Image.Image, output_path: Path) -> None:
    scaled = main_image.resize((600, round(main_image.height * (600 / main_image.width))), Image.Resampling.LANCZOS)
    crop_height = min(500, scaled.height)
    email = scaled.crop((0, 0, 600, crop_height))
    if crop_height < 500:
        padded = Image.new("RGB", (600, 500), color="white")
        padded.paste(email, (0, 0))
        email = padded
    email.save(output_path, format="JPEG", quality=90, optimize=True)


def find_slide_regions(page_text: PageText, analysis_image: Image.Image, content_start: float) -> list[CropRegion]:
    grayscale = np.asarray(analysis_image.convert("L"))
    ink = (grayscale < 245).mean(axis=1)
    kernel = np.ones(35) / 35
    smoothed = np.convolve(ink, kernel, mode="same")
    pt_per_px = page_text.height / analysis_image.height
    low_ink_runs = _low_ink_runs(smoothed)
    candidates = [((start + end) / 2) * pt_per_px for start, end in low_ink_runs if end - start >= 8]

    min_slice = 300.0
    ideal_slice = 430.0
    max_slice = 520.0
    bottom = page_text.height - 24.0
    current = content_start
    regions: list[CropRegion] = []

    while bottom - current > max_slice:
        next_cut = _pick_cut(candidates, current, ideal_slice, min_slice, max_slice, bottom)
        regions.append(CropRegion(start_pt=current, end_pt=next_cut, score=1.0))
        current = max(current + 60.0, next_cut - 6.0)

    regions.append(CropRegion(start_pt=current, end_pt=bottom, score=1.0))
    return _merge_small_tail(regions)


def save_crop(image: Image.Image, page_height_pt: float, region: CropRegion, output_path: Path) -> None:
    top = max(0, round(region.start_pt / page_height_pt * image.height))
    bottom = min(image.height, round(region.end_pt / page_height_pt * image.height))
    cropped = image.crop((0, top, image.width, bottom))
    cropped.save(output_path, format="PNG")


def _low_ink_runs(smoothed_ink: np.ndarray) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    threshold = 0.012
    start: int | None = None
    for index, value in enumerate(smoothed_ink):
        if value <= threshold and start is None:
            start = index
        elif value > threshold and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(smoothed_ink) - 1))
    return runs


def _pick_cut(
    candidates: list[float],
    current: float,
    ideal_slice: float,
    min_slice: float,
    max_slice: float,
    bottom: float,
) -> float:
    floor = current + min_slice
    ceiling = min(current + max_slice, bottom - 80.0)
    target = current + ideal_slice
    viable = [candidate for candidate in candidates if floor <= candidate <= ceiling]
    if viable:
        return min(viable, key=lambda candidate: abs(candidate - target))
    return min(target, ceiling)


def _merge_small_tail(regions: list[CropRegion]) -> list[CropRegion]:
    if len(regions) < 2:
        return regions
    tail = regions[-1]
    if tail.end_pt - tail.start_pt >= 180:
        return regions
    previous = regions[-2]
    regions[-2] = CropRegion(start_pt=previous.start_pt, end_pt=tail.end_pt, score=1.0)
    return regions[:-1]
