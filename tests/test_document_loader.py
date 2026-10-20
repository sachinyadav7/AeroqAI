"""
Unit tests for Module 1 — Stage 1: PDF Document Loader.
"""

import pytest
from pathlib import Path
from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader, DocumentLoaderError
from AeroqAI.models.document import RawDocument


@pytest.fixture
def sample_pdf_path() -> Path:
    return Path("AeroqAI/data/sample_docs/hr_policy.pdf")


def test_load_valid_pdf(sample_pdf_path: Path):
    """Test loading a valid multi-page PDF document."""
    loader = PDFDocumentLoader()
    docs = loader.load_file(sample_pdf_path)

    assert len(docs) == 10
    assert all(isinstance(d, RawDocument) for d in docs)

    # Verify first page properties
    first_page = docs[0]
    assert first_page.doc_id == "doc_hr_policy_p1"
    assert first_page.metadata.source_file == "hr_policy.pdf"
    assert first_page.metadata.page_number == 1
    assert first_page.metadata.total_pages == 10
    assert first_page.metadata.char_count > 0
    assert first_page.metadata.word_count > 0
    assert "Global Tech Inc." in first_page.content


def test_load_nonexistent_file():
    """Test loader error when file path does not exist."""
    loader = PDFDocumentLoader()
    with pytest.raises(DocumentLoaderError) as exc_info:
        loader.load_file("AeroqAI/data/sample_docs/non_existent.pdf")
    assert "File not found" in str(exc_info.value)


def test_load_invalid_file_extension(tmp_path: Path):
    """Test loader error when loading a non-PDF file."""
    txt_file = tmp_path / "sample.txt"
    txt_file.write_text("Hello World", encoding="utf-8")
    
    loader = PDFDocumentLoader()
    with pytest.raises(DocumentLoaderError) as exc_info:
        loader.load_file(txt_file)
    assert "Unsupported file extension" in str(exc_info.value)


def test_load_empty_pdf_file(tmp_path: Path):
    """Test loader error on a 0-byte PDF file."""
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")

    loader = PDFDocumentLoader()
    with pytest.raises(DocumentLoaderError) as exc_info:
        loader.load_file(empty_pdf)
    assert "File is empty" in str(exc_info.value)


def test_load_directory(sample_pdf_path: Path):
    """Test scanning directory for PDFs."""
    loader = PDFDocumentLoader()
    docs = loader.load_directory(sample_pdf_path.parent)

    assert len(docs) >= 10
    sources = set(d.metadata.source_file for d in docs)
    assert "hr_policy.pdf" in sources
