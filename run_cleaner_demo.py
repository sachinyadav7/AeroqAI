"""
AeroqAI — Module 1 — Stage 2: Text Cleaner Demo Script

Executes TextCleaner on loaded RawDocuments, displays before/after statistics,
and verifies clean normalization.
"""

import sys
import json
from pathlib import Path
from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" AEROQAI -- MODULE 1 -- STAGE 2: TEXT CLEANER DEMO")
    print("=" * 80)

    pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
    if not pdf_path.exists():
        print(f"❌ Error: Sample PDF not found at '{pdf_path}'. Please run Stage 1 first.")
        sys.exit(1)

    print(f"\n📂 Step 1: Ingesting Raw Documents via PDFDocumentLoader...")
    loader = PDFDocumentLoader()
    raw_docs = loader.load_file(pdf_path)
    print(f"   Loaded {len(raw_docs)} RawDocument pages.")

    print(f"\n🧹 Step 2: Applying TextCleaner Normalization Engine...")
    cleaner = TextCleaner(
        remove_control_chars=True,
        fix_hyphenation=True,
        normalize_unicode=True,
        collapse_whitespace=True
    )
    cleaned_docs = cleaner.clean_documents(raw_docs)

    print("\n" + "-" * 80)
    print(" 📋 PAGE-BY-PAGE CLEANING STATS BREAKDOWN")
    print("-" * 80)
    
    total_raw_chars = 0
    total_cleaned_chars = 0

    for c_doc in cleaned_docs:
        stats = c_doc.cleaning_stats
        total_raw_chars += stats['raw_char_count']
        total_cleaned_chars += stats['cleaned_char_count']
        print(
            f"  📄 Page {c_doc.metadata.page_number:02d} | "
            f"Raw: {stats['raw_char_count']:4d} chars -> Clean: {stats['cleaned_char_count']:4d} chars | "
            f"Reduction: {stats['char_reduction_percent']:5.2f}% | "
            f"Fixed Wraps: {stats.get('hyphenated_wraps_fixed', 0)} | "
            f"Control Chars Removed: {stats.get('control_chars_removed', 0)}"
        )

    overall_reduction = ((total_raw_chars - total_cleaned_chars) / total_raw_chars * 100.0) if total_raw_chars > 0 else 0.0

    print("-" * 80)
    print(
        f" 📊 Aggregate Summary: Raw={total_raw_chars:,} chars -> Clean={total_cleaned_chars:,} chars | "
        f"Overall Reduction={overall_reduction:.2f}%"
    )
    print("-" * 80)

    print("\n" + "=" * 80)
    print(" 🔍 BEFORE VS AFTER CLEANING PREVIEW (Page 1)")
    print("=" * 80)
    
    p1_raw = raw_docs[0].content
    p1_clean = cleaned_docs[0].content
    
    print("\n--- [ORIGINAL RAW TEXT] ---")
    print(p1_raw[:300] + "...")
    print("\n--- [CLEANED & NORMALIZED TEXT] ---")
    print(p1_clean[:300] + "...")

    print("\n" + "=" * 80)
    print(" 📦 STRUCTURED Pydantic CLEANED DOCUMENT SCHEMA (JSON Format Example)")
    print("=" * 80)
    print(json.dumps(cleaned_docs[0].model_dump(), indent=2))

    print("\n" + "=" * 80)
    print(" 🎉 STAGE 2 (TEXT CLEANING) VERIFICATION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()
