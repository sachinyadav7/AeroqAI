"""
AeroqAI — Module 1 — Stage 1: Document Loader Demo Script

Executes PDF Document Loader against sample HR Policy PDF, displays page metadata,
content previews, and validates structured output.
"""

import sys
import json
from pathlib import Path
from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader, DocumentLoaderError


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" AEROQAI -- MODULE 1 -- STAGE 1: DOCUMENT LOADER DEMO")
    print("=" * 80)

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at '{pdf_path}'.")
        sys.exit(1)

    print(f"\n📂 Ingesting Target PDF File: {pdf_path.resolve()}")
    
    loader = PDFDocumentLoader(extract_empty_pages=False)
    
    try:
        documents = loader.load_file(pdf_path)
    except DocumentLoaderError as err:
        print(f"❌ Document Loader Error: {err}")
        sys.exit(1)

    print(f"\n✅ Successfully Loaded Document!")
    print(f" Total Pages Extracted: {len(documents)}")
    print(f" Source File: {documents[0].metadata.source_file}")
    print(f" Total File Size: {documents[0].metadata.file_size_bytes:,} bytes")

    print("\n" + "-" * 80)
    print(" 📋 PAGE-BY-PAGE EXTRACTED METADATA BREAKDOWN")
    print("-" * 80)
    
    total_chars = 0
    total_words = 0

    for doc in documents:
        meta = doc.metadata
        total_chars += meta.char_count
        total_words += meta.word_count
        print(
            f"  📄 Doc ID: {doc.doc_id:<22} | Page: {meta.page_number:02d}/{meta.total_pages:02d} | "
            f"Chars: {meta.char_count:4d} | Words: {meta.word_count:3d}"
        )

    print("-" * 80)
    print(f" 📊 Aggregate Summary: {total_chars:,} Characters | {total_words:,} Words across {len(documents)} pages.")
    print("-" * 80)

    print("\n" + "=" * 80)
    print(" 🔍 PAGE CONTENT PREVIEWS (First 3 Pages)")
    print("=" * 80)

    for doc in documents[:3]:
        meta = doc.metadata
        print(f"\n--- [Page {meta.page_number} / {meta.total_pages}] ---")
        preview = doc.content[:250].replace('\n', ' ')
        print(f"Snippet: \"{preview}...\"")

    print("\n" + "=" * 80)
    print(" 📦 STRUCTURED Pydantic RAW DOCUMENT SCHEMA (JSON Format Example)")
    print("=" * 80)
    sample_json = json.dumps(documents[0].model_dump(), indent=2)
    print(sample_json)

    print("\n" + "=" * 80)
    print(" 🎉 STAGE 1 (DOCUMENT LOADING) VERIFICATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
