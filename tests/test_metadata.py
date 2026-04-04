from pathlib import Path

from pro_data_analysis.pdf_extract import extract_metadata, load_page_text


def test_extracts_metadata_from_dhs_pdf() -> None:
    page_text = load_page_text(Path("test_cases/where-the-dhs-shutdown-hit-hardest.pdf"))
    metadata = extract_metadata(page_text)
    assert metadata.title == "Where the DHS shutdown hit hardest"
    assert metadata.last_name == "SONI"
    assert metadata.date_mmddyyyy == "04/02/2026"
    assert metadata.stem == "20260402-where-the-dhs-shutdown-hit-hardest-soni"
