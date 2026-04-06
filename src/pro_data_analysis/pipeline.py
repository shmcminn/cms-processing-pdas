from __future__ import annotations

import json
import shutil
from datetime import datetime, UTC
from pathlib import Path

from .adobe import export_ai_to_pdf_and_pptx, prepare_ppt_ai
from .images import render_pdf_page, save_email_jpeg, save_main_jpeg
from .models import OutputPaths
from .pdf_extract import extract_metadata, extract_note_and_source_from_blocks, load_page_text


def process_pdf(pdf_path: Path, output_dir: Path | None = None) -> OutputPaths:
    pdf_path = pdf_path.resolve()
    if output_dir is None:
        output_dir = pdf_path.parent
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    page_text = load_page_text(pdf_path)
    metadata = extract_metadata(page_text)
    metadata.note, metadata.source = extract_note_and_source_from_blocks(page_text.blocks)

    canonical_pdf = output_dir / f"{metadata.stem}.pdf"
    main_jpg = output_dir / f"{metadata.stem}.jpg"
    email_jpg = output_dir / f"EMAIL-{metadata.stem}.jpg"
    ppt_working_ai = output_dir / f"PPT-{metadata.stem}.ai"
    workflow_state = output_dir / f"PPT-{metadata.stem}.workflow.json"
    ppt_working_pdf = output_dir / f"PPT-{metadata.stem}.pdf"
    pptx_path = output_dir / f"{metadata.stem}.pptx"

    shutil.copy2(pdf_path, canonical_pdf)

    main_image = render_pdf_page(pdf_path, target_width=2300)
    save_main_jpeg(main_image, main_jpg)
    save_email_jpeg(main_image, email_jpg)

    if not ppt_working_ai.exists():
        try:
            prepare_ppt_ai(metadata, pdf_path, ppt_working_ai)
        except Exception as exc:
            _write_workflow_state(
                workflow_state,
                phase="failed_initial_build",
                metadata=metadata,
                source_pdf=pdf_path,
                output_ai=ppt_working_ai,
                error=str(exc),
            )
            raise
        _write_workflow_state(
            workflow_state,
            phase="awaiting_manual_layout",
            metadata=metadata,
            source_pdf=pdf_path,
            output_ai=ppt_working_ai,
        )
        return OutputPaths(
            canonical_pdf=canonical_pdf,
            main_jpg=main_jpg,
            email_jpg=email_jpg,
            ppt_working_ai=ppt_working_ai,
            workflow_state=workflow_state,
        )

    _ensure_manual_layout_is_saved(ppt_working_ai, workflow_state)
    try:
        export_ai_to_pdf_and_pptx(ppt_working_ai, ppt_working_pdf, pptx_path)
    except Exception as exc:
        _write_workflow_state(
            workflow_state,
            phase="failed_export",
            metadata=metadata,
            source_pdf=pdf_path,
            output_ai=ppt_working_ai,
            output_pdf=ppt_working_pdf if ppt_working_pdf.exists() else None,
            output_pptx=pptx_path if pptx_path.exists() else None,
            error=str(exc),
        )
        raise
    _write_workflow_state(
        workflow_state,
        phase="exported",
        metadata=metadata,
        source_pdf=pdf_path,
        output_ai=ppt_working_ai,
        output_pdf=ppt_working_pdf,
        output_pptx=pptx_path,
    )
    return OutputPaths(
        canonical_pdf=canonical_pdf,
        main_jpg=main_jpg,
        email_jpg=email_jpg,
        ppt_working_ai=ppt_working_ai,
        workflow_state=workflow_state,
        ppt_working_pdf=ppt_working_pdf,
        pptx=pptx_path,
    )


def _ensure_manual_layout_is_saved(ppt_working_ai: Path, workflow_state: Path) -> None:
    if not workflow_state.exists():
        return
    try:
        state = json.loads(workflow_state.read_text())
    except json.JSONDecodeError:
        return

    recorded_mtime = state.get("ppt_working_ai_mtime")
    if recorded_mtime is None:
        return

    current_mtime = ppt_working_ai.stat().st_mtime
    if current_mtime <= float(recorded_mtime) + 1e-6:
        raise RuntimeError(
            "The working PPT Illustrator file has not changed since it was created. "
            "Open the PPT AI file, move content onto the slide artboards, save it, then rerun the same command."
        )


def _write_workflow_state(
    workflow_state: Path,
    phase: str,
    metadata,
    source_pdf: Path,
    output_ai: Path,
    output_pdf: Path | None = None,
    output_pptx: Path | None = None,
    error: str | None = None,
) -> None:
    payload = {
        "phase": phase,
        "updated_at": datetime.now(UTC).isoformat(),
        "source_pdf": str(source_pdf.resolve()),
        "ppt_working_ai": str(output_ai.resolve()),
        "ppt_working_ai_mtime": output_ai.stat().st_mtime if output_ai.exists() else None,
        "canonical_stem": metadata.stem,
        "manual_step": "Open the PPT AI file, move chart/content from the off-artboard source group onto the slide artboards, save the AI file, then rerun the same command on the original PDF."
        if phase == "awaiting_manual_layout"
        else None,
        "ppt_working_pdf": str(output_pdf.resolve()) if output_pdf else None,
        "pptx": str(output_pptx.resolve()) if output_pptx else None,
        "error": error,
    }
    workflow_state.write_text(json.dumps(payload, indent=2))
