from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import fitz

from .models import Metadata


@dataclass(slots=True)
class TextBlock:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


@dataclass(slots=True)
class PageText:
    width: float
    height: float
    blocks: list[TextBlock]
    raw_text: str


BYLINE_RE = re.compile(
    r"\bBY\s+(?P<authors>.+?)(?:\s*\|\s*(?P<date>\d{2}/\d{2}/\d{4}))?(?:\b|$)",
    re.IGNORECASE,
)


def load_page_text(pdf_path: Path) -> PageText:
    doc = fitz.open(pdf_path)
    page = doc[0]
    blocks: list[TextBlock] = []
    for raw_block in sorted(page.get_text("blocks"), key=lambda item: (item[1], item[0])):
        x0, y0, x1, y1, text, *_ = raw_block
        clean = " ".join(text.split())
        if clean:
            blocks.append(TextBlock(x0=x0, y0=y0, x1=x1, y1=y1, text=clean))
    return PageText(
        width=page.rect.width,
        height=page.rect.height,
        blocks=blocks,
        raw_text=" ".join(page.get_text("text").split()),
    )


def extract_metadata(page_text: PageText) -> Metadata:
    title_block = _pick_title_block(page_text.blocks)
    byline_block = _pick_byline_block(page_text.blocks)
    date_mmddyyyy = _extract_date(byline_block.text if byline_block else page_text.raw_text)
    byline = _extract_byline(byline_block.text if byline_block else page_text.raw_text)
    last_name = _pick_last_name(byline)
    dek = _extract_dek(page_text.blocks, byline_block)
    title = title_block.text if title_block else "Untitled data analysis"
    source = _extract_source(page_text.raw_text, title)
    slug = slugify(title)
    stem = f"{yyyymmdd(date_mmddyyyy)}-{slug}-{slugify(last_name)}"
    return Metadata(
        title=title,
        byline=byline,
        date_mmddyyyy=date_mmddyyyy,
        dek=dek,
        source=source,
        slug=slug,
        last_name=last_name,
        stem=stem,
    )


def content_start_pt(page_text: PageText) -> float:
    top_blocks = [
        block
        for block in page_text.blocks
        if block.y0 < 305
        and len(block.text) > 20
        and not block.text.upper().startswith("SOURCE:")
        and block.x0 < 90
        and (block.x1 - block.x0) > page_text.width * 0.7
    ]
    if not top_blocks:
        return 280.0
    return min(page_text.height - 100, max(block.y1 for block in top_blocks) + 20)


def _pick_title_block(blocks: list[TextBlock]) -> TextBlock | None:
    candidates = [
        block
        for block in blocks
        if block.y0 < 190
        and len(block.text) > 25
        and "DATA ANALYSIS" not in block.text.upper()
        and not block.text.upper().startswith("SOURCE:")
        and not block.text.upper().startswith("NOTE:")
        and " BY " not in f" {block.text.upper()} "
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda block: (block.y0, -len(block.text)))


def _pick_byline_block(blocks: list[TextBlock]) -> TextBlock | None:
    for block in blocks:
        if block.y0 > 260:
            break
        if " BY " in f" {block.text.upper()} " or block.text.upper().startswith("BY "):
            return block
    return None


def _extract_date(text: str) -> str:
    match = re.search(r"\b(\d{2}/\d{2}/\d{4})\b", text)
    if match:
        return match.group(1)
    raise ValueError("Could not find publication date in PDF text.")


def _extract_byline(text: str) -> str:
    if "|" in text.upper() and "BY " in text.upper():
        before_pipe = text.split("|", 1)[0]
        return before_pipe.split("BY", 1)[1].strip()
    match = BYLINE_RE.search(text)
    if not match:
        raise ValueError("Could not find byline in PDF text.")
    authors = re.sub(r"\s+", " ", match.group("authors")).strip(" |")
    return authors


def _pick_last_name(byline: str) -> str:
    first_author = re.split(r",| AND ", byline, maxsplit=1)[0].strip()
    if not first_author:
        return "staff"
    return first_author.split()[-1]


def _extract_dek(blocks: list[TextBlock], byline_block: TextBlock | None) -> str:
    if byline_block is None:
        return ""
    candidates: list[str] = []
    for block in blocks:
        if block.y0 <= byline_block.y1 + 4:
            continue
        if block.y0 > 320:
            break
        if len(block.text) < 40:
            continue
        if block.text.upper().startswith("SOURCE:") or block.text.upper().startswith("NOTE:"):
            continue
        candidates.append(block.text)
    if not candidates:
        return ""
    dek = candidates[0]
    if len(dek) < 180 and len(candidates) > 1:
        dek = f"{dek} {candidates[1]}"
    return re.sub(r"\s+", " ", dek).strip()


def _extract_source(text: str, title: str) -> str:
    source_match = re.search(r"Source:\s*(.+)", text, re.IGNORECASE)
    if source_match:
        source_tail = source_match.group(1)
        delimiters = [r"Note:", r"\bBY\s", re.escape(title)]
        cut_positions = [
            match.start()
            for delimiter in delimiters
            if (match := re.search(delimiter, source_tail, re.IGNORECASE))
        ]
        if cut_positions:
            source_tail = source_tail[: min(cut_positions)]
        return re.sub(r"\s+", " ", source_tail).strip(" .")
    return ""


def slugify(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[’']", "", lowered)
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    return lowered.strip("-")


def yyyymmdd(date_mmddyyyy: str) -> str:
    month, day, year = date_mmddyyyy.split("/")
    return f"{year}{month}{day}"
