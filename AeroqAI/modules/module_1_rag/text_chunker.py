"""
Module 1 — Stage 3: Text Chunker

Transforms CleanedDocument instances into discrete, structured TextChunk instances.
Supports Recursive Character Chunking and Fixed-size Chunking with configurable
chunk size, token overlap, and boundary preservation.
"""

import math
from typing import List, Optional, Sequence
from AeroqAI.models.document import CleanedDocument
from AeroqAI.models.chunk import TextChunk, ChunkMetadata


class TextChunkerError(Exception):
    """Custom exception raised when text chunking fails."""
    pass


class TextChunker:
    """
    Production-grade Text Chunking Engine for AeroqAI RAG Pipeline.
    
    Prepares normalized document text for Vector Embedding (Stage 4) and 
    provides parameter hooks for RAG Optimization (Module 3).
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        strategy: str = "recursive",
        separators: Optional[Sequence[str]] = None,
        chars_per_token: float = 4.0
    ):
        """
        Initialize TextChunker.

        Args:
            chunk_size: Maximum character length of each chunk.
            chunk_overlap: Overlapping character count between consecutive chunks.
            strategy: Chunking strategy ('recursive' or 'fixed').
            separators: Hierarchical separator list for recursive splitting.
            chars_per_token: Average character count per token for heuristic token estimation.
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        if chunk_overlap < 0:
            raise ValueError(f"chunk_overlap must be non-negative, got {chunk_overlap}")
        if chunk_overlap >= chunk_size:
            raise ValueError(
                f"chunk_overlap ({chunk_overlap}) must be strictly smaller than chunk_size ({chunk_size})"
            )

        strategy_clean = strategy.lower().strip()
        if strategy_clean not in ("recursive", "fixed"):
            raise ValueError(f"Unsupported strategy '{strategy}'. Expected 'recursive' or 'fixed'.")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.strategy = strategy_clean
        self.separators = list(separators) if separators is not None else self.DEFAULT_SEPARATORS
        self.chars_per_token = chars_per_token

    def estimate_tokens(self, text: str) -> int:
        """Estimates token count based on character heuristics."""
        if not text:
            return 0
        return max(1, math.ceil(len(text) / self.chars_per_token))

    def _split_text_recursively(self, text: str, separators: List[str]) -> List[str]:
        """
        Recursively splits text using the first matching separator in the list.
        """
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        final_chunks: List[str] = []
        separator = ""
        new_separators: List[str] = []

        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1:]
                break

        splits = text.split(separator) if separator != "" else list(text)

        current_doc: List[str] = []
        total_len = 0

        for piece in splits:
            if not piece:
                continue
            piece_len = len(piece)

            if piece_len > self.chunk_size:
                # Sub-piece exceeds chunk size: flush current buffer, then recurse
                if current_doc:
                    merged = separator.join(current_doc).strip()
                    if merged:
                        final_chunks.append(merged)
                    current_doc = []
                    total_len = 0

                if new_separators:
                    final_chunks.extend(self._split_text_recursively(piece, new_separators))
                else:
                    final_chunks.extend(self._fixed_slice(piece))
                continue

            sep_len = len(separator) if current_doc else 0
            if total_len + sep_len + piece_len > self.chunk_size:
                if current_doc:
                    merged = separator.join(current_doc).strip()
                    if merged:
                        final_chunks.append(merged)

                    # Compute overlap buffer
                    while current_doc and total_len > self.chunk_overlap:
                        removed = current_doc.pop(0)
                        total_len -= len(removed) + (len(separator) if current_doc else 0)

                current_doc.append(piece)
                total_len += piece_len + (len(separator) if len(current_doc) > 1 else 0)
            else:
                current_doc.append(piece)
                total_len += piece_len + (len(separator) if len(current_doc) > 1 else 0)

        if current_doc:
            merged = separator.join(current_doc).strip()
            if merged and (not final_chunks or final_chunks[-1] != merged):
                final_chunks.append(merged)

        return final_chunks

    def _fixed_slice(self, text: str) -> List[str]:
        """Slices long text using sliding window of chunk_size and chunk_overlap."""
        if not text:
            return []
        chunks = []
        step = max(1, self.chunk_size - self.chunk_overlap)
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            start += step
        return chunks

    def chunk_document(self, document: CleanedDocument) -> List[TextChunk]:
        """
        Splits a CleanedDocument into a list of structured TextChunk objects.

        Args:
            document: CleanedDocument instance from Stage 2.

        Returns:
            List[TextChunk]: List of generated text chunks with rich metadata.
        """
        text = document.content.strip()
        if not text:
            return []

        # 1. Apply chosen chunking strategy
        if self.strategy == "fixed":
            raw_chunk_texts = self._fixed_slice(text)
        else:
            raw_chunk_texts = self._split_text_recursively(text, self.separators)

        # Filter out empty or whitespace-only chunks
        raw_chunk_texts = [c.strip() for c in raw_chunk_texts if c.strip()]
        total_count = len(raw_chunk_texts)

        # 2. Package into structured TextChunk models
        chunks: List[TextChunk] = []
        current_search_pos = 0

        for idx, chunk_text in enumerate(raw_chunk_texts):
            # Locate character offset in original cleaned content
            char_start = text.find(chunk_text[:min(30, len(chunk_text))], current_search_pos)
            if char_start == -1:
                char_start = current_search_pos
            char_end = char_start + len(chunk_text)
            current_search_pos = max(char_start, current_search_pos)

            chunk_id = f"chunk_{document.doc_id}_{idx}"
            word_count = len(chunk_text.split())
            token_count = self.estimate_tokens(chunk_text)

            meta = ChunkMetadata(
                source_file=document.metadata.source_file,
                doc_id=document.doc_id,
                page_number=document.metadata.page_number,
                chunk_index=idx,
                total_chunks=total_count,
                char_count=len(chunk_text),
                word_count=word_count,
                token_count=token_count,
                start_char_idx=char_start,
                end_char_idx=char_end,
                chunk_strategy=self.strategy,
                extra={
                    "parent_char_count": len(text),
                    "chunk_size_config": self.chunk_size,
                    "chunk_overlap_config": self.chunk_overlap
                }
            )

            chunks.append(TextChunk(chunk_id=chunk_id, content=chunk_text, metadata=meta))

        return chunks

    def chunk_documents(self, documents: List[CleanedDocument]) -> List[TextChunk]:
        """
        Splits multiple CleanedDocuments into a flat list of TextChunks.
        """
        all_chunks: List[TextChunk] = []
        for doc in documents:
            all_chunks.extend(self.chunk_document(doc))
        return all_chunks
