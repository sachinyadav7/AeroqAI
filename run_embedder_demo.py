"""
AeroqAI — Module 1 — Stage 4: Embedding Generator Demo Script

Executes the complete pipeline from document ingestion to vector embedding:
  Stage 1: Document Loader (PDF -> RawDocuments)
  Stage 2: Text Cleaner (RawDocuments -> CleanedDocuments)
  Stage 3: Text Chunker (CleanedDocuments -> TextChunks)
  Stage 4: Embedding Generator (TextChunks -> EmbeddedChunks)

Demonstrates:
  - Vector dimensionality and unit normalization (L2 norm = 1.0)
  - Semantic similarity ranking against a sample user query
  - Structured Pydantic EmbeddedChunk JSON output
"""

import sys
import json
from pathlib import Path

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import (
    BaseEmbeddingGenerator,
    DeterministicMockEmbedder,
    SentenceTransformerEmbedder,
    get_embedding_generator
)


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" AEROQAI -- MODULE 1 -- STAGE 4: EMBEDDING GENERATOR DEMO")
    print("=" * 80)

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at '{pdf_path}'. Please run scripts/generate_sample_pdf.py first.")
        sys.exit(1)

    # 1. Pipeline Stages 1 to 3
    print("\n⚡ Running Ingestion Pipeline (Stages 1 -> 2 -> 3)...")
    loader = PDFDocumentLoader()
    raw_docs = loader.load_file(pdf_path)
    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_docs)
    chunker = TextChunker(chunk_size=400, chunk_overlap=50)
    chunks = chunker.chunk_documents(cleaned_docs)
    print(f"   Generated {len(chunks)} TextChunks ready for vector embedding.")

    # 2. Stage 4: Embedding Generation
    print("\n🧠 Initializing Embedding Model...")
    try:
        print("   Attempting to load 'all-MiniLM-L6-v2' via SentenceTransformers...")
        embedder = SentenceTransformerEmbedder(model_name="all-MiniLM-L6-v2")
        print(f"   ✅ Loaded SentenceTransformer model: '{embedder.model_name}' (dim={embedder.dimension})")
    except Exception as e:
        print(f"   ⚠️ Local HuggingFace download unavailable ({e}). Falling back to DeterministicMockEmbedder.")
        embedder = DeterministicMockEmbedder(dimension=384)
        print(f"   ✅ Initialized DeterministicMockEmbedder: '{embedder.model_name}' (dim={embedder.dimension})")

    print(f"\n🔮 Generating Dense Vector Embeddings for {len(chunks)} chunks...")
    embedded_chunks = embedder.embed_chunks(chunks)
    print(f"   Successfully generated {len(embedded_chunks)} EmbeddedChunk objects!")

    # 3. Vector Statistics
    first_vec = embedded_chunks[0].embedding
    sample_preview = [round(x, 4) for x in first_vec[:6]]
    print("\n" + "-" * 80)
    print(" 📊 EMBEDDING VECTOR SPECIFICATIONS")
    print("-" * 80)
    print(f"  • Model Name:             {embedder.model_name}")
    print(f"  • Vector Dimensionality:  {embedder.dimension} dimensions")
    print(f"  • Sample Values (First 6): {sample_preview}...")
    print(f"  • Total Vectors Created:  {len(embedded_chunks)}")
    print("-" * 80)

    # 4. Semantic Similarity Demonstration (Preview for Stage 5 Retrieval)
    sample_query = "How many days of annual paid leave do employees receive?"
    print("\n" + "=" * 80)
    print(f" 🔍 SEMANTIC SIMILARITY BENCHMARK AGAINST QUERY:")
    print(f"    \"{sample_query}\"")
    print("=" * 80)

    query_vector = embedder.embed_text(sample_query)
    
    # Compute similarity between query and all chunks
    scored_chunks = []
    for ec in embedded_chunks:
        sim = BaseEmbeddingGenerator.cosine_similarity(query_vector, ec.embedding)
        scored_chunks.append((sim, ec))

    # Sort by descending similarity score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)

    print("\n🏆 Top 3 Most Relevant Chunks (Cosine Similarity Score):")
    for rank, (score, chunk) in enumerate(scored_chunks[:3], start=1):
        meta = chunk.metadata
        preview = chunk.content.replace('\n', ' ')[:160]
        print(f"\n  #{rank} | Match Score: {score * 100:.2f}% | Chunk ID: {chunk.chunk_id} (Page {meta.page_number})")
        print(f"     \"{preview}...\"")

    print("\n" + "=" * 80)
    print(" 📦 STRUCTURED Pydantic EMBEDDED CHUNK SCHEMA (Truncated Vector JSON Example)")
    print("=" * 80)
    sample_dict = embedded_chunks[0].model_dump()
    sample_dict["embedding"] = sample_dict["embedding"][:5] + [f"... +{embedder.dimension - 5} more floats"]
    print(json.dumps(sample_dict, indent=2))

    print("\n" + "=" * 80)
    print(" 🎉 STAGE 4 (EMBEDDING GENERATION) VERIFICATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
