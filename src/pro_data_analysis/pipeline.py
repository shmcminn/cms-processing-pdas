from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .images import find_slide_regions, render_pdf_page, save_crop, save_email_jpeg, save_main_jpeg
from .models import OutputPaths
from .pdf_extract import content_start_pt, extract_metadata, load_page_text
from .ppt import build_pptx


def process_pdf(pdf_path: Path, output_dir: Path | None = None) -> OutputPaths:
    pdf_path = pdf_path.resolve()
    if output_dir is None:
        output_dir = pdf_path.parent
    output_dir = output_dir.resolve()
    page_text = load_page_text(pdf_path)
    metadata = extract_metadata(page_text)

    canonical_pdf = output_dir / f"{metadata.stem}.pdf"
    main_jpg = output_dir / f"{metadata.stem}.jpg"
    email_jpg = output_dir / f"EMAIL-{metadata.stem}.jpg"
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
        slide_images: list[Path] = []
        for index, region in enumerate(regions, start=2):
            crop_path = temp_path / f"slide-{index}.png"
            save_crop(main_image, page_text.height, region, crop_path)
            slide_images.append(crop_path)
        build_pptx(metadata, slide_images, pptx_path, temp_path)

    return OutputPaths(
        canonical_pdf=canonical_pdf,
        main_jpg=main_jpg,
        email_jpg=email_jpg,
        pptx=pptx_path,
    )
