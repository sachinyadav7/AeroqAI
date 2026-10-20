"""
Unit tests for Module 1 — Stage 3: Text Chunker Engine.
"""

import pytest
from AeroqAI.models.document import CleanedDocument, DocumentMetadata
from AeroqAI.models.chunk import TextChunk
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker


def _create_sample_cleaned_doc(doc_id: str, content: str, page: int = 1) -> CleanedDocument:
    meta = DocumentMetadata(
        source_file="test_policy.pdf",
        page_number=page,
        total_pages=5,
        char_count=len(content),
        word_count=len(content.split())
    )
    return CleanedDocument(
        doc_id=doc_id,
        content=content,
        raw_content=content,
        metadata=meta,
        cleaning_stats={"char_reduction": 0}
    )


def test_invalid_chunker_initialization():
    """Verify validation errors on improper chunker configuration."""
    with pytest.raises(ValueError, match="chunk_size must be positive"):
        TextChunker(chunk_size=0)

    with pytest.raises(ValueError, match="chunk_overlap must be non-negative"):
        TextChunker(chunk_size=100, chunk_overlap=-5)

    with pytest.raises(ValueError, match="strictly smaller than chunk_size"):
        TextChunker(chunk_size=100, chunk_overlap=100)

    with pytest.raises(ValueError, match="strictly smaller than chunk_size"):
        TextChunker(chunk_size=100, chunk_overlap=120)

    with pytest.raises(ValueError, match="Unsupported strategy"):
        TextChunker(strategy="unknown_mode")


def test_chunk_empty_or_whitespace_document():
    """Empty or blank documents should produce zero chunks."""
    chunker = TextChunker(chunk_size=200, chunk_overlap=20)
    empty_doc = _create_sample_cleaned_doc("doc_empty", "")
    blank_doc = _create_sample_cleaned_doc("doc_blank", "   \n\n   ")

    assert chunker.chunk_document(empty_doc) == []
    assert chunker.chunk_document(blank_doc) == []


def test_chunk_short_document():
    """Content smaller than chunk_size should produce exactly 1 chunk."""
    chunker = TextChunker(chunk_size=300, chunk_overlap=30)
    short_text = "This is a brief policy statement regarding remote work safety."
    doc = _create_sample_cleaned_doc("doc_short", short_text)

    chunks = chunker.chunk_document(doc)
    assert len(chunks) == 1
    assert isinstance(chunks[0], TextChunk)
    assert chunks[0].content == short_text
    assert chunks[0].chunk_id == "chunk_doc_short_0"
    assert chunks[0].metadata.doc_id == "doc_short"
    assert chunks[0].metadata.chunk_index == 0
    assert chunks[0].metadata.total_chunks == 1
    assert chunks[0].metadata.char_count == len(short_text)
    assert chunks[0].metadata.token_count > 0


def test_recursive_chunking_multi_paragraph():
    """Recursive chunking should split logically across paragraph and sentence boundaries."""
    para1 = "Paragraph 1: Welcome to Global Tech Inc. All employees must follow company guidelines."
    para2 = "Paragraph 2: Remote employees are entitled to high-speed internet reimbursement."
    para3 = "Paragraph 3: Core working hours are 10:00 AM to 4:00 PM EST daily."
    full_text = f"{para1}\n\n{para2}\n\n{para3}"

    chunker = TextChunker(chunk_size=120, chunk_overlap=20, strategy="recursive")
    doc = _create_sample_cleaned_doc("doc_recursive", full_text)

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 2
    assert all(isinstance(c, TextChunk) for c in chunks)
    assert all(len(c.content) <= 150 for c in chunks)  # bounded by size + tolerance

    # Ensure chunk IDs are sequential
    for i, c in enumerate(chunks):
        assert c.chunk_id == f"chunk_doc_recursive_{i}"
        assert c.metadata.chunk_index == i
        assert c.metadata.total_chunks == len(chunks)


def test_fixed_chunking_with_overlap():
    """Fixed chunking should create predictable sliding window chunks."""
    text = "0123456789" * 10  # 100 characters
    chunker = TextChunker(chunk_size=40, chunk_overlap=10, strategy="fixed")
    doc = _create_sample_cleaned_doc("doc_fixed", text)

    chunks = chunker.chunk_document(doc)
    assert len(chunks) >= 3
    assert chunks[0].content.startswith("0123456789")
    assert chunks[0].metadata.chunk_strategy == "fixed"


def test_batch_chunking_multiple_documents():
    """chunk_documents should process multiple documents sequentially."""
    chunker = TextChunker(chunk_size=100, chunk_overlap=10)
    doc1 = _create_sample_cleaned_doc("doc_p1", "Page 1 content about holiday leave.", page=1)
    doc2 = _create_sample_cleaned_doc("doc_p2", "Page 2 content about medical insurance.", page=2)

    chunks = chunker.chunk_documents([doc1, doc2])
    assert len(chunks) == 2
    assert chunks[0].metadata.doc_id == "doc_p1"
    assert chunks[0].metadata.page_number == 1
    assert chunks[1].metadata.doc_id == "doc_p2"
    assert chunks[1].metadata.page_number == 2
