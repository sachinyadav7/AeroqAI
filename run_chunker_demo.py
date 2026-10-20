"""
AeroqAI — Module 1 — Stage 3: Text Chunker Demo Script

Executes the complete pipeline:
  Stage 1: Document Loader (PDF -> RawDocuments)
  Stage 2: Text Cleaner (RawDocuments -> CleanedDocuments)
  Stage 3: Text Chunker (CleanedDocuments -> TextChunks)

Displays page-by-page chunk breakdowns, chunk metrics, content previews,
and outputs structured JSON schemas.
"""

import sys
import json
from pathlib import Path

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" AEROQAI -- MODULE 1 -- STAGE 3: TEXT CHUNKER DEMO")
    print("=" * 80)

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at '{pdf_path}'. Please run scripts/generate_sample_pdf.py first.")
        sys.exit(1)

    # 1. Ingest
    print(f"\n📂 Step 1: Ingesting Raw Documents via PDFDocumentLoader...")
    loader = PDFDocumentLoader()
    raw_docs = loader.load_file(pdf_path)
    print(f"   Loaded {len(raw_docs)} RawDocument pages.")

    # 2. Clean
    print(f"\n🧹 Step 2: Normalizing Text via TextCleaner...")
    cleaner = TextCleaner()
    cleaned_docs = cleaner.clean_documents(raw_docs)
    print(f"   Cleaned {len(cleaned_docs)} CleanedDocument pages.")

    # 3. Chunk
    chunk_size = 400
    chunk_overlap = 50
    strategy = "recursive"

    print(f"\n✂️ Step 3: Generating Chunks via TextChunker...")
    print(f"   Settings: Strategy='{strategy}' | ChunkSize={chunk_size} chars | Overlap={chunk_overlap} chars")
    
    chunker = TextChunker(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        strategy=strategy
    )
    all_chunks = chunker.chunk_documents(cleaned_docs)

    print(f"   Generated a total of {len(all_chunks)} TextChunk instances across {len(cleaned_docs)} pages.")

    print("\n" + "-" * 80)
    print(" 📋 CHUNK DISTRIBUTION PER PAGE")
    print("-" * 80)

    page_counts = {}
    for c in all_chunks:
        pg = c.metadata.page_number
        page_counts[pg] = page_counts.get(pg, 0) + 1

    total_tokens = sum(c.metadata.token_count for c in all_chunks)
    total_chars = sum(c.metadata.char_count for c in all_chunks)

    for pg in sorted(page_counts.keys()):
        count = page_counts[pg]
        pg_chunks = [c for c in all_chunks if c.metadata.page_number == pg]
        avg_tokens = sum(c.metadata.token_count for c in pg_chunks) / count
        print(f"  📄 Page {pg:02d}: {count:2d} chunks | Avg Tokens/Chunk: {avg_tokens:5.1f}")

    print("-" * 80)
    print(f" 📊 Aggregate Summary: {len(all_chunks)} chunks | {total_chars:,} chars | ~{total_tokens:,} tokens")
    print("-" * 80)

    print("\n" + "=" * 80)
    print(" 🔍 FIRST 3 CHUNKS PREVIEW (from Page 1)")
    print("=" * 80)

    for chunk in all_chunks[:3]:
        meta = chunk.metadata
        print(f"\n--- [{chunk.chunk_id}] ---")
        print(f"Page: {meta.page_number} | Index: {meta.chunk_index} | Chars: {meta.char_count} | Tokens: ~{meta.token_count}")
        preview = chunk.content.replace('\n', ' ')
        print(f"Snippet: \"{preview}\"")

    print("\n" + "=" * 80)
    print(" 📦 STRUCTURED Pydantic TEXT CHUNK SCHEMA (JSON Format Example)")
    print("=" * 80)
    print(json.dumps(all_chunks[0].model_dump(), indent=2))

    print("\n" + "=" * 80)
    print(" 🎉 STAGE 3 (TEXT CHUNKING) VERIFICATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
