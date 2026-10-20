"""
Module 2: Automated Evaluation Engine — Live Benchmark Runner.

Executes the complete 7-stage Module 1 RAG pipeline against the 10-sample
golden benchmark dataset (hr_policy_benchmark.json) and computes the Evaluation Triad:
  1. Faithfulness (Groundedness / Hallucination Detection)
  2. Answer Correctness (Semantic & Factual Alignment)
  3. Context Precision (Retrieval Relevance)

Supports high-speed LLM-as-a-Judge via Groq and offline deterministic scoring.
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

from AeroqAI.models.evaluation import EvaluationSample, BenchmarkReport
from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store
from AeroqAI.modules.module_1_rag.reranker import get_reranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator
from AeroqAI.modules.module_2_evaluation.evaluator import get_evaluator


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 85)
    print(" 🚀 AeroqAI: Module 2 Automated Evaluation Benchmark Runner")
    print("=" * 85)

    benchmark_path = Path("AeroqAI/data/evaluation_sets/hr_policy_benchmark.json")
    if not benchmark_path.exists():
        print(f"Error: Benchmark dataset not found at {benchmark_path}")
        sys.exit(1)

    with open(benchmark_path, "r", encoding="utf-8") as f:
        raw_samples = json.load(f)
    samples = [EvaluationSample(**s) for s in raw_samples]
    print(f"Loaded {len(samples)} golden benchmark evaluation samples from {benchmark_path.name}.")

    # Initialize RAG Pipeline
    print("\n--- Initializing Module 1 RAG Pipeline ---")
    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    loader = PDFDocumentLoader(extract_empty_pages=False)
    pages = loader.load_file(pdf_path)

    cleaner = TextCleaner()
    cleaned = cleaner.clean_documents(pages)

    chunker = TextChunker(chunk_size=500, chunk_overlap=50, strategy="recursive")
    chunks = chunker.chunk_documents(cleaned)

    embedder = get_embedding_generator(provider="sentence-transformers", model_name="all-MiniLM-L6-v2")
    embedded = embedder.embed_chunks(chunks)

    vector_store = get_vector_store(store_type="memory")
    vector_store.add_chunks(embedded)

    reranker = get_reranker(provider="cross-encoder", model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    
    # Try Groq generator first if key is present, otherwise fallback to deterministic mock
    has_groq = bool(os.getenv("GROQ_API_KEY") or Path(".env").exists())
    gen_provider = "groq" if has_groq else "mock"
    generator = get_llm_generator(provider=gen_provider)
    print(f"Generator Model: {generator.model_name} (Provider: {generator.provider})")

    # Initialize Evaluator (LLM-as-a-Judge if Groq available, else Deterministic)
    eval_provider = "groq" if has_groq else "deterministic"
    evaluator = get_evaluator(provider=eval_provider, pass_threshold=0.70)
    print(f"Evaluator Engine: {evaluator.model_name} (Provider: {evaluator.provider})")

    def run_pipeline(query: str) -> Tuple[str, List[str]]:
        """Adapter invoking RAG retrieve ➡️ rerank ➡️ generate."""
        retrieval = vector_store.search_text(query_text=query, embedder=embedder, top_k=5)
        reranked = reranker.rerank(query=query, search_results=retrieval, top_k=2)
        gen_result = generator.generate(query=query, context=reranked)
        contexts = [r.chunk.content for r in reranked.results]
        return gen_result.answer, contexts

    print("\n" + "=" * 85)
    print(f" Running Automated Evaluation Benchmark ({len(samples)} Samples)")
    print("=" * 85)

    report = evaluator.evaluate_dataset(
        dataset_name="HR Policy Golden Evaluation Benchmark",
        samples=samples,
        pipeline_fn=run_pipeline
    )

    # Print Detailed Per-Sample Scores
    print("\n" + "-" * 85)
    print(f"{'Sample ID':<18} | {'Faithfulness':<12} | {'Correctness':<12} | {'Precision':<10} | {'Overall':<8} | {'Status'}")
    print("-" * 85)
    for res in report.sample_results:
        status_tag = "✅ PASS" if res.passed else "❌ FAIL"
        print(f"{res.sample_id:<18} | {res.faithfulness.score:<12.4f} | {res.answer_correctness.score:<12.4f} | "
              f"{res.context_precision.score:<10.4f} | {res.overall_score:<8.4f} | {status_tag}")

    print("-" * 85)
    print("\n" + report.format_summary_table())

    # Export report to JSON artifact
    output_file = Path("benchmark_results.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
    print(f"\n📁 Full detailed benchmark artifact saved to: {output_file.resolve()}")


if __name__ == "__main__":
    main()
