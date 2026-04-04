from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .images import find_slide_regions, render_pdf_page, save_crop, save_email_jpeg, save_main_jpeg
from .models import OutputPaths, SlideSpec
from .pdf_extract import content_start_pt, extract_metadata, extract_overlay_text, extract_source_from_blocks, load_page_text
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
    pptx_path = output_dir / f"{metadata.stem}.pptx"

    shutil.copy2(pdf_path, canonical_pdf)

    main_image = render_pdf_page(pdf_path, target_width=2300)
    save_main_jpeg(main_image, main_jpg)
    save_email_jpeg(main_image, email_jpg)

    analysis_image = render_pdf_page(pdf_path, target_width=1800)
    content_start = content_start_pt(page_text)
    regions = find_slide_regions(page_text, analysis_image, content_start)

    with tempfile.TemporaryDirectory(prefix="pro-data-analysis-") as temp_dir:
        temp_path = Path(temp_dir)
        slide_specs: list[SlideSpec] = []
        for index, region in enumerate(regions, start=2):
            overlay_title, overlay_subtitle, crop_start = extract_overlay_text(page_text.blocks, region)
            crop_path = temp_path / f"slide-{index}.png"
            adjusted_region = region
            if crop_start > region.start_pt and crop_start < region.end_pt - 80:
                adjusted_region = type(region)(start_pt=crop_start, end_pt=region.end_pt, score=region.score)
            save_crop(main_image, page_text.height, adjusted_region, crop_path)
            slide_specs.append(SlideSpec(image_path=crop_path, title=overlay_title, subtitle=overlay_subtitle))
        build_pptx(metadata, slide_specs, pptx_path, temp_path)
        export_working_files(metadata, slide_specs, ppt_working_pdf, ppt_working_ai)

    return OutputPaths(
        canonical_pdf=canonical_pdf,
        main_jpg=main_jpg,
        email_jpg=email_jpg,
        ppt_working_pdf=ppt_working_pdf,
        ppt_working_ai=ppt_working_ai,
        pptx=pptx_path,
    )
