"""
Module 6: Interactive RAG Debugger — Live CLI Diagnostic Runner.

Provides step-by-step query profiling, latency waterfall analysis,
neural reranker rank shifts, assembled prompt inspection, and real-time evaluation.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store
from AeroqAI.modules.module_1_rag.reranker import get_reranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator
from AeroqAI.modules.module_2_evaluation.evaluator import get_evaluator
from AeroqAI.modules.module_6_debugger.debugger import RAGDebugger


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AeroqAI Interactive RAG Query Debugger")
    parser.add_argument(
        "--query",
        type=str,
        default="How many days of annual leave can be carried over into the next consecutive calendar year?",
        help="Query to inspect through the RAG pipeline"
    )
    parser.add_argument(
        "--ground-truth",
        type=str,
        default="Up to 5 unused leave days can be carried over into the next consecutive calendar year.",
        help="Optional expected reference answer for real-time Triad evaluation"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Initial vector retrieval depth (default: 5)"
    )
    parser.add_argument(
        "--rerank-top-k",
        type=int,
        default=2,
        help="Number of candidates retained after neural reranking (default: 2)"
    )
    parser.add_argument(
        "--disable-reranker",
        action="store_true",
        help="Disable neural Cross-Encoder reranking stage"
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    print("=" * 85)
    print(" 🔬 AeroqAI: Module 6 Interactive RAG Query Debugger & Step-by-Step Profiler")
    print("=" * 85)

    # Step 1: Load and ingest document
    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        sys.exit(1)

    print(f"\n[1/4] Preparing RAG corpus from: {pdf_path.name}")
    loader = PDFDocumentLoader(extract_empty_pages=False)
    pages = loader.load_file(pdf_path)

    cleaner = TextCleaner()
    cleaned = cleaner.clean_documents(pages)

    # Chunking tuned based on Module 3 optimizer findings (chunk size 800, overlap 60)
    chunker = TextChunker(chunk_size=800, chunk_overlap=60, strategy="recursive")
    chunks = chunker.chunk_documents(cleaned)

    embedder = get_embedding_generator(provider="sentence-transformers", model_name="all-MiniLM-L6-v2")
    embedded_chunks = embedder.embed_chunks(chunks)

    vector_store = get_vector_store(store_type="memory")
    vector_store.add_chunks(embedded_chunks)
    print(f"      Ingested {len(embedded_chunks)} embedded chunks into vector store.")

    # Step 2: Initialize Reranker and Generator
    reranker = None
    if not args.disable_reranker:
        reranker = get_reranker(provider="cross-encoder", model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")

    has_groq = bool(os.getenv("GROQ_API_KEY") or Path(".env").exists())
    gen_provider = "groq" if has_groq else "mock"
    generator = get_llm_generator(provider=gen_provider)

    evaluator = get_evaluator(provider="deterministic")

    print(f"[2/4] Pipeline Components Configured:")
    print(f"      • Retrieval Embedder : {embedder.model_name}")
    print(f"      • Neural Reranker    : {reranker.model_name if reranker else 'DISABLED'}")
    print(f"      • Generation Engine  : {generator.model_name} (Provider: {generator.provider})")
    print(f"      • Evaluation Judge   : {evaluator.model_name}")

    # Step 3: Run Interactive Debugger
    debugger = RAGDebugger(
        vector_store=vector_store,
        embedder=embedder,
        generator=generator,
        reranker=reranker,
        evaluator=evaluator
    )

    print(f"\n[3/4] Tracing Query Execution:")
    print(f"      Query: \"{args.query}\"")
    print("-" * 85)

    trace = debugger.trace_query(
        query=args.query,
        ground_truth_answer=args.ground_truth,
        top_k=args.top_k,
        rerank_top_k=args.rerank_top_k
    )

    # Step 4: Render Markdown Diagnostic Report
    print(trace.format_trace_report())
    print("-" * 85)

    # Step 5: Save JSON artifact
    output_path = Path("query_trace_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(trace.model_dump(), f, indent=2)
    print(f"\n📁 Full detailed query trace written to: {output_path.resolve()}")


if __name__ == "__main__":
    main()
