"""
AeroqAI — Module 1 — Stage 6: Cross-Encoder Reranker Demo Script

Executes the complete pipeline:
  Stage 1: Document Loader (PDF -> RawDocuments)
  Stage 2: Text Cleaner (RawDocuments -> CleanedDocuments)
  Stage 3: Text Chunker (CleanedDocuments -> TextChunks)
  Stage 4: Embedding Generator (TextChunks -> EmbeddedChunks)
  Stage 5: Vector Store (EmbeddedChunks -> Bi-Encoder Top-K Search)
  Stage 6: Cross-Encoder Reranker (Candidate SearchResults -> Deep Reranking)

Demonstrates:
  - Deep cross-attention relevance scoring of (query, candidate) pairs
  - Side-by-side comparison of Bi-Encoder vs. Cross-Encoder ranking
  - Position promotion/demotion analysis
  - Assembled context string ready for LLM generation (Stage 7)
"""

import sys
import json
from pathlib import Path

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import (
    SentenceTransformerEmbedder,
    DeterministicMockEmbedder
)
from AeroqAI.modules.module_1_rag.vector_store import InMemoryVectorStore
from AeroqAI.modules.module_1_rag.reranker import (
    CrossEncoderReranker,
    DeterministicMockReranker
)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" AEROQAI -- MODULE 1 -- STAGE 6: CROSS-ENCODER RERANKER DEMO")
    print("=" * 80)

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at '{pdf_path}'. Please run scripts/generate_sample_pdf.py first.")
        sys.exit(1)

    # 1. Stages 1 to 5: Candidate Retrieval
    print("\n⚡ [Stages 1 - 5] Ingesting Document & Generating Candidate Chunks...")
    loader = PDFDocumentLoader()
    raw_docs = loader.load_file(pdf_path)
    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_docs)
    chunker = TextChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_documents(cleaned_docs)

    try:
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
    except Exception:
        embedder = DeterministicMockEmbedder(dimension=384)

    embedded_chunks = embedder.embed_chunks(chunks)
    store = InMemoryVectorStore()
    store.add_chunks(embedded_chunks)

    # 2. Query Candidate Retrieval
    target_query = "What is the parental leave allowance for primary and secondary caregivers?"
    top_candidates = 6

    print(f"\n🔍 Query: \"{target_query}\"")
    print(f"   Executing Stage 5 initial Bi-Encoder search (Top-{top_candidates} candidates)...")
    initial_retrieval = store.search_text(query_text=target_query, embedder=embedder, top_k=top_candidates)

    print("\n" + "-" * 80)
    print(" 📋 STAGE 5: INITIAL BI-ENCODER CANDIDATE RANKING")
    print("-" * 80)
    for res in initial_retrieval.results:
        preview = res.chunk.content.replace('\n', ' ')[:90]
        print(f"  Rank #{res.rank} | Sim: {res.similarity_score * 100:5.2f}% | ID: {res.chunk.chunk_id:<24} | \"{preview}...\"")

    # 3. Stage 6: Cross-Encoder Reranking
    print("\n" + "=" * 80)
    print(" 🎯 STAGE 6: APPLYING DEEP CROSS-ENCODER RE-RANKING")
    print("=" * 80)

    try:
        print("   Loading CrossEncoder model 'cross-encoder/ms-marco-MiniLM-L-6-v2'...")
        reranker = CrossEncoderReranker(model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
        print(f"   ✅ Active Reranker: {reranker.model_name}")
    except Exception as e:
        print(f"   ⚠️ CrossEncoder offline ({e}). Falling back to DeterministicMockReranker.")
        reranker = DeterministicMockReranker()

    rerank_result = reranker.rerank(
        query=target_query,
        search_results=initial_retrieval.results,
        top_k=3
    )

    print(f"\n   Rerank Latency: {rerank_result.rerank_latency_ms:.2f} ms | Evaluated: {len(initial_retrieval.results)} candidates -> Top-{rerank_result.top_k} selected")

    print("\n" + "-" * 80)
    print(" 🏆 BEFORE VS AFTER RERANKING COMPARISON TABLE")
    print("-" * 80)
    print(f" {'New Rank':<9} | {'Orig Rank':<9} | {'Rerank Score':<12} | {'Bi-Encoder':<10} | {'Shift':<7} | Chunk ID")
    print("-" * 80)

    for res in rerank_result.results:
        shift_diff = res.original_rank - res.new_rank
        if shift_diff > 0:
            shift_str = f"▲ +{shift_diff}"
        elif shift_diff < 0:
            shift_str = f"▼ {shift_diff}"
        else:
            shift_str = "  --"

        print(
            f"  #{res.new_rank:<7} | #{res.original_rank:<7} | "
            f"{res.rerank_score:<12.4f} | {res.original_score * 100:5.2f}%    | "
            f"{shift_str:<7} | {res.chunk.chunk_id}"
        )

    print("\n" + "-" * 80)
    print(" 📄 FINAL RERANKED CONTEXT (Top Match Preview)")
    print("-" * 80)
    best_match = rerank_result.results[0]
    print(f"Top Pick: {best_match.chunk.chunk_id} (Page {best_match.chunk.metadata.page_number})")
    print(f"Content: \"{best_match.chunk.content}\"")

    print("\n" + "=" * 80)
    print(" 📦 STRUCTURED Pydantic RERANK RESULT SCHEMA (JSON Format Example)")
    print("=" * 80)
    sample_dict = rerank_result.model_dump()
    for item in sample_dict["results"]:
        item["chunk"]["embedding"] = f"[Vector with {len(item['chunk']['embedding'])} floats omitted]"
    print(json.dumps(sample_dict, indent=2))

    print("\n" + "=" * 80)
    print(" 🎉 STAGE 6 (CROSS-ENCODER RERANKER) VERIFICATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
