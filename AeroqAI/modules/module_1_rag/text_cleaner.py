"""
Module 1 — Stage 2: Text Cleaner & Normalizer

Transforms RawDocument instances into CleanedDocument instances by removing
non-printable control characters, fixing line-wrap hyphenation, normalizing Unicode smart quotes/dashes,
and collapsing redundant whitespace.
"""

import re
import unicodedata
from typing import List, Optional, Dict, Any
from AeroqAI.models.document import RawDocument, CleanedDocument, DocumentMetadata


class TextCleaner:
    """
    Production-grade Text Cleaning & Normalization Engine.
    
    Prepares extracted PDF text for optimal Token Chunking (Stage 3) and Vector Embedding (Stage 4).
    """

    def __init__(
        self,
        remove_control_chars: bool = True,
        fix_hyphenation: bool = True,
        normalize_unicode: bool = True,
        collapse_whitespace: bool = True,
        max_consecutive_newlines: int = 2,
        header_footer_patterns: Optional[List[str]] = None
    ):
        """
        Initialize TextCleaner with customizable cleaning rules.
        """
        self.remove_control_chars = remove_control_chars
        self.fix_hyphenation = fix_hyphenation
        self.normalize_unicode = normalize_unicode
        self.collapse_whitespace = collapse_whitespace
        self.max_consecutive_newlines = max_consecutive_newlines
        self.header_footer_patterns = header_footer_patterns or []

    def clean_text(self, text: str) -> tuple[str, Dict[str, Any]]:
        """
        Applies configured cleaning transformations to a raw string.
        
        Returns:
            tuple[str, Dict[str, Any]]: (cleaned_text, transformation_stats)
        """
        if not text:
            return "", {"raw_chars": 0, "cleaned_chars": 0, "reduction_percent": 0.0}

        original_chars = len(text)
        cleaned = text
        stats = {}

        # 1. Strip non-printable control characters
        if self.remove_control_chars:
            # Preserve \n and \t; remove all other control chars (ASCII 0-31, 127-159, zero-width chars)
            before_cc = len(cleaned)
            cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f\xad\u200b-\u200d\ufffd]', '', cleaned)
            stats["control_chars_removed"] = before_cc - len(cleaned)

        # 2. Fix line-wrap hyphenation (e.g. "hand-\nbook" or "multi-\n page")
        if self.fix_hyphenation:
            before_hyphen = len(cleaned)
            cleaned = re.sub(r'(\b\w+)-\s*\n\s*(\w+\b)', r'\1\2', cleaned)
            stats["hyphenated_wraps_fixed"] = (before_hyphen - len(cleaned)) // 2

        # 3. Normalize Unicode quotes, dashes, spaces & bullets
        if self.normalize_unicode:
            # NFKC Unicode Normalization
            cleaned = unicodedata.normalize('NFKC', cleaned)
            # Smart quotes & apostrophes
            cleaned = cleaned.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
            # Em-dash, En-dash to standard hyphen
            cleaned = cleaned.replace('—', '-').replace('–', '-')
            # Non-breaking space to standard space
            cleaned = cleaned.replace('\xa0', ' ')
            # Bullet symbols to standard hyphen
            cleaned = re.sub(r'[•▪▸►]', '-', cleaned)

        # 4. Strip specific recurring header/footer regex patterns if provided
        for pattern in self.header_footer_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

        # 5. Collapse excessive whitespace & trailing line spaces
        if self.collapse_whitespace:
            # Strip spaces at the ends of individual lines
            cleaned = re.sub(r'[ \t]+\n', '\n', cleaned)
            cleaned = re.sub(r'\n[ \t]+', '\n', cleaned)
            # Replace 3 or more spaces with a single space
            cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)
            # Limit consecutive newlines
            max_nl_pattern = r'\n{' + str(self.max_consecutive_newlines + 1) + r',}'
            max_nl_replacement = '\n' * self.max_consecutive_newlines
            cleaned = re.sub(max_nl_pattern, max_nl_replacement, cleaned)
            # Trim overall string
            cleaned = cleaned.strip()

        final_chars = len(cleaned)
        char_reduction = original_chars - final_chars
        reduction_pct = (char_reduction / original_chars * 100.0) if original_chars > 0 else 0.0

        stats["raw_char_count"] = original_chars
        stats["cleaned_char_count"] = final_chars
        stats["char_reduction"] = char_reduction
        stats["char_reduction_percent"] = round(reduction_pct, 2)
        stats["word_count"] = len(cleaned.split())

        return cleaned, stats

    def clean_document(self, raw_doc: RawDocument) -> CleanedDocument:
        """
        Cleans a single RawDocument and returns a CleanedDocument.
        """
        cleaned_text, stats = self.clean_text(raw_doc.content)

        # Update metadata word & char counts to reflect cleaned state
        updated_meta_dict = raw_doc.metadata.model_dump()
        updated_meta_dict["char_count"] = stats["cleaned_char_count"]
        updated_meta_dict["word_count"] = stats["word_count"]
        updated_metadata = DocumentMetadata(**updated_meta_dict)

        return CleanedDocument(
            doc_id=raw_doc.doc_id,
            content=cleaned_text,
            raw_content=raw_doc.content,
            metadata=updated_metadata,
            cleaning_stats=stats
        )

    def clean_documents(self, raw_docs: List[RawDocument]) -> List[CleanedDocument]:
        """
        Batch-cleans a list of RawDocument objects.
        """
        return [self.clean_document(doc) for doc in raw_docs]
