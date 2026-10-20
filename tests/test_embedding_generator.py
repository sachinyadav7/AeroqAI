"""
Unit tests for Module 1 — Stage 4: Embedding Generator.
"""

import math
import pytest
import numpy as np

from AeroqAI.models.chunk import TextChunk, ChunkMetadata, EmbeddedChunk
from AeroqAI.modules.module_1_rag.embedding_generator import (
    BaseEmbeddingGenerator,
    DeterministicMockEmbedder,
    SentenceTransformerEmbedder,
    get_embedding_generator
)


def _create_sample_chunk(chunk_id: str, content: str) -> TextChunk:
    meta = ChunkMetadata(
        source_file="test.pdf",
        doc_id="doc_1",
        page_number=1,
        chunk_index=0,
        total_chunks=1,
        char_count=len(content),
        word_count=len(content.split()),
        token_count=max(1, len(content) // 4)
    )
    return TextChunk(chunk_id=chunk_id, content=content, metadata=meta)


def test_deterministic_mock_embedder_properties():
    """Verify mock embedder dimensions, normalization, and determinism."""
    dim = 256
    embedder = DeterministicMockEmbedder(dimension=dim, model_name="mock-256")
    assert embedder.dimension == dim
    assert embedder.model_name == "mock-256"

    text = "Employees are entitled to 20 days paid annual leave."
    vec1 = embedder.embed_text(text)
    vec2 = embedder.embed_text(text)

    # Dimensionality check
    assert len(vec1) == dim
    # Determinism check
    assert vec1 == vec2

    # L2 unit-norm check (vector magnitude ~= 1.0)
    norm = np.linalg.norm(np.array(vec1, dtype=np.float32))
    assert math.isclose(norm, 1.0, rel_tol=1e-5)


def test_deterministic_mock_empty_text():
    """Empty or blank text should yield a zero-filled vector without errors."""
    embedder = DeterministicMockEmbedder(dimension=64)
    zero_vec = embedder.embed_text("")
    assert len(zero_vec) == 64
    assert all(v == 0.0 for v in zero_vec)


def test_embed_chunks_transformation():
    """Verify embed_chunks cleanly maps TextChunk to EmbeddedChunk data contracts."""
    embedder = DeterministicMockEmbedder(dimension=128, model_name="test-model")
    chunk1 = _create_sample_chunk("chunk_1", "Health and dental coverage benefits.")
    chunk2 = _create_sample_chunk("chunk_2", "Flexible remote work hours policy.")

    embedded_chunks = embedder.embed_chunks([chunk1, chunk2])

    assert len(embedded_chunks) == 2
    assert all(isinstance(c, EmbeddedChunk) for c in embedded_chunks)

    # Check contracts on first embedded chunk
    c1 = embedded_chunks[0]
    assert c1.chunk_id == "chunk_1"
    assert c1.content == "Health and dental coverage benefits."
    assert c1.embedding_model == "test-model"
    assert c1.embedding_dimension == 128
    assert len(c1.embedding) == 128
    assert c1.metadata.source_file == "test.pdf"


def test_cosine_similarity_computation():
    """Verify cosine similarity function behaves correctly mathematically."""
    embedder = DeterministicMockEmbedder(dimension=128)

    # Exact same vector
    vec_a = embedder.embed_text("Annual leave policy rules")
    assert math.isclose(BaseEmbeddingGenerator.cosine_similarity(vec_a, vec_a), 1.0, rel_tol=1e-5)

    # Zero vector
    zero_vec = [0.0] * 128
    assert BaseEmbeddingGenerator.cosine_similarity(vec_a, zero_vec) == 0.0


def test_factory_generator():
    """Verify get_embedding_generator resolves providers correctly."""
    mock_gen = get_embedding_generator(provider="mock", dimension=64)
    assert isinstance(mock_gen, DeterministicMockEmbedder)
    assert mock_gen.dimension == 64

    with pytest.raises(ValueError, match="Unknown embedding provider"):
        get_embedding_generator(provider="nonexistent_provider")


def test_sentence_transformer_embedder():
    """Verify local SentenceTransformer embedder if available in the environment."""
    try:
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    except Exception as e:
        pytest.skip(f"SentenceTransformer model download skipped or offline: {e}")

    assert embedder.dimension == 384
    assert embedder.model_name == "all-MiniLM-L6-v2"

    text = "Global Tech Inc. hybrid workplace guidelines."
    vec = embedder.embed_text(text)
    assert len(vec) == 384

    # Verify L2 normalization
    norm = np.linalg.norm(np.array(vec, dtype=np.float32))
    assert math.isclose(norm, 1.0, rel_tol=1e-4)

    # Verify semantic similarity: related statements should score higher than unrelated ones
    vec_related = embedder.embed_text("Work from home and office schedule policy.")
    vec_unrelated = embedder.embed_text("Baking chocolate chip cookies in an oven.")

    sim_related = BaseEmbeddingGenerator.cosine_similarity(vec, vec_related)
    sim_unrelated = BaseEmbeddingGenerator.cosine_similarity(vec, vec_unrelated)
    assert sim_related > sim_unrelated
