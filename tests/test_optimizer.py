"""Unit tests for Module 3: RAG Optimizer."""
from unittest.mock import MagicMock
import pytest

from AeroqAI.models.document import CleanedDocument, DocumentMetadata
from AeroqAI.models.evaluation import (
    EvaluationSample,
    MetricScore,
    SampleEvaluationResult,
    BenchmarkReport
)
from AeroqAI.models.optimization import (
    PipelineConfig,
    OptimizationTrial,
    OptimizationResult
)
from AeroqAI.modules.module_3_optimizer.optimizer import RAGOptimizer
from AeroqAI.modules.module_2_evaluation.evaluator import DeterministicEvaluator


def test_pipeline_config_contract():
    """Verify PipelineConfig defaults and custom attributes."""
    cfg = PipelineConfig(
        config_id="cfg_test_1",
        chunk_size=400,
        chunk_overlap=50,
        top_k=3,
        use_reranker=True,
        reranker_top_k=2
    )
    assert cfg.config_id == "cfg_test_1"
    assert cfg.chunk_size == 400
    assert cfg.chunk_overlap == 50
    assert cfg.top_k == 3
    assert cfg.use_reranker is True
    assert cfg.reranker_top_k == 2
    assert cfg.generator_provider == "mock"


def test_pareto_frontier_logic():
    """Verify multi-objective non-dominated sorting across Quality, Latency, and Cost."""
    dummy_report = BenchmarkReport(
        dataset_name="dummy",
        evaluator_model="deterministic",
        total_samples=1,
        passed_samples=1,
        failed_samples=0,
        pass_rate=100.0,
        mean_faithfulness=1.0,
        mean_correctness=1.0,
        mean_context_precision=1.0,
        mean_overall_score=1.0,
        sample_results=[]
    )

    cfg = PipelineConfig(config_id="c1", chunk_size=500, chunk_overlap=50)

    # Trial A: Highest quality (0.95), Higher latency (500ms), Higher cost
    trial_a = OptimizationTrial(
        trial_id="A",
        config=cfg,
        benchmark_report=dummy_report,
        overall_quality_score=0.95,
        faithfulness=1.0,
        answer_correctness=0.90,
        context_precision=0.95,
        avg_latency_ms=500.0,
        estimated_cost_per_1k_queries=0.08
    )

    # Trial B: High quality (0.90), Very low latency (150ms), Low cost
    trial_b = OptimizationTrial(
        trial_id="B",
        config=cfg,
        benchmark_report=dummy_report,
        overall_quality_score=0.90,
        faithfulness=0.95,
        answer_correctness=0.85,
        context_precision=0.90,
        avg_latency_ms=150.0,
        estimated_cost_per_1k_queries=0.02
    )

    # Trial C: Dominated by B (Lower quality 0.80, Higher latency 250ms, Higher cost 0.04)
    trial_c = OptimizationTrial(
        trial_id="C",
        config=cfg,
        benchmark_report=dummy_report,
        overall_quality_score=0.80,
        faithfulness=0.80,
        answer_correctness=0.80,
        context_precision=0.80,
        avg_latency_ms=250.0,
        estimated_cost_per_1k_queries=0.04
    )

    frontier = RAGOptimizer.compute_pareto_frontier([trial_a, trial_b, trial_c])
    pareto_ids = [t.trial_id for t in frontier]

    assert "A" in pareto_ids
    assert "B" in pareto_ids
    assert "C" not in pareto_ids
    assert trial_c.is_pareto_optimal is False
    assert trial_a.is_pareto_optimal is True
    assert trial_b.is_pareto_optimal is True


def test_optimizer_embedding_cache():
    """Verify that chunking and embeddings are cached per (chunk_size, chunk_overlap, strategy)."""
    meta = DocumentMetadata(source_file="test.pdf", page_number=1, total_pages=1, char_count=100, word_count=20, file_size_bytes=100)
    cleaned_doc = CleanedDocument(
        doc_id="doc_cache_test",
        content="AeroqAI RAG optimization system provides automated hyperparameter tuning and evaluation metrics.",
        raw_content="AeroqAI RAG optimization system provides automated hyperparameter tuning and evaluation metrics.",
        metadata=meta
    )

    optimizer = RAGOptimizer(
        cleaned_documents=[cleaned_doc],
        evaluation_samples=[],
        verbose=False
    )

    # First call generates chunks and embeddings
    chunks_1 = optimizer._get_or_create_embedded_chunks(chunk_size=300, chunk_overlap=30)
    assert len(chunks_1) > 0
    assert (300, 30, "recursive") in optimizer._embedding_cache

    # Mock embedder to verify subsequent calls retrieve directly from cache without re-embedding
    optimizer.embedder.embed_chunks = MagicMock(side_effect=RuntimeError("Embedder should not be called!"))
    chunks_2 = optimizer._get_or_create_embedded_chunks(chunk_size=300, chunk_overlap=30)
    assert chunks_1 == chunks_2


def test_optimizer_grid_execution():
    """Verify full end-to-end grid sweep across candidate configurations."""
    meta = DocumentMetadata(source_file="policy.pdf", page_number=1, total_pages=1, char_count=200, word_count=40, file_size_bytes=500)
    cleaned_doc = CleanedDocument(
        doc_id="doc_grid_test",
        content=(
            "Company Leave Policy: Full-time employees accrue 20 days of paid annual leave per calendar year. "
            "Up to 5 unused leave days can be carried over into the next consecutive calendar year. "
            "Leave requests must be submitted through the portal at least 7 calendar days in advance."
        ),
        raw_content=(
            "Company Leave Policy: Full-time employees accrue 20 days of paid annual leave per calendar year. "
            "Up to 5 unused leave days can be carried over into the next consecutive calendar year. "
            "Leave requests must be submitted through the portal at least 7 calendar days in advance."
        ),
        metadata=meta
    )

    sample = EvaluationSample(
        sample_id="test_sample_1",
        query="How many annual leave days do full-time employees receive?",
        ground_truth_answer="Full-time employees receive 20 days of paid annual leave per calendar year.",
        reference_contexts=["Full-time employees accrue 20 days of paid annual leave per calendar year."]
    )

    optimizer = RAGOptimizer(
        cleaned_documents=[cleaned_doc],
        evaluation_samples=[sample],
        evaluator=DeterministicEvaluator(),
        generator_provider="mock",
        verbose=False
    )

    result = optimizer.optimize_grid(
        search_space_name="Mini Unit Test Grid",
        chunk_sizes=[250, 450],
        chunk_overlaps=[20],
        top_k_values=[1, 2],
        use_reranker_options=[False]
    )

    assert isinstance(result, OptimizationResult)
    assert result.total_trials == 4  # 2 chunk_sizes * 1 overlap * 2 top_k * 1 reranker_option
    assert len(result.all_trials) == 4
    assert result.best_trial is not None
    assert result.fastest_trial is not None
    assert len(result.pareto_frontier) >= 1

    summary_table = result.format_summary_table()
    assert "Mini Unit Test Grid" in summary_table
    assert "Pareto Optimal Variants" in summary_table
