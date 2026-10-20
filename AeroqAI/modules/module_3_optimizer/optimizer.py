"""
Module 3: RAG Optimizer.

Automated hyperparameter optimization, grid search exploration, and Pareto frontier
analysis across chunk sizes, overlap ratios, retrieval depths (Top-K), and reranking.
"""
import itertools
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Sequence

from AeroqAI.models.document import CleanedDocument
from AeroqAI.models.chunk import EmbeddedChunk
from AeroqAI.models.evaluation import EvaluationSample, BenchmarkReport
from AeroqAI.models.optimization import PipelineConfig, OptimizationTrial, OptimizationResult
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator, BaseEmbeddingGenerator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store
from AeroqAI.modules.module_1_rag.reranker import get_reranker, BaseReranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator, BaseLLMGenerator
from AeroqAI.modules.module_2_evaluation.evaluator import BaseEvaluator, get_evaluator


class RAGOptimizer:
    """
    Automated optimization engine for RAG pipelines.
    Searches hyperparameter spaces, evaluates triad metrics, and identifies
    the Pareto optimal trade-offs between Quality, Speed, and Cost.
    """

    def __init__(
        self,
        cleaned_documents: Sequence[CleanedDocument],
        evaluation_samples: Sequence[EvaluationSample],
        evaluator: Optional[BaseEvaluator] = None,
        embedding_generator: Optional[BaseEmbeddingGenerator] = None,
        generator_provider: str = "mock",
        verbose: bool = True
    ) -> None:
        self.cleaned_documents = list(cleaned_documents)
        self.evaluation_samples = list(evaluation_samples)
        self.evaluator = evaluator or get_evaluator("deterministic")
        self.embedder = embedding_generator or get_embedding_generator("sentence-transformers", "all-MiniLM-L6-v2")
        self.generator_provider = generator_provider
        self.verbose = verbose

        # Cache of embedded chunks keyed by (chunk_size, chunk_overlap, strategy)
        self._embedding_cache: Dict[Tuple[int, int, str], List[EmbeddedChunk]] = {}

    def _get_or_create_embedded_chunks(
        self,
        chunk_size: int,
        chunk_overlap: int,
        strategy: str = "recursive"
    ) -> List[EmbeddedChunk]:
        """Retrieve embedded chunks from cache or compute and cache them."""
        cache_key = (chunk_size, chunk_overlap, strategy)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            strategy=strategy
        )
        chunks = chunker.chunk_documents(self.cleaned_documents)
        embedded_chunks = self.embedder.embed_chunks(chunks)

        self._embedding_cache[cache_key] = embedded_chunks
        return embedded_chunks

    def _evaluate_configuration(
        self,
        trial_id: str,
        config: PipelineConfig
    ) -> OptimizationTrial:
        """Execute a full benchmark evaluation trial for a single pipeline configuration."""
        start_time = time.perf_counter()

        # Step 1: Ingest cached chunks into an in-memory vector index
        embedded_chunks = self._get_or_create_embedded_chunks(
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
            strategy=config.chunk_strategy
        )
        vector_store = get_vector_store(store_type="memory")
        vector_store.add_chunks(embedded_chunks)

        # Step 2: Initialize Reranker if requested
        reranker: Optional[BaseReranker] = None
        if config.use_reranker:
            reranker = get_reranker(
                provider="cross-encoder",
                model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"
            )

        # Step 3: Initialize Generator
        generator: BaseLLMGenerator = get_llm_generator(
            provider=config.generator_provider
        )

        # Step 4: Define trial RAG execution adapter
        latencies: List[float] = []

        def pipeline_fn(query: str) -> Tuple[str, List[str]]:
            q_start = time.perf_counter()
            retrieval_res = vector_store.search_text(
                query_text=query,
                embedder=self.embedder,
                top_k=config.top_k
            )

            if reranker and config.use_reranker:
                final_res = reranker.rerank(
                    query=query,
                    search_results=retrieval_res,
                    top_k=config.reranker_top_k
                )
                contexts = [r.chunk.content for r in final_res.results]
            else:
                final_res = retrieval_res
                contexts = [r.chunk.content for r in final_res.results]

            gen_res = generator.generate(query=query, context=final_res)
            latencies.append((time.perf_counter() - q_start) * 1000.0)
            return gen_res.answer, contexts

        # Step 5: Evaluate against golden benchmark dataset
        report: BenchmarkReport = self.evaluator.evaluate_dataset(
            dataset_name=f"Trial {trial_id} ({config.config_id})",
            samples=self.evaluation_samples,
            pipeline_fn=pipeline_fn
        )

        avg_latency = round(sum(latencies) / max(1, len(latencies)), 2)

        # Estimated cost model: assumes $0.15 / 1M input tokens + $0.60 / 1M output tokens
        # Groq Llama / open-source rough equivalent estimate per 1,000 queries
        est_tokens_per_query = config.chunk_size * (config.reranker_top_k if config.use_reranker else config.top_k) // 4
        cost_per_1k = round((est_tokens_per_query * 1000 / 1_000_000) * 0.20, 4)

        return OptimizationTrial(
            trial_id=trial_id,
            config=config,
            benchmark_report=report,
            overall_quality_score=report.mean_overall_score,
            faithfulness=report.mean_faithfulness,
            answer_correctness=report.mean_correctness,
            context_precision=report.mean_context_precision,
            avg_latency_ms=avg_latency,
            estimated_cost_per_1k_queries=cost_per_1k,
            is_pareto_optimal=False
        )

    @staticmethod
    def compute_pareto_frontier(trials: List[OptimizationTrial]) -> List[OptimizationTrial]:
        """
        Identify the non-dominated Pareto optimal configurations.
        A trial A dominates B if:
          - A.quality >= B.quality AND A.latency <= B.latency AND A.cost <= B.cost
          - AND at least one metric is strictly superior.
        """
        frontier: List[OptimizationTrial] = []

        for candidate in trials:
            dominated = False
            for other in trials:
                if other.trial_id == candidate.trial_id:
                    continue

                better_or_equal = (
                    other.overall_quality_score >= candidate.overall_quality_score and
                    other.avg_latency_ms <= candidate.avg_latency_ms and
                    other.estimated_cost_per_1k_queries <= candidate.estimated_cost_per_1k_queries
                )
                strictly_better = (
                    other.overall_quality_score > candidate.overall_quality_score or
                    other.avg_latency_ms < candidate.avg_latency_ms or
                    other.estimated_cost_per_1k_queries < candidate.estimated_cost_per_1k_queries
                )

                if better_or_equal and strictly_better:
                    dominated = True
                    break

            if not dominated:
                candidate.is_pareto_optimal = True
                frontier.append(candidate)
            else:
                candidate.is_pareto_optimal = False

        # Sort Pareto frontier by Quality descending
        frontier.sort(key=lambda t: t.overall_quality_score, reverse=True)
        return frontier

    def optimize_grid(
        self,
        search_space_name: str,
        chunk_sizes: List[int],
        chunk_overlaps: List[int],
        top_k_values: List[int],
        use_reranker_options: List[bool] = [True],
        reranker_top_k: int = 2
    ) -> OptimizationResult:
        """
        Execute hyperparameter grid search across the Cartesian product of parameters.
        """
        grid_start = time.perf_counter()
        combinations = list(itertools.product(
            chunk_sizes,
            chunk_overlaps,
            top_k_values,
            use_reranker_options
        ))

        trials: List[OptimizationTrial] = []
        if self.verbose:
            print(f"\n🔍 Launching RAG Optimizer Grid Search: '{search_space_name}'")
            print(f"📊 Total Configurations to Evaluate: {len(combinations)}")
            print("-" * 85)

        for i, (c_size, c_overlap, top_k, use_rr) in enumerate(combinations, start=1):
            # Ensure overlap < chunk_size
            if c_overlap >= c_size:
                continue

            trial_id = f"trial_{i:03d}"
            rr_tag = f"rrON_k{reranker_top_k}" if use_rr else "rrOFF"
            config_id = f"cfg_c{c_size}_o{c_overlap}_k{top_k}_{rr_tag}"

            config = PipelineConfig(
                config_id=config_id,
                chunk_size=c_size,
                chunk_overlap=c_overlap,
                chunk_strategy="recursive",
                top_k=top_k,
                use_reranker=use_rr,
                reranker_top_k=reranker_top_k if use_rr else top_k,
                generator_provider=self.generator_provider
            )

            trial = self._evaluate_configuration(trial_id=trial_id, config=config)
            trials.append(trial)

            if self.verbose:
                rr_str = "ON" if use_rr else "OFF"
                print(
                    f"[{i:02d}/{len(combinations):02d}] {trial_id} | Chunk: {c_size} | Overlap: {c_overlap} | "
                    f"Top-K: {top_k} | Reranker: {rr_str} ➡️ Quality: {trial.overall_quality_score:.4f} "
                    f"(Corr: {trial.answer_correctness:.4f}, Prec: {trial.context_precision:.4f}) | "
                    f"Latency: {trial.avg_latency_ms:.1f}ms",
                    flush=True
                )

        # Compute Pareto Frontier
        pareto_trials = self.compute_pareto_frontier(trials)

        best_quality_trial = max(trials, key=lambda t: t.overall_quality_score)
        fastest_trial = min(trials, key=lambda t: t.avg_latency_ms)
        total_time_ms = (time.perf_counter() - grid_start) * 1000.0

        return OptimizationResult(
            search_space_name=search_space_name,
            total_trials=len(trials),
            best_trial=best_quality_trial,
            fastest_trial=fastest_trial,
            pareto_frontier=pareto_trials,
            all_trials=trials,
            total_optimization_latency_ms=round(total_time_ms, 2)
        )
