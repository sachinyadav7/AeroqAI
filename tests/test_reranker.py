"""
Unit tests for Module 1 — Stage 6: Cross-Encoder Reranker Engine.
"""

import pytest
from AeroqAI.models.chunk import ChunkMetadata, EmbeddedChunk
from AeroqAI.models.retrieval import SearchResult, RerankedSearchResult, RerankResult
from AeroqAI.modules.module_1_rag.reranker import (
    DeterministicMockReranker,
    CrossEncoderReranker,
    get_reranker
)


def _create_sample_search_result(
    chunk_id: str,
    content: str,
    score: float,
    rank: int,
    page: int = 1
) -> SearchResult:
    meta = ChunkMetadata(
        source_file="hr_policy.pdf",
        doc_id=f"doc_{chunk_id}",
        page_number=page,
        chunk_index=0,
        total_chunks=1,
        char_count=len(content),
        word_count=len(content.split()),
        token_count=max(1, len(content) // 4)
    )
    chunk = EmbeddedChunk(
        chunk_id=chunk_id,
        content=content,
        embedding=[0.1] * 64,
        embedding_model="mock",
        embedding_dimension=64,
        metadata=meta
    )
    return SearchResult(chunk=chunk, similarity_score=score, rank=rank)


def test_deterministic_mock_reranker_scoring():
    """Verify mock reranker recalculates scores and preserves rank metadata."""
    reranker = DeterministicMockReranker(model_name="test-reranker")
    assert reranker.model_name == "test-reranker"

    query = "annual paid vacation leave allowance"

    # Candidate A: High initial vector score, but general discussion
    res_a = _create_sample_search_result(
        chunk_id="c_general",
        content="Welcome to Global Tech Inc. All employees must review the general employment manual.",
        score=0.85,
        rank=1
    )

    # Candidate B: Lower initial vector score, but exact target keywords
    res_b = _create_sample_search_result(
        chunk_id="c_specific",
        content="Standard full-time employees receive 20 days of paid annual vacation leave allowance per year.",
        score=0.65,
        rank=2
    )

    rerank_out = reranker.rerank(query=query, search_results=[res_a, res_b])

    assert isinstance(rerank_out, RerankResult)
    assert len(rerank_out.results) == 2

    # Specific passage with exact target keywords should be promoted to Rank 1
    top_res = rerank_out.results[0]
    assert top_res.chunk.chunk_id == "c_specific"
    assert top_res.new_rank == 1
    assert top_res.original_rank == 2
    assert top_res.original_score == 0.65
    assert top_res.rerank_score > top_res.original_score

    # Check context text helper
    context = rerank_out.get_context_text()
    assert "20 days of paid annual vacation leave" in context


def test_rerank_empty_results():
    """Empty candidate list should return empty RerankResult safely."""
    reranker = DeterministicMockReranker()
    out = reranker.rerank(query="any query", search_results=[])
    assert out.results == []
    assert out.total_reranked == 0
    assert out.rerank_latency_ms == 0.0


def test_rerank_top_k_truncation():
    """Reranker should respect top_k parameter."""
    reranker = DeterministicMockReranker()
    candidates = [
        _create_sample_search_result(f"c{i}", f"Policy text paragraph {i}", 0.5 + (i * 0.05), i)
        for i in range(1, 6)
    ]

    out = reranker.rerank(query="Policy text", search_results=candidates, top_k=2)
    assert len(out.results) == 2
    assert out.results[0].new_rank == 1
    assert out.results[1].new_rank == 2


def test_factory_generator():
    """Verify get_reranker resolves providers correctly."""
    mock_reranker = get_reranker("mock")
    assert isinstance(mock_reranker, DeterministicMockReranker)

    with pytest.raises(ValueError, match="Unknown reranker provider"):
        get_reranker("unsupported_provider")


def test_cross_encoder_reranker():
    """Verify CrossEncoder model if available locally or skipped if network unavailable."""
    try:
        reranker = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    except Exception as e:
        pytest.skip(f"CrossEncoder model download skipped or offline: {e}")

    assert reranker.model_name == "cross-encoder/ms-marco-MiniLM-L-6-v2"

    query = "What is the annual leave policy?"
    c1 = _create_sample_search_result("c1", "Employees receive 20 days annual leave.", 0.60, 1)
    c2 = _create_sample_search_result("c2", "Returning monitors and laptop chargers.", 0.70, 2)

    res = reranker.rerank(query=query, search_results=[c1, c2])
    assert len(res.results) == 2
    assert all(isinstance(r, RerankedSearchResult) for r in res.results)

    # c1 is semantically an exact answer, cross-encoder should rank c1 ahead of c2
    assert res.results[0].chunk.chunk_id == "c1"
