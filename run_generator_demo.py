"""
Interactive Demonstration of Module 1: Complete End-to-End RAG Pipeline.
Stages 1 through 7:
  1. PDF Document Loading (pypdf)
  2. Text Cleaning & Normalization (TextCleaner)
  3. Text Chunking (TextChunker)
  4. Dense Vector Embedding (SentenceTransformerEmbedder)
  5. Vector Indexing & Top-K Retrieval (InMemoryVectorStore)
  6. Neural Cross-Encoder Reranking (CrossEncoderReranker)
  7. Context Assembly & LLM Answer Generation (generator.py)
"""
import sys
import time
from pathlib import Path

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store
from AeroqAI.modules.module_1_rag.reranker import get_reranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"Error: Sample PDF not found at {pdf_path}")
        sys.exit(1)

    print("=" * 80)
    print(" AeroqAI — Module 1 End-to-End RAG Pipeline Demonstration")
    print("=" * 80)
    print(f"📄 Source PDF: {pdf_path}")

    # Stage 1: Load
    print("\n--- [Stage 1] Loading Document ---")
    loader = PDFDocumentLoader(extract_empty_pages=False)
    raw_pages = loader.load_file(pdf_path)
    print(f"Loaded {len(raw_pages)} pages.")

    # Stage 2: Clean
    print("\n--- [Stage 2] Cleaning & Normalizing ---")
    cleaner = TextCleaner()
    cleaned_pages = cleaner.clean_documents(raw_pages)
    print(f"Cleaned {len(cleaned_pages)} pages.")

    # Stage 3: Chunk
    print("\n--- [Stage 3] Chunking Text ---")
    chunker = TextChunker(chunk_size=500, chunk_overlap=50, strategy="recursive")
    chunks = chunker.chunk_documents(cleaned_pages)
    print(f"Created {len(chunks)} chunks (recursive strategy).")

    # Stage 4: Embed
    print("\n--- [Stage 4] Generating Vector Embeddings ---")
    t0 = time.perf_counter()
    embedder = get_embedding_generator(provider="sentence-transformers", model_name="all-MiniLM-L6-v2")
    embedded_chunks = embedder.embed_chunks(chunks)
    embed_ms = (time.perf_counter() - t0) * 1000.0
    print(f"Generated {len(embedded_chunks)} dense vectors in {embed_ms:.2f} ms ({embedder.dimension} dim).")

    # Stage 5: Index in Vector Store
    print("\n--- [Stage 5] Indexing Chunks in Vector Store ---")
    vector_store = get_vector_store(store_type="memory")
    vector_store.add_chunks(embedded_chunks)
    print(f"Indexed {vector_store.count()} chunks in InMemoryVectorStore.")

    # Stage 6: Initialize Reranker
    print("\n--- [Stage 6] Initializing Cross-Encoder Reranker ---")
    reranker = get_reranker(reranker_type="cross-encoder", model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")
    print(f"Loaded Cross-Encoder: {reranker.model_name}")

    # Stage 7: Initialize Generator
    print("\n--- [Stage 7] Initializing Context Assembly & LLM Generator ---")
    generator = get_llm_generator(provider="mock")
    print(f"Generator model: {generator.model_name} (Provider: {generator.provider})")

    # Benchmark test queries
    benchmark_queries = [
        "What are the rules and allowances for annual paid leave and carry-over?",
        "What are the core working hours and remote hybrid schedule?",
        "What is the company policy for spaceships and warp speed travel?"
    ]

    print("\n" + "=" * 80)
    print(" Running End-to-End RAG Queries (Retrieve ➡️ Rerank ➡️ Generate)")
    print("=" * 80)

    for i, query in enumerate(benchmark_queries, start=1):
        print(f"\n🔍 Query #{i}: \"{query}\"")
        
        # 1. Retrieve (Top 6 candidates)
        t_start = time.perf_counter()
        retrieval_res = vector_store.search_text(
            query_text=query,
            embedder=embedder,
            top_k=6
        )

        # 2. Rerank (Top 2 candidates)
        rerank_res = reranker.rerank(
            query=query,
            search_results=retrieval_res,
            top_k=2
        )

        # 3. Assemble Context & Generate
        gen_res = generator.generate(
            query=query,
            context=rerank_res
        )
        total_time_ms = (time.perf_counter() - t_start) * 1000.0

        print(f"   ⏱️ Total Pipeline Latency: {total_time_ms:.2f} ms "
              f"(Retrieval: {retrieval_res.retrieval_latency_ms:.1f}ms, "
              f"Reranking: {rerank_res.rerank_latency_ms:.1f}ms, "
              f"Generation: {gen_res.latency_ms:.1f}ms)")
        print(f"   🏷️ Grounded Answer Status: {'✅ GROUNDED' if gen_res.grounded else '❌ UNGROUNDED / REFUSED'}")
        print(f"   📝 Answer:\n      {gen_res.answer.replace(chr(10), chr(10) + '      ')}")
        print(f"   📚 Sources Cited:\n      {gen_res.get_formatted_sources().replace(chr(10), chr(10) + '      ')}")
        print(f"   🔢 Token Usage: Prompt: {gen_res.prompt_tokens} | Completion: {gen_res.completion_tokens} | Total: {gen_res.total_tokens}")
        print("-" * 80)

    print("\n🎉 Module 1 (Stages 1 through 7) verification complete!")


if __name__ == "__main__":
    main()
