"""Unit tests for Module 6: Interactive RAG Debugger."""
import pytest

from AeroqAI.models.chunk import TextChunk, ChunkMetadata, EmbeddedChunk
from AeroqAI.models.trace import (
    ChunkTraceItem,
    RetrievalStageTrace,
    RerankStageTrace,
    PromptAssemblyStageTrace,
    GenerationStageTrace,
    QueryExecutionTrace
)
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store
from AeroqAI.modules.module_1_rag.reranker import get_reranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator
from AeroqAI.modules.module_2_evaluation.evaluator import DeterministicEvaluator
from AeroqAI.modules.module_6_debugger.debugger import RAGDebugger


@pytest.fixture
def populated_vector_store():
    """Populates an in-memory vector store with sample chunks for debugging."""
    embedder = get_embedding_generator(provider="mock")
    store = get_vector_store(store_type="memory")

    chunks = [
        TextChunk(
            chunk_id="chunk_leave_01",
            content="Employees receive 20 days of paid annual leave per calendar year. Unused leave can be carried over up to 5 days.",
            metadata=ChunkMetadata(doc_id="doc_hr_policy", source_file="hr_policy.pdf", page_number=2, chunk_index=0)
        ),
        TextChunk(
            chunk_id="chunk_wfh_02",
            content="Employees may work remotely up to 2 days per week with direct manager pre-approval.",
            metadata=ChunkMetadata(doc_id="doc_hr_policy", source_file="hr_policy.pdf", page_number=4, chunk_index=1)
        ),
        TextChunk(
            chunk_id="chunk_medical_03",
            content="Medical insurance coverage begins on the first day of the calendar month following 30 days of employment.",
            metadata=ChunkMetadata(doc_id="doc_hr_policy", source_file="hr_policy.pdf", page_number=6, chunk_index=2)
        )
    ]

    embedded = embedder.embed_chunks(chunks)
    store.add_chunks(embedded)
    return store, embedder


def test_chunk_trace_item_contract():
    """Verify ChunkTraceItem attributes and rank shift calculations."""
    item = ChunkTraceItem(
        chunk_id="c_01",
        source_file="policy.pdf",
        page_number=3,
        content_snippet="Leave policy rules...",
        char_length=20,
        initial_retrieval_score=0.82,
        initial_rank=3,
        rerank_score=0.95,
        final_rank=1,
        rank_delta=2,
        retained_in_context=True
    )
    assert item.chunk_id == "c_01"
    assert item.rank_delta == 2
    assert item.retained_in_context is True


def test_debugger_trace_without_reranker(populated_vector_store):
    """Verify tracing execution through retrieval, prompt assembly, and generation without reranking."""
    store, embedder = populated_vector_store
    generator = get_llm_generator(provider="mock")

    debugger = RAGDebugger(
        vector_store=store,
        embedder=embedder,
        generator=generator,
        reranker=None
    )

    trace = debugger.trace_query(
        query="How many days of paid leave do employees receive?",
        top_k=2
    )

    assert isinstance(trace, QueryExecutionTrace)
    assert trace.query == "How many days of paid leave do employees receive?"
    assert trace.total_latency_ms >= 0.0
    assert trace.retrieval.total_candidates_found == 2
    assert trace.rerank is None
    assert trace.prompt_assembly.context_chunks_count == 2
    assert trace.generation.provider == "mock"
    assert len(trace.generation.generated_answer) > 0


def test_debugger_trace_with_reranker(populated_vector_store):
    """Verify tracing execution with neural cross-encoder reranking, checking rank deltas and pruning."""
    store, embedder = populated_vector_store
    generator = get_llm_generator(provider="mock")
    reranker = get_reranker(provider="mock")

    debugger = RAGDebugger(
        vector_store=store,
        embedder=embedder,
        generator=generator,
        reranker=reranker
    )

    trace = debugger.trace_query(
        query="What is the remote work policy?",
        top_k=3,
        rerank_top_k=1
    )

    assert trace.rerank is not None
    assert trace.rerank.top_k_retained == 1
    assert len(trace.rerank.reranked_chunks) == 3

    # The top retained candidate should have retained_in_context=True
    top_chunk = trace.rerank.reranked_chunks[0]
    assert top_chunk.retained_in_context is True
    assert top_chunk.final_rank == 1

    # Non-retained candidate
    pruned_chunk = trace.rerank.reranked_chunks[-1]
    assert pruned_chunk.retained_in_context is False


def test_debugger_trace_with_ground_truth_evaluation(populated_vector_store):
    """Verify on-the-spot real-time Triad evaluation against ground truth."""
    store, embedder = populated_vector_store
    generator = get_llm_generator(provider="mock")
    evaluator = DeterministicEvaluator()

    debugger = RAGDebugger(
        vector_store=store,
        embedder=embedder,
        generator=generator,
        reranker=None,
        evaluator=evaluator
    )

    gt = "Employees receive 20 days of paid annual leave."
    trace = debugger.trace_query(
        query="What is the annual leave allowance?",
        ground_truth_answer=gt,
        top_k=2
    )

    assert trace.evaluation is not None
    assert "faithfulness" in trace.evaluation
    assert "correctness" in trace.evaluation
    assert "precision" in trace.evaluation
    assert "overall" in trace.evaluation


def test_trace_report_markdown_formatting(populated_vector_store):
    """Verify markdown trace inspection report contains all required sections."""
    store, embedder = populated_vector_store
    generator = get_llm_generator(provider="mock")
    reranker = get_reranker(provider="mock")

    debugger = RAGDebugger(
        vector_store=store,
        embedder=embedder,
        generator=generator,
        reranker=reranker
    )

    trace = debugger.trace_query(
        query="Tell me about medical insurance coverage.",
        top_k=2,
        rerank_top_k=1
    )

    report = trace.format_trace_report()
    assert "AeroqAI Interactive RAG Query Trace" in report
    assert "Latency Waterfall Breakdown" in report
    assert "Candidate Passages & Score Transitions" in report
    assert "Final Generated Response" in report
    assert "Estimated Tokens" in report
