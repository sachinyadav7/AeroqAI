"""
Unit tests for Module 1 — Stage 5: Vector Store & Retrieval Engine.
"""

import pytest
from AeroqAI.models.chunk import ChunkMetadata, EmbeddedChunk
from AeroqAI.models.retrieval import SearchResult, RetrievalResult
from AeroqAI.modules.module_1_rag.vector_store import (
    InMemoryVectorStore,
    VectorStoreError,
    get_vector_store
)
from AeroqAI.modules.module_1_rag.embedding_generator import DeterministicMockEmbedder


def _create_sample_embedded_chunk(
    chunk_id: str,
    content: str,
    embedding: list[float],
    page: int = 1
) -> EmbeddedChunk:
    meta = ChunkMetadata(
        source_file="hr_policy.pdf",
        doc_id=f"doc_{chunk_id}",
        page_number=page,
        chunk_index=0,
        total_chunks=1,
        char_count=len(content),
        word_count=len(content.split()),
        token_count=max(1, len(content) // 4),
        extra={"department": "HR"}
    )
    return EmbeddedChunk(
        chunk_id=chunk_id,
        content=content,
        embedding=embedding,
        embedding_model="mock-deterministic",
        embedding_dimension=len(embedding),
        metadata=meta
    )


def test_add_and_count_chunks():
    """Verify adding chunks and counting indexed elements."""
    store = InMemoryVectorStore()
    assert store.count() == 0

    embedder = DeterministicMockEmbedder(dimension=64)
    vec1 = embedder.embed_text("Annual paid time off policies")
    vec2 = embedder.embed_text("Health and dental benefits")

    chunk1 = _create_sample_embedded_chunk("c1", "PTO rules", vec1, page=1)
    chunk2 = _create_sample_embedded_chunk("c2", "Health benefits", vec2, page=2)

    store.add_chunks([chunk1, chunk2])
    assert store.count() == 2

    # Verify get_by_id
    retrieved = store.get_by_id("c1")
    assert retrieved is not None
    assert retrieved.chunk_id == "c1"
    assert retrieved.content == "PTO rules"

    assert store.get_by_id("non_existent") is None


def test_dimension_mismatch_validation():
    """Verify error when adding chunk with conflicting vector dimensions."""
    store = InMemoryVectorStore()
    c1 = _create_sample_embedded_chunk("c1", "Content", [1.0, 0.0, 0.0])
    c2 = _create_sample_embedded_chunk("c2", "Content", [1.0, 0.0])  # dim 2 vs 3

    store.add_chunks([c1])
    with pytest.raises(VectorStoreError, match="Dimension mismatch"):
        store.add_chunks([c2])


def test_top_k_vector_search():
    """Verify Top-K vector retrieval ranks results correctly."""
    store = InMemoryVectorStore()
    embedder = DeterministicMockEmbedder(dimension=64)

    c1 = _create_sample_embedded_chunk("c1", "Leave and vacation rules", embedder.embed_text("Leave rules"), page=1)
    c2 = _create_sample_embedded_chunk("c2", "Remote laptop return policy", embedder.embed_text("Laptop return"), page=2)
    c3 = _create_sample_embedded_chunk("c3", "Holiday calendar dates", embedder.embed_text("Holiday calendar"), page=3)

    store.add_chunks([c1, c2, c3])

    query_vec = embedder.embed_text("Leave policy and vacation days")
    results = store.search_vector(query_vec, top_k=2)

    assert len(results) == 2
    assert all(isinstance(r, SearchResult) for r in results)
    assert results[0].rank == 1
    assert results[1].rank == 2
    assert results[0].similarity_score >= results[1].similarity_score


def test_score_threshold_filtering():
    """Verify results below score_threshold are filtered out."""
    store = InMemoryVectorStore()
    embedder = DeterministicMockEmbedder(dimension=64)

    c1 = _create_sample_embedded_chunk("c1", "Target Topic", embedder.embed_text("Target Topic"))
    c2 = _create_sample_embedded_chunk("c2", "Completely Unrelated Subject", embedder.embed_text("Completely Unrelated Subject"))
    store.add_chunks([c1, c2])

    query_vec = embedder.embed_text("Target Topic")
    # Exact match should have similarity ~1.0; unrelated will be much lower
    results = store.search_vector(query_vec, top_k=5, score_threshold=0.8)

    assert len(results) == 1
    assert results[0].chunk.chunk_id == "c1"


def test_metadata_filtering():
    """Verify filtering by page_number and custom metadata."""
    store = InMemoryVectorStore()
    embedder = DeterministicMockEmbedder(dimension=64)

    c1 = _create_sample_embedded_chunk("c1", "PTO Rules Page 1", embedder.embed_text("PTO"), page=1)
    c2 = _create_sample_embedded_chunk("c2", "PTO Rules Page 2", embedder.embed_text("PTO"), page=2)
    store.add_chunks([c1, c2])

    query_vec = embedder.embed_text("PTO")
    
    # Filter by page 2
    results_p2 = store.search_vector(query_vec, top_k=5, metadata_filter={"page_number": 2})
    assert len(results_p2) == 1
    assert results_p2[0].chunk.chunk_id == "c2"

    # Filter by department
    results_dept = store.search_vector(query_vec, top_k=5, metadata_filter={"department": "HR"})
    assert len(results_dept) == 2


def test_search_text_end_to_end():
    """Verify search_text helper returns structured RetrievalResult with latency."""
    store = InMemoryVectorStore()
    embedder = DeterministicMockEmbedder(dimension=64)

    c1 = _create_sample_embedded_chunk("c1", "Travel expense reimbursement.", embedder.embed_text("Travel expense"))
    store.add_chunks([c1])

    retrieval = store.search_text("reimbursement for business travel", embedder=embedder, top_k=1)

    assert isinstance(retrieval, RetrievalResult)
    assert retrieval.query == "reimbursement for business travel"
    assert retrieval.top_k == 1
    assert retrieval.total_retrieved == 1
    assert retrieval.retrieval_latency_ms >= 0.0
    assert "Travel expense" in retrieval.get_context_text()


def test_delete_and_clear():
    """Verify deleting individual chunks and clearing the store."""
    store = InMemoryVectorStore()
    c1 = _create_sample_embedded_chunk("c1", "Test", [1.0, 0.0])
    c2 = _create_sample_embedded_chunk("c2", "Test", [0.0, 1.0])
    store.add_chunks([c1, c2])

    assert store.delete_by_id("c1") is True
    assert store.count() == 1
    assert store.get_by_id("c1") is None

    store.clear()
    assert store.count() == 0
    assert store.search_vector([1.0, 0.0]) == []


def test_factory_generator():
    """Verify get_vector_store resolves correctly."""
    store = get_vector_store("in_memory")
    assert isinstance(store, InMemoryVectorStore)

    with pytest.raises(ValueError, match="Unknown vector store type"):
        get_vector_store("unsupported_store")
