"""
Unit tests for Module 1 — Stage 2: Text Cleaner & Normalizer.
"""

from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.models.document import RawDocument, CleanedDocument, DocumentMetadata


def test_remove_control_characters():
    cleaner = TextCleaner()
    raw = "Hello\x00 World!\x0c This is \u200ba test.\x07"
    cleaned, stats = cleaner.clean_text(raw)
    
    assert cleaned == "Hello World! This is a test."
    assert stats["control_chars_removed"] > 0



def test_fix_line_wrap_hyphenation():
    cleaner = TextCleaner()
    raw = "This is a hand-\nbook for inter-\n national policy."
    cleaned, stats = cleaner.clean_text(raw)
    
    assert "handbook" in cleaned
    assert "international" in cleaned
    assert stats["hyphenated_wraps_fixed"] == 2


def test_normalize_unicode_quotes_and_dashes():
    cleaner = TextCleaner()
    raw = "“Welcome”—said the manager—‘it’s’ a non-breaking\xa0space test."
    cleaned, _ = cleaner.clean_text(raw)
    
    assert '"Welcome"' in cleaned
    assert "-said the manager-" in cleaned
    assert "'it's'" in cleaned
    assert "\xa0" not in cleaned


def test_collapse_excessive_whitespace():
    cleaner = TextCleaner()
    raw = "Header   Line   with    spaces.\n\n\n\n\nFooter section."
    cleaned, _ = cleaner.clean_text(raw)
    
    assert "Header Line with spaces." in cleaned
    assert "\n\n\n" not in cleaned
    assert "Header Line with spaces.\n\nFooter section." in cleaned


def test_clean_document_end_to_end():
    cleaner = TextCleaner()
    raw_meta = DocumentMetadata(
        source_file="test.pdf",
        page_number=1,
        total_pages=1,
        char_count=50,
        word_count=8
    )
    raw_doc = RawDocument(
        doc_id="doc_test_p1",
        content="Raw  “Text”   with\x00 control   chars.\n\n\n",
        metadata=raw_meta
    )
    
    cleaned_doc = cleaner.clean_document(raw_doc)
    
    assert isinstance(cleaned_doc, CleanedDocument)
    assert cleaned_doc.doc_id == "doc_test_p1"
    assert '"Text"' in cleaned_doc.content
    assert "\x00" not in cleaned_doc.content
    assert cleaned_doc.metadata.char_count == len(cleaned_doc.content)
    assert cleaned_doc.cleaning_stats["char_reduction"] > 0
