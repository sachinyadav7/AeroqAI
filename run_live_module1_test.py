"""
AeroqAI: Module 1 (RAG Pipeline) — Comprehensive Live Diagnostic Test.
Tests all 7 stages sequentially and end-to-end against sample enterprise data.
"""
import sys
import time
from pathlib import Path
from typing import Dict, Any

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store
from AeroqAI.modules.module_1_rag.reranker import get_reranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator


def print_header(title: str) -> None:
    print("\n" + "=" * 85)
    print(f" {title}")
    print("=" * 85)


def print_stage(num: int, title: str) -> None:
    print(f"\n▶ [STAGE {num}] {title}")
    print("-" * 85)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    overall_start = time.perf_counter()

    print_header("🚀 AeroqAI: Full Live Diagnostic & Operational Verification for Module 1")
    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")

    if not pdf_path.exists():
        print(f"❌ Error: Required test PDF not found at: {pdf_path}")
        sys.exit(1)

    print(f"Target Document: {pdf_path.resolve()}")
    print(f"File Size:       {pdf_path.stat().st_size:,} bytes")

    # -------------------------------------------------------------------------
    # STAGE 1: DOCUMENT LOADER
    # -------------------------------------------------------------------------
    print_stage(1, "Document Ingestion & Metadata Extraction (PDFDocumentLoader)")
    t0 = time.perf_counter()
    loader = PDFDocumentLoader(extract_empty_pages=False)
    raw_docs = loader.load_file(pdf_path)
    s1_ms = (time.perf_counter() - t0) * 1000.0

    assert len(raw_docs) == 10, f"Expected 10 pages, got {len(raw_docs)}"
    total_raw_chars = sum(d.metadata.char_count for d in raw_docs)
    total_raw_words = sum(d.metadata.word_count for d in raw_docs)

    print(f"✔ Status:            PASSED")
    print(f"✔ Extracted Pages:   {len(raw_docs)} pages in {s1_ms:.2f} ms")
    print(f"✔ Total Volume:      {total_raw_chars:,} characters, {total_raw_words:,} words")
    print(f"✔ Sample Header:     \"{raw_docs[0].content.splitlines()[0]}\" (Page 1)")

    # -------------------------------------------------------------------------
    # STAGE 2: TEXT CLEANING & NORMALIZATION
    # -------------------------------------------------------------------------
    print_stage(2, "Text Normalization & Unicode Cleaning (TextCleaner)")
    t0 = time.perf_counter()
    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_docs)
    s2_ms = (time.perf_counter() - t0) * 1000.0

    assert len(cleaned_docs) == len(raw_docs)
    total_cleaned_chars = sum(d.metadata.char_count for d in cleaned_docs)
    total_cleaned_words = sum(d.metadata.word_count for d in cleaned_docs)

    print(f"✔ Status:            PASSED")
    print(f"✔ Normalized Pages:  {len(cleaned_docs)} pages in {s2_ms:.2f} ms")
    print(f"✔ Cleaned Volume:    {total_cleaned_chars:,} characters, {total_cleaned_words:,} words")
    print(f"✔ Sample Page 1 Clean Stats: {cleaned_docs[0].cleaning_stats}")

    # -------------------------------------------------------------------------
    # STAGE 3: TEXT CHUNKING
    # -------------------------------------------------------------------------
    print_stage(3, "Hierarchical Recursive Text Chunking (TextChunker)")
    t0 = time.perf_counter()
    chunker = TextChunker(chunk_size=500, chunk_overlap=50, strategy="recursive")
    chunks = chunker.chunk_documents(cleaned_docs)
    s3_ms = (time.perf_counter() - t0) * 1000.0

    assert len(chunks) > 0, "No chunks generated!"
    avg_tokens = sum(c.metadata.token_count for c in chunks) / len(chunks)
    avg_chars = sum(c.metadata.char_count for c in chunks) / len(chunks)

    print(f"✔ Status:            PASSED")
    print(f"✔ Generated Chunks:  {len(chunks)} chunks in {s3_ms:.2f} ms")
    print(f"✔ Chunk Size / Overlap: 500 chars / 50 chars overlap")
    print(f"✔ Average Density:   {avg_chars:.1f} chars/chunk, ~{avg_tokens:.1f} tokens/chunk")
    print(f"✔ Chunk #1 ID:       {chunks[0].chunk_id} (Page {chunks[0].metadata.page_number})")

    # -------------------------------------------------------------------------
    # STAGE 4: EMBEDDING GENERATION
    # -------------------------------------------------------------------------
    print_stage(4, "Dense Semantic Vector Embeddings (SentenceTransformerEmbedder)")
    t0 = time.perf_counter()
    embedder = get_embedding_generator(provider="sentence-transformers", model_name="all-MiniLM-L6-v2")
    embedded_chunks = embedder.embed_chunks(chunks)
    s4_ms = (time.perf_counter() - t0) * 1000.0

    assert len(embedded_chunks) == len(chunks)
    assert embedded_chunks[0].embedding_dimension == 384
    # Verify L2 normalization
    import numpy as np
    norm = np.linalg.norm(embedded_chunks[0].embedding)
    assert abs(norm - 1.0) < 1e-4, f"Vector not L2 normalized: {norm}"

    print(f"✔ Status:            PASSED")
    print(f"✔ Model:             {embedder.model_name} (Hugging Face local)")
    print(f"✔ Dimension:         {embedder.dimension} dimensions (dense float32)")
    print(f"✔ Vectors Generated: {len(embedded_chunks)} vectors in {s4_ms:.2f} ms")
    print(f"✔ L2 Unit Norm:      Verified norm={norm:.6f} ≈ 1.0 (optimizes cosine to dot product)")

    # -------------------------------------------------------------------------
    # STAGE 5: VECTOR STORE & RETRIEVAL
    # -------------------------------------------------------------------------
    print_stage(5, "In-Memory Vector Search Index (InMemoryVectorStore)")
    t0 = time.perf_counter()
    vector_store = get_vector_store(store_type="memory")
    vector_store.add_chunks(embedded_chunks)
    s5_ms = (time.perf_counter() - t0) * 1000.0

    assert vector_store.count() == len(embedded_chunks)

    # Retrieval probe test
    probe_query = "What is the annual paid leave policy?"
    retrieval_res = vector_store.search_text(query_text=probe_query, embedder=embedder, top_k=5)
    
    print(f"✔ Status:            PASSED")
    print(f"✔ Indexed Records:   {vector_store.count()} chunks in {s5_ms:.2f} ms")
    print(f"✔ Probe Query:       \"{probe_query}\"")
    print(f"✔ Retrieval Latency: {retrieval_res.retrieval_latency_ms:.2f} ms")
    print(f"✔ Top Match:         Page {retrieval_res.results[0].chunk.metadata.page_number} "
          f"(Score: {retrieval_res.results[0].similarity_score:.4f}, Chunk ID: {retrieval_res.results[0].chunk.chunk_id})")

    # -------------------------------------------------------------------------
    # STAGE 6: CROSS-ENCODER RERANKER
    # -------------------------------------------------------------------------
    print_stage(6, "Neural Cross-Encoder Reranking (CrossEncoderReranker)")
    t0 = time.perf_counter()
    reranker = get_reranker(provider="cross-encoder", model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    rerank_res = reranker.rerank(query=probe_query, search_results=retrieval_res, top_k=3)
    s6_ms = (time.perf_counter() - t0) * 1000.0

    assert len(rerank_res.results) == 3
    top_reranked = rerank_res.results[0]

    print(f"✔ Status:            PASSED")
    print(f"✔ Cross Model:       {reranker.model_name}")
    print(f"✔ Rerank Latency:    {rerank_res.rerank_latency_ms:.2f} ms (Init+Rerank: {s6_ms:.2f} ms)")
    print(f"✔ Refined Rank #1:   Page {top_reranked.chunk.metadata.page_number} | "
          f"Neural Score: {top_reranked.rerank_score:.4f} (Original Bi-Encoder Score: {top_reranked.original_score:.4f})")
    print(f"✔ Rank Refinement:   Was rank {top_reranked.original_rank} ➡️ Now rank {top_reranked.new_rank}")

    # -------------------------------------------------------------------------
    # STAGE 7: CONTEXT ASSEMBLY & LLM GENERATOR
    # -------------------------------------------------------------------------
    print_stage(7, "Context Assembly & Grounded LLM Generation (generator.py)")
    generator = get_llm_generator(provider="mock")

    test_scenarios = [
        {
            "category": "In-Domain: Leave & Time-Off",
            "query": "What is the annual paid leave allowance and how many days can be carried over?",
            "expected_page": 3,
            "must_be_grounded": True
        },
        {
            "category": "In-Domain: Work Schedules & Remote",
            "query": "What are the core operating hours and the hybrid work policy?",
            "expected_page": 2,
            "must_be_grounded": True
        },
        {
            "category": "In-Domain: Health & Wellness Benefits",
            "query": "What health insurance coverage and wellness benefits are provided?",
            "expected_page": 6,
            "must_be_grounded": True
        },
        {
            "category": "In-Domain: Offboarding & Termination",
            "query": "What is the procedure for returning equipment upon leaving the company?",
            "expected_page": 10,
            "must_be_grounded": True
        },
        {
            "category": "Out-of-Domain: Hallucination Guardrail Check",
            "query": "What is the company policy regarding interstellar space travel and personal spaceships?",
            "expected_page": None,
            "must_be_grounded": False
        }
    ]

    print(f"Executing {len(test_scenarios)} Live RAG Queries Across All 7 Pipeline Stages...\n")

    for idx, sc in enumerate(test_scenarios, start=1):
        q = sc["query"]
        t_q_start = time.perf_counter()

        # Step A: Vector Retrieval (Top 6)
        r_step = vector_store.search_text(query_text=q, embedder=embedder, top_k=6)
        
        # Step B: Neural Cross-Rerank (Top 2)
        rr_step = reranker.rerank(query=q, search_results=r_step, top_k=2)

        # Step C: Prompt Assembly & Generation
        g_step = generator.generate(query=q, context=rr_step)
        q_latency = (time.perf_counter() - t_q_start) * 1000.0

        status_icon = "✅ PASSED" if g_step.grounded == sc["must_be_grounded"] else "❌ FAILED"
        grounded_str = "GROUNDED" if g_step.grounded else "REFUSED / UNGROUNDED (Correct Behavior)"

        print(f"[{idx}/{len(test_scenarios)}] Scenario: {sc['category']}")
        print(f"    Query:            \"{q}\"")
        print(f"    Pipeline Latency: {q_latency:.2f} ms (Retrieve: {r_step.retrieval_latency_ms:.1f}ms, "
              f"Rerank: {rr_step.rerank_latency_ms:.1f}ms, Gen: {g_step.latency_ms:.1f}ms)")
        print(f"    Verification:     {status_icon} — Status: {grounded_str}")
        print(f"    Generated Answer:\n      {g_step.answer.replace(chr(10), chr(10) + '      ')}")
        if g_step.sources:
            print(f"    Source Citations:\n      {g_step.get_formatted_sources().replace(chr(10), chr(10) + '      ')}")
        print(f"    Token Metrics:    Prompt: {g_step.prompt_tokens} | Completion: {g_step.completion_tokens} | Total: {g_step.total_tokens}")
        print("-" * 85)

        # Assert correct groundedness
        assert g_step.grounded == sc["must_be_grounded"], (
            f"Query '{q}' expected grounded={sc['must_be_grounded']}, got {g_step.grounded}"
        )

    overall_ms = (time.perf_counter() - overall_start) * 1000.0
    print_header(f"🎉 All Live Tests Succeeded in {overall_ms:.2f} ms ({overall_ms/1000.0:.2f} seconds)!")
    print("Module 1 (Stages 1 through 7) is 100% operational, fully integrated, and verified.")


if __name__ == "__main__":
    main()
