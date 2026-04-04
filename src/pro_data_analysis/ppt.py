from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image
from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .models import Metadata, SlideSpec

REPO_ROOT = Path(__file__).resolve().parents[2]


def build_pptx(
    metadata: Metadata,
    slide_specs: list[SlideSpec],
    output_path: Path,
    workspace_dir: Path,
) -> None:
    payload = {
        "title": metadata.title,
        "byline": metadata.byline.upper(),
        "date": metadata.date_mmddyyyy,
        "dek": metadata.dek,
        "source": metadata.source,
        "slide_specs": [
            {
                "image_path": str(slide.image_path),
                "title": slide.title,
                "subtitle": slide.subtitle,
            }
            for slide in slide_specs
        ],
        "output_path": str(output_path),
    }
    payload_path = workspace_dir / "ppt_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2))
    node_binary = shutil.which("node")
    if node_binary is None:
        raise RuntimeError("Node is required to build the PowerPoint deck.")
    subprocess.run(
        [node_binary, str(REPO_ROOT / "tools" / "build_pptx.mjs"), str(payload_path)],
        cwd=REPO_ROOT,
        check=True,
    )
    if payload_path.exists():
        payload_path.unlink()


def export_working_files(metadata: Metadata, slide_specs: list[SlideSpec], ppt_pdf_path: Path, ai_copy_path: Path) -> None:
    build_working_pdf(metadata, slide_specs, ppt_pdf_path)
    shutil.copy2(ppt_pdf_path, ai_copy_path)


def build_working_pdf(metadata: Metadata, slide_specs: list[SlideSpec], output_path: Path) -> None:
    pdf = canvas.Canvas(str(output_path), pagesize=landscape(letter))
    pdf.setTitle(metadata.title)

    _draw_title_slide(pdf, metadata)
    for slide_spec in slide_specs:
        pdf.showPage()
        _draw_content_slide(pdf, slide_spec)

    pdf.save()


def _draw_title_slide(pdf: canvas.Canvas, metadata: Metadata) -> None:
    _draw_chrome(pdf)

    title_lines = _wrap_text(metadata.title, "Helvetica-Bold", 29, 8.55 * 72)
    _draw_lines(pdf, title_lines, 0.98 * 72, 6.58 * 72, "Helvetica-Bold", 29, 34, Color(0.07, 0.07, 0.07))

    pdf.setFont("Helvetica-Bold", 11.5)
    pdf.setFillColor(Color(0.29, 0.29, 0.29))
    pdf.drawString(0.98 * 72, 4.96 * 72, f"{metadata.byline.upper()} | {metadata.date_mmddyyyy}")

    dek_lines = _wrap_text(metadata.dek, "Helvetica", 18, 8.65 * 72)
    _draw_lines(pdf, dek_lines, 0.98 * 72, 4.6 * 72, "Helvetica", 18, 23, Color(0.13, 0.13, 0.13))

    if metadata.source:
        source_lines = _wrap_text(f"Source: {metadata.source}", "Helvetica", 10, 8.5 * 72)
        _draw_lines(pdf, source_lines, 0.98 * 72, 1.0 * 72, "Helvetica", 10, 13, Color(0.2, 0.2, 0.2))


def _draw_content_slide(pdf: canvas.Canvas, slide_spec: SlideSpec) -> None:
    _draw_chrome(pdf)

    image_top_in = 1.24
    if slide_spec.title:
        title_lines = _wrap_text(slide_spec.title, "Helvetica-Bold", 17, 8.75 * 72)
        _draw_lines(pdf, title_lines, 1.0 * 72, 6.96 * 72, "Helvetica-Bold", 17, 20, Color(0.07, 0.07, 0.07))
        image_top_in = 1.92

    if slide_spec.subtitle:
        subtitle_lines = _wrap_text(slide_spec.subtitle, "Helvetica", 10.5, 8.75 * 72)
        _draw_lines(pdf, subtitle_lines, 1.0 * 72, 6.56 * 72, "Helvetica", 10.5, 13, Color(0.27, 0.27, 0.27))
        image_top_in = 2.08

    with Image.open(slide_spec.image_path) as image:
        width_px, height_px = image.size
    width_pt = 9.0 * 72
    height_pt = min((7.12 - image_top_in) * 72, width_pt * height_px / width_px)
    pdf.drawImage(str(slide_spec.image_path), 1.0 * 72, 8.5 * 72 - (image_top_in * 72) - height_pt, width=width_pt, height=height_pt, preserveAspectRatio=True, mask="auto")


def _draw_chrome(pdf: canvas.Canvas) -> None:
    red = Color(0.76, 0.13, 0.15)
    dark = Color(0.07, 0.07, 0.07)
    light = Color(0.85, 0.85, 0.85)
    footer = Color(0.73, 0.76, 0.81)

    pdf.setStrokeColor(light)
    pdf.setLineWidth(1)
    pdf.line(0.98 * 72, 7.22 * 72, 9.96 * 72, 7.22 * 72)
    pdf.line(0.98 * 72, 1.22 * 72, 9.96 * 72, 1.22 * 72)

    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(red)
    pdf.drawCentredString(5.02 * 72, 8.02 * 72, "POLITICO")
    pdf.setFillColor(dark)
    pdf.drawString(5.56 * 72, 8.02 * 72, "PRO")
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(5.25 * 72, 7.63 * 72, "Analysis")

    pdf.setFont("Helvetica", 9.5)
    pdf.setFillColor(footer)
    pdf.drawString(1.0 * 72, 0.96 * 72, "Data Analysis")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.setFillColor(red)
    pdf.drawString(8.42 * 72, 0.94 * 72, "POLITICO")
    pdf.setFillColor(dark)
    pdf.drawString(9.26 * 72, 0.94 * 72, "PRO")


def _draw_lines(
    pdf: canvas.Canvas,
    lines: list[str],
    x: float,
    top_y: float,
    font_name: str,
    font_size: float,
    line_height: float,
    color: Color,
) -> None:
    pdf.setFont(font_name, font_size)
    pdf.setFillColor(color)
    for index, line in enumerate(lines):
        pdf.drawString(x, top_y - (index * line_height), line)


def _wrap_text(text: str, font_name: str, font_size: float, max_width: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines = [words[0]]
    for word in words[1:]:
        candidate = f"{lines[-1]} {word}"
        if stringWidth(candidate, font_name, font_size) <= max_width:
            lines[-1] = candidate
        else:
            lines.append(word)
    return lines
