from pathlib import Path

from pro_data_analysis.pdf_extract import PageText, TextBlock, extract_metadata, extract_source_from_blocks, load_page_text


def test_extracts_metadata_from_dhs_pdf() -> None:
    page_text = load_page_text(Path("test_cases/where-the-dhs-shutdown-hit-hardest.pdf"))
    metadata = extract_metadata(page_text)
    assert metadata.title == "Where the DHS shutdown hit hardest"
    assert metadata.last_name == "SONI"
    assert metadata.date_mmddyyyy == "04/02/2026"
    assert metadata.stem == "20260402-where-the-dhs-shutdown-hit-hardest-soni"


def test_extracts_source_from_bottom_note_block() -> None:
    page_text = load_page_text(Path("test_cases/in-iran-us-strikes-another-blow-to-chinas-oil-suppliers.pdf"))
    assert extract_source_from_blocks(page_text.blocks) == "Kpler"


def test_uses_filename_date_when_pdf_text_has_no_date() -> None:
    page_text = _page_text_without_date()
    metadata = extract_metadata(page_text, filename_stem="20260128-dhs-ice-funding-shutdown")
    assert metadata.date_mmddyyyy == "01/28/2026"
    assert metadata.stem == "20260128-ice-funding-fight-could-shut-down-government-thomas"


def test_uses_undated_placeholder_when_pdf_and_filename_have_no_date() -> None:
    page_text = _page_text_without_date()
    metadata = extract_metadata(page_text, filename_stem="dhs-ice-funding-shutdown")
    assert metadata.date_mmddyyyy == "DATE TK"
    assert metadata.stem == "undated-ice-funding-fight-could-shut-down-government-thomas"


def _page_text_without_date() -> PageText:
    blocks = [
        TextBlock(
            x0=50,
            y0=100,
            x1=550,
            y1=140,
            text="Ice funding fight could shut down government",
        ),
        TextBlock(
            x0=50,
            y0=190,
            x1=550,
            y1=210,
            text="BY ELI THOMAS",
        ),
        TextBlock(
            x0=50,
            y0=230,
            x1=550,
            y1=260,
            text="A test dek long enough to be treated as the summary text for this page.",
        ),
    ]
    return PageText(width=612, height=792, blocks=blocks, raw_text=" ".join(block.text for block in blocks))
