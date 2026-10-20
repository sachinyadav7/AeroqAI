"""
Module 3: RAG Optimizer — Live Hyperparameter Grid & Pareto Frontier Demo.

Explores combinations of chunk sizes, overlap ratios, retrieval depths (Top-K),
and neural reranking to find the optimal trade-off between Quality, Latency, and Cost.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import List

from AeroqAI.models.document import CleanedDocument
from AeroqAI.models.evaluation import EvaluationSample
from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_2_evaluation.evaluator import get_evaluator
from AeroqAI.modules.module_3_optimizer.optimizer import RAGOptimizer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AeroqAI RAG Optimizer Grid Search Demo")
    parser.add_argument(
        "--space",
        choices=["quick", "full"],
        default="quick",
        help="Search space size ('quick'=4 configs, 'full'=12 configs)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=5,
        help="Number of evaluation samples from the benchmark to test per trial (default: 5)"
    )
    parser.add_argument(
        "--judge",
        choices=["deterministic", "groq", "openai"],
        default="deterministic",
        help="Evaluator engine ('deterministic' for rapid offline search, 'groq' for live LLM judge)"
    )
    parser.add_argument(
        "--generator",
        choices=["mock", "groq", "openai"],
        default="mock",
        help="Generation provider to use in RAG pipeline ('mock' or 'groq')"
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    print("=" * 85)
    print(" ⚡ AeroqAI: Module 3 RAG Hyperparameter Optimizer & Pareto Frontier Explorer")
    print("=" * 85)

    # Step 1: Load and clean document
    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        sys.exit(1)

    print(f"\n[1/4] Ingesting document: {pdf_path.name}")
    loader = PDFDocumentLoader(extract_empty_pages=False)
    raw_pages = loader.load_file(pdf_path)

    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_pages)
    print(f"      Loaded {len(cleaned_docs)} cleaned pages into document corpus.")

    # Step 2: Load evaluation samples
    benchmark_path = Path("AeroqAI/data/evaluation_sets/hr_policy_benchmark.json")
    if not benchmark_path.exists():
        print(f"Error: Benchmark dataset not found at {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        raw_samples = json.load(f)
    all_samples = [EvaluationSample(**s) for s in raw_samples]
    active_samples = all_samples[: args.samples]
    print(f"[2/4] Selected {len(active_samples)} benchmark evaluation queries for tuning sweep.")

    # Step 3: Initialize Evaluator Engine
    print(f"[3/4] Initializing Evaluator: '{args.judge}' | Generator: '{args.generator}'")
    evaluator = get_evaluator(provider=args.judge, pass_threshold=0.70)

    # Step 4: Configure Search Space
    if args.space == "quick":
        chunk_sizes = [400, 800]
        chunk_overlaps = [60]
        top_k_values = [3]
        reranker_options = [False, True]
        space_name = "Quick Sweep (Chunk Size x Reranker)"
    else:
        chunk_sizes = [300, 600, 900]
        chunk_overlaps = [50, 100]
        top_k_values = [2, 4]
        reranker_options = [False, True]
        space_name = "Comprehensive Multi-Parameter Grid"

    # Step 5: Execute Grid Search with Caching
    optimizer = RAGOptimizer(
        cleaned_documents=cleaned_docs,
        evaluation_samples=active_samples,
        evaluator=evaluator,
        generator_provider=args.generator,
        verbose=True
    )

    print(f"\n[4/4] Executing RAG Optimization Grid across candidate pipelines...")
    result = optimizer.optimize_grid(
        search_space_name=space_name,
        chunk_sizes=chunk_sizes,
        chunk_overlaps=chunk_overlaps,
        top_k_values=top_k_values,
        use_reranker_options=reranker_options,
        reranker_top_k=2
    )

    # Step 6: Display Markdown Summary & Pareto Analysis
    print("\n" + "=" * 85)
    print(" 🏁 Optimization Results & Pareto Frontier Analysis")
    print("=" * 85)
    print(result.format_summary_table())

    print("\n" + "-" * 85)
    print("🌟 Optimal Pipeline Recommendations:")
    print(f"  • Best Quality Target : Trial `{result.best_trial.trial_id}` ({result.best_trial.config.config_id})")
    print(f"                          Quality Score: {result.best_trial.overall_quality_score:.4f} | Latency: {result.best_trial.avg_latency_ms:.1f}ms")
    print(f"  • Lowest Latency Target: Trial `{result.fastest_trial.trial_id}` ({result.fastest_trial.config.config_id})")
    print(f"                          Latency: {result.fastest_trial.avg_latency_ms:.1f}ms | Quality Score: {result.fastest_trial.overall_quality_score:.4f}")
    print(f"  • Pareto Frontier Size: {len(result.pareto_frontier)} non-dominated optimal balance points")
    print("-" * 85)

    # Step 7: Export to JSON artifact
    output_file = Path("optimization_report.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"\n📁 Detailed Optimization Report written to: {output_file.resolve()}")


if __name__ == "__main__":
    main()
