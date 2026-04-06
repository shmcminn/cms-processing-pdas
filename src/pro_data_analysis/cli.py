from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import process_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate CMS files from a Pro Data Analysis PDF.")
    parser.add_argument("pdf_path", type=Path, help="Path to the finished PDF.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional directory for generated files. Defaults to the PDF folder.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        outputs = process_pdf(args.pdf_path, output_dir=args.output_dir)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    for path in [
        outputs.canonical_pdf,
        outputs.main_jpg,
        outputs.email_jpg,
        outputs.ppt_working_ai,
        outputs.workflow_state,
    ]:
        print(path)
    if outputs.ppt_working_pdf is not None:
        print(outputs.ppt_working_pdf)
    if outputs.pptx is not None:
        print(outputs.pptx)
