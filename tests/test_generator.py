"""Unit tests for Module 1 — Stage 7 Context Assembly & LLM Generator."""
from unittest.mock import MagicMock, patch
import pytest

from AeroqAI.models.chunk import TextChunk, ChunkMetadata, EmbeddedChunk
from AeroqAI.models.retrieval import SearchResult, RetrievalResult, RerankedSearchResult, RerankResult
from AeroqAI.models.generation import SourceCitation, GenerationResult
from AeroqAI.modules.module_1_rag.generator import (
    BaseLLMGenerator,
    DeterministicMockGenerator,
    OpenAIGenerator,
    get_llm_generator
)


def _create_sample_embedded_chunk(chunk_id: str, page: int, text: str) -> EmbeddedChunk:
    """Helper creating an EmbeddedChunk fixture."""
    meta = ChunkMetadata(
        doc_id="hr_policy.pdf",
        source_file="hr_policy.pdf",
        page_number=page,
        char_start=0,
        char_end=len(text),
        word_count=len(text.split()),
        token_count=len(text.split()),
        strategy="recursive",
        chunk_size=500,
        chunk_overlap=50
    )
    return EmbeddedChunk(
        chunk_id=chunk_id,
        content=text,
        metadata=meta,
        embedding=[0.1] * 384,
        embedding_model="mock-embedder",
        embedding_dimension=384
    )


def test_assemble_context_from_retrieval_result():
    """Verify assemble_context formats SearchResults into numbered citation blocks."""
    chunk1 = _create_sample_embedded_chunk(
        "chunk_1", 3, "Employees receive 20 days of paid annual leave per year."
    )
    chunk2 = _create_sample_embedded_chunk(
        "chunk_2", 3, "Sick leave requires a medical certificate after 3 consecutive days."
    )
    retrieval_res = RetrievalResult(
        query="leave rules",
        results=[
            SearchResult(chunk=chunk1, similarity_score=0.88, rank=1),
            SearchResult(chunk=chunk2, similarity_score=0.74, rank=2)
        ],
        top_k=2,
        total_retrieved=2,
        retrieval_latency_ms=12.5,
        embedding_model="mock-embedder"
    )

    gen = DeterministicMockGenerator()
    assembled, citations = gen.assemble_context(retrieval_res)

    assert "[Source 1: hr_policy.pdf | Page 3 | Chunk: chunk_1]" in assembled
    assert "Employees receive 20 days of paid annual leave per year." in assembled
    assert "[Source 2: hr_policy.pdf | Page 3 | Chunk: chunk_2]" in assembled
    assert len(citations) == 2
    assert citations[0].doc_id == "hr_policy.pdf"
    assert citations[0].page_number == 3
    assert citations[0].relevance_score == 0.88


def test_assemble_context_from_rerank_result():
    """Verify assemble_context formats RerankResult and preserves rerank scores."""
    chunk = _create_sample_embedded_chunk(
        "chunk_hybrid", 2, "Core working hours are 10:00 AM to 4:00 PM with hybrid flexibility."
    )
    rerank_res = RerankResult(
        query="working hours",
        results=[
            RerankedSearchResult(
                chunk=chunk,
                original_score=0.65,
                original_rank=2,
                rerank_score=8.75,
                new_rank=1
            )
        ],
        top_k=1,
        total_reranked=1,
        rerank_latency_ms=25.0,
        reranker_model="mock-reranker"
    )

    gen = DeterministicMockGenerator()
    assembled, citations = gen.assemble_context(rerank_res)

    assert "[Source 1: hr_policy.pdf | Page 2 | Chunk: chunk_hybrid]" in assembled
    assert len(citations) == 1
    assert citations[0].relevance_score == 8.75
    assert citations[0].chunk_id == "chunk_hybrid"


def test_assemble_context_from_plain_string():
    """Verify raw strings pass through assemble_context cleanly."""
    gen = DeterministicMockGenerator()
    raw = "Direct reference passage provided without structured models."
    assembled, citations = gen.assemble_context(raw)
    assert assembled == raw
    assert citations == []


def test_deterministic_mock_generator_grounded_answer():
    """Verify DeterministicMockGenerator synthesizes answers with citations when query matches context."""
    chunk = _create_sample_embedded_chunk(
        "chunk_leave", 3,
        "Paid Annual Leave: Full-time employees accrue 20 days of paid annual leave per calendar year. "
        "A maximum of 5 unused leave days can be carried over into the following year."
    )
    retrieval_res = RetrievalResult(
        query="How many days of paid annual leave do employees accrue?",
        results=[SearchResult(chunk=chunk, similarity_score=0.91, rank=1)],
        top_k=1,
        total_retrieved=1,
        retrieval_latency_ms=10.0,
        embedding_model="mock-embedder"
    )

    gen = DeterministicMockGenerator()
    result = gen.generate(
        query="How many days of paid annual leave do employees accrue?",
        context=retrieval_res
    )

    assert isinstance(result, GenerationResult)
    assert result.grounded is True
    assert "Based on the provided documents" in result.answer
    assert "20 days of paid annual leave" in result.answer
    assert len(result.sources) == 1
    assert result.sources[0].page_number == 3
    assert result.prompt_tokens is not None and result.prompt_tokens > 0
    assert result.completion_tokens is not None and result.completion_tokens > 0
    assert result.total_tokens == result.prompt_tokens + result.completion_tokens
    assert result.latency_ms >= 0.0


