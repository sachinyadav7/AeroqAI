"""
AeroqAI — Module 1 — Stage 5: Vector Store & Retrieval Demo Script

Executes the complete pipeline:
  Stage 1: Document Loader (PDF -> RawDocuments)
  Stage 2: Text Cleaner (RawDocuments -> CleanedDocuments)
  Stage 3: Text Chunker (CleanedDocuments -> TextChunks)
  Stage 4: Embedding Generator (TextChunks -> EmbeddedChunks)
  Stage 5: Vector Store (EmbeddedChunks -> Vector Index -> Top-K Retrieval)

Demonstrates:
  - Indexing and vector count verification
  - Multi-query Top-K semantic similarity retrieval with latency tracking
  - Metadata attribute filtering (e.g., scoping search to specific pages)
  - Context assembly string ready for LLM generation (Stage 7)
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


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" AEROQAI -- MODULE 1 -- STAGE 5: VECTOR STORE & RETRIEVAL DEMO")
    print("=" * 80)

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at '{pdf_path}'. Please run scripts/generate_sample_pdf.py first.")
        sys.exit(1)

    # 1. Pipeline Stages 1 -> 2 -> 3
    print("\n⚡ [Stages 1 - 3] Ingesting, Normalizing, and Chunking Document...")
    loader = PDFDocumentLoader()
    raw_docs = loader.load_file(pdf_path)
    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_docs)
    chunker = TextChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_documents(cleaned_docs)
    print(f"   Created {len(chunks)} TextChunks across {len(cleaned_docs)} pages.")

    # 2. Stage 4: Embedding Generation
    print("\n🧠 [Stage 4] Generating Dense Vector Embeddings...")
    try:
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        print(f"   Using SentenceTransformer: '{embedder.model_name}' (dim={embedder.dimension})")
    except Exception as e:
        print(f"   Falling back to DeterministicMockEmbedder ({e})")
        embedder = DeterministicMockEmbedder(dimension=384)

    embedded_chunks = embedder.embed_chunks(chunks)

    # 3. Stage 5: Vector Store Indexing
    print("\n📦 [Stage 5] Populating Vector Store Index...")
    store = InMemoryVectorStore()
    store.add_chunks(embedded_chunks)
    print(f"   ✅ Vector store populated successfully with {store.count()} indexed chunks.")

    # 4. Multi-Query Semantic Retrieval Benchmark
    test_queries = [
        "What are the rules and allowances for annual paid leave?",
        "What are the core working hours and remote hybrid schedule?",
        "What is the procedure for returning company equipment when leaving?"
    ]

    print("\n" + "=" * 80)
    print(" 🔍 RUNNING TOP-3 SEMANTIC RETRIEVAL BENCHMARKS")
    print("=" * 80)

    for i, query in enumerate(test_queries, start=1):
        print(f"\n👉 Query #{i}: \"{query}\"")
        retrieval = store.search_text(query_text=query, embedder=embedder, top_k=3)
        print(f"   Latency: {retrieval.retrieval_latency_ms:.2f} ms | Retrieved: {retrieval.total_retrieved} matches")

        for res in retrieval.results:
            meta = res.chunk.metadata
            preview = res.chunk.content.replace('\n', ' ')[:140]
            print(f"    Rank #{res.rank} [Score: {res.similarity_score * 100:5.2f}%] | Page {meta.page_number:02d} ({res.chunk.chunk_id}):")
            print(f"      \"{preview}...\"")

    # 5. Metadata Attribute Filtering Demo
    filtered_query = "What policies apply to employee leave?"
    target_page = 3
    print("\n" + "=" * 80)
    print(f" 🎯 DEMO: METADATA ATTRIBUTE FILTERING (Scoped to Page {target_page} Only)")
    print("=" * 80)
    print(f"Query: \"{filtered_query}\" | Filter: {{'page_number': {target_page}}}")
    
    filtered_retrieval = store.search_text(
        query_text=filtered_query,
        embedder=embedder,
        top_k=3,
        metadata_filter={"page_number": target_page}
    )
    print(f"Retrieved {len(filtered_retrieval.results)} matches, all strictly on Page {target_page}:")
    for res in filtered_retrieval.results:
        print(f"  • Match: {res.chunk.chunk_id} (Page {res.chunk.metadata.page_number}) | Score: {res.similarity_score * 100:.2f}%")

    # 6. Structured Schema Output
    print("\n" + "=" * 80)
    print(" 📦 STRUCTURED Pydantic RETRIEVAL RESULT SCHEMA (JSON Format Example)")
    print("=" * 80)
    sample_retrieval_dict = filtered_retrieval.model_dump()
    for item in sample_retrieval_dict["results"]:
        item["chunk"]["embedding"] = f"[Vector with {len(item['chunk']['embedding'])} floats omitted]"
    print(json.dumps(sample_retrieval_dict, indent=2))

    print("\n" + "=" * 80)
    print(" 🎉 STAGE 5 (VECTOR STORE & RETRIEVAL) VERIFICATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
