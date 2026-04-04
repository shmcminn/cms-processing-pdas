from __future__ import annotations

import json
import shutil
from pathlib import Path

from .images import find_slide_regions_with_bottom, render_pdf_page, save_crop, save_email_jpeg, save_main_jpeg
from .models import CropRegion, OutputPaths, SlideSpec
from .pdf_extract import content_end_pt, content_start_pt, extract_metadata, extract_overlay_text, extract_source_from_blocks, load_page_text
from .ppt import build_pptx, export_working_files


def process_pdf(pdf_path: Path, output_dir: Path | None = None) -> OutputPaths:
    pdf_path = pdf_path.resolve()
    if output_dir is None:
        output_dir = pdf_path.parent
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    page_text = load_page_text(pdf_path)
    metadata = extract_metadata(page_text)
    metadata.source = extract_source_from_blocks(page_text.blocks) or metadata.source

    canonical_pdf = output_dir / f"{metadata.stem}.pdf"
    main_jpg = output_dir / f"{metadata.stem}.jpg"
    email_jpg = output_dir / f"EMAIL-{metadata.stem}.jpg"
    ppt_working_pdf = output_dir / f"PPT-{metadata.stem}.pdf"
    ppt_working_ai = output_dir / f"PPT-{metadata.stem}.ai"
    ppt_assets_dir = output_dir / f"PPT-{metadata.stem}-assets"
    ppt_segments_json = output_dir / f"PPT-{metadata.stem}.segments.json"
    pptx_path = output_dir / f"{metadata.stem}.pptx"

    shutil.copy2(pdf_path, canonical_pdf)

    main_image = render_pdf_page(pdf_path, target_width=2300)
    save_main_jpeg(main_image, main_jpg)
    save_email_jpeg(main_image, email_jpg)

    analysis_image = render_pdf_page(pdf_path, target_width=1800)
    content_start = content_start_pt(page_text)
    content_end = content_end_pt(page_text)
    auto_regions = find_slide_regions_with_bottom(page_text, analysis_image, content_start, content_end)
    regions = _load_or_write_regions(ppt_segments_json, auto_regions)

    ppt_assets_dir.mkdir(parents=True, exist_ok=True)
    for existing_png in ppt_assets_dir.glob("slide-*.png"):
        existing_png.unlink()

    slide_specs: list[SlideSpec] = []
    for index, region in enumerate(regions, start=2):
        overlay_title, overlay_subtitle, crop_start = extract_overlay_text(page_text.blocks, region)
        crop_path = ppt_assets_dir / f"slide-{index}.png"
        adjusted_region = region
        if crop_start > region.start_pt and crop_start < region.end_pt - 80:
            adjusted_region = CropRegion(start_pt=crop_start, end_pt=region.end_pt, score=region.score)
        save_crop(main_image, page_text.height, adjusted_region, crop_path)
        slide_specs.append(SlideSpec(image_path=crop_path, title=overlay_title, subtitle=overlay_subtitle))

    _write_region_manifest(ppt_segments_json, page_text.height, regions, slide_specs)
    build_pptx(metadata, slide_specs, pptx_path, ppt_assets_dir)
    export_working_files(metadata, slide_specs, ppt_working_pdf, ppt_working_ai)

    return OutputPaths(
        canonical_pdf=canonical_pdf,
        main_jpg=main_jpg,
        email_jpg=email_jpg,
        ppt_working_pdf=ppt_working_pdf,
        ppt_working_ai=ppt_working_ai,
        ppt_assets_dir=ppt_assets_dir,
        ppt_segments_json=ppt_segments_json,
        pptx=pptx_path,
    )


def _load_or_write_regions(segments_path: Path, auto_regions: list[CropRegion]) -> list[CropRegion]:
    if not segments_path.exists():
        return auto_regions

    payload = json.loads(segments_path.read_text())
    return [
        CropRegion(
            start_pt=float(item["start_pt"]),
            end_pt=float(item["end_pt"]),
            score=float(item.get("score", 1.0)),
        )
        for item in payload.get("regions", [])
    ] or auto_regions


def _write_region_manifest(
    segments_path: Path,
    page_height_pt: float,
    regions: list[CropRegion],
    slide_specs: list[SlideSpec],
) -> None:
    payload = {
        "page_height_pt": page_height_pt,
        "instructions": "Edit start_pt and end_pt if you want different slide splits, then rerun the pipeline.",
        "regions": [
            {
                "slide_number": index + 2,
                "start_pt": round(region.start_pt, 2),
                "end_pt": round(region.end_pt, 2),
                "score": round(region.score, 3),
                "title": slide_specs[index].title,
                "subtitle": slide_specs[index].subtitle,
                "image_path": str(slide_specs[index].image_path),
            }
            for index, region in enumerate(regions)
        ],
    }
    segments_path.write_text(json.dumps(payload, indent=2))
