"""
Text Chunk and Chunk Metadata Data Models.

Represents discrete text chunks created from CleanedDocument instances.
Forms the contract for Stage 4 (Embedding Generation) and Stage 5 (Vector Indexing).
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata attributes associated with an individual text chunk."""
    source_file: str = Field(..., description="Name or path of the source document")
    doc_id: str = Field(..., description="ID of parent CleanedDocument / RawDocument")
    page_number: int = Field(default=1, description="1-based page number of source document")
    chunk_index: int = Field(default=0, description="0-based sequential index of this chunk")
    total_chunks: int = Field(default=1, description="Total chunks generated for this parent page/document")
    char_count: int = Field(default=0, description="Character count in chunk content")
    word_count: int = Field(default=0, description="Word count in chunk content")
    token_count: int = Field(default=0, description="Estimated token count (approx. 4 chars/token or tokenizer)")
    start_char_idx: int = Field(default=0, description="Start character offset in parent content")
    end_char_idx: int = Field(default=0, description="End character offset in parent content")
    chunk_strategy: str = Field(default="recursive", description="Strategy used: 'recursive' or 'fixed'")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC Timestamp when chunk was generated"
    )
    extra: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary custom metadata fields")


class TextChunk(BaseModel):
    """
    Structured representation of a single text chunk.
    
    This forms the exact input contract for:
      - Stage 4: Embedding Generation
      - Stage 5: Vector Store & Retrieval
      - Stage 6: Reranker
    """
    chunk_id: str = Field(..., description="Unique chunk identifier (e.g., chunk_doc_hr_policy_p1_0)")
    content: str = Field(..., description="Text content payload of this chunk")
    metadata: ChunkMetadata = Field(..., description="Structured metadata container")

    def __repr__(self) -> str:
        return (
            f"<TextChunk id='{self.chunk_id}' parent='{self.metadata.doc_id}' "
            f"page={self.metadata.page_number} idx={self.metadata.chunk_index} "
            f"chars={self.metadata.char_count} tokens={self.metadata.token_count}>"
        )