def test_deterministic_mock_generator_ungrounded_fallback():
    """Verify fallback refusal when context contains no overlapping keywords."""
    chunk = _create_sample_embedded_chunk(
        "chunk_it", 4, "Employees must change their corporate passwords every 90 days."
    )
    retrieval_res = RetrievalResult(
        query="What is the policy for interstellar spacecraft warp drives?",
        results=[SearchResult(chunk=chunk, similarity_score=0.12, rank=1)],
        top_k=1,
        total_retrieved=1,
        retrieval_latency_ms=10.0,
        embedding_model="mock-embedder"
    )

    gen = DeterministicMockGenerator()
    result = gen.generate(
        query="What is the policy for interstellar spacecraft warp drives?",
        context=retrieval_res
    )

    assert result.grounded is False
    assert result.answer == "I cannot find the answer in the provided documents."


def test_generation_result_get_formatted_sources():
    """Verify get_formatted_sources creates markdown formatted citations."""
    gen_result = GenerationResult(
        query="leave days",
        answer="Employees accrue 20 days.",
        sources=[
            SourceCitation(
                doc_id="doc1",
                source_file="handbook.pdf",
                page_number=3,
                chunk_id="chunk_01",
                relevance_score=0.92
            ),
            SourceCitation(
                doc_id="doc1",
                source_file="handbook.pdf",
                page_number=4,
                chunk_id="chunk_02",
                relevance_score=0.85
            )
        ],
        model_name="mock-model",
        provider="mock",
        latency_ms=5.0
    )

    formatted = gen_result.get_formatted_sources()
    assert "[1] handbook.pdf (Page 3, Chunk: chunk_01) (Score: 0.9200)" in formatted
    assert "[2] handbook.pdf (Page 4, Chunk: chunk_02) (Score: 0.8500)" in formatted


def test_factory_generator():
    """Verify get_llm_generator factory resolves correct providers and validates bad ones."""
    mock_gen = get_llm_generator("mock")
    assert isinstance(mock_gen, DeterministicMockGenerator)
    assert mock_gen.provider == "mock"

    with pytest.raises(ValueError, match="Unsupported LLM generator provider"):
        get_llm_generator("unknown_provider")


def test_openai_generator_missing_api_key():
    """Verify OpenAIGenerator raises ValueError if api_key is missing."""
    with patch.dict("os.environ", {}, clear=True):
        gen = OpenAIGenerator(api_key=None)
        with pytest.raises(ValueError, match="OpenAI API key is missing"):
            gen.generate("test question", "test context")


def test_openai_generator_mocked_call():
    """Verify OpenAIGenerator successfully invokes client and processes usage metrics."""
    mock_choice = MagicMock()
    mock_choice.message.content = "According to Section 3, employees receive 20 days of annual leave."

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 120
    mock_usage.completion_tokens = 18
    mock_usage.total_tokens = 138

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        gen = OpenAIGenerator(api_key="sk-test-fake-key", model_name="gpt-4o-mini")
        result = gen.generate(
            query="How many leave days?",
            context="[Source 1: hr.pdf | Page 3 | Chunk: c1]\n20 days annual leave."
        )

        assert result.provider == "openai"
        assert result.model_name == "gpt-4o-mini"
        assert result.answer == "According to Section 3, employees receive 20 days of annual leave."
        assert result.prompt_tokens == 120
        assert result.completion_tokens == 18
        assert result.total_tokens == 138
        assert result.grounded is True


def test_groq_generator_factory_and_call():
    """Verify GroqGenerator resolves via factory and invokes endpoint with groq provider."""
    from AeroqAI.modules.module_1_rag.generator import GroqGenerator

    mock_choice = MagicMock()
    mock_choice.message.content = "Employees accrue 20 days paid leave."

    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 95
    mock_usage.completion_tokens = 12
    mock_usage.total_tokens = 107

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.usage = mock_usage

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai_cls.return_value = mock_client

        gen = get_llm_generator("groq", api_key="gsk-test-key")
        assert isinstance(gen, GroqGenerator)
        assert gen.provider == "groq"
        assert gen.base_url == "https://api.groq.com/openai/v1"

        result = gen.generate(
            query="Leave policy?",
            context="[Source 1: hr.pdf | Page 3 | Chunk: c1]\n20 days paid leave."
        )
        assert result.provider == "groq"
        assert result.answer == "Employees accrue 20 days paid leave."
        assert result.total_tokens == 107
        assert result.grounded is True

