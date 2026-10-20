"""
Raw Document and Document Metadata Data Models.

Represents documents loaded from external sources (PDF, TXT, MD)
before cleaning, chunking, or embedding.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Metadata attributes associated with a raw document or page."""
    source_file: str = Field(..., description="Name or path of the source file")
    file_type: str = Field(default="pdf", description="File extension / type (pdf, txt, md)")
    page_number: int = Field(default=1, description="1-based page number")
    total_pages: int = Field(default=1, description="Total pages in source document")
    char_count: int = Field(default=0, description="Total characters in extracted text")
    word_count: int = Field(default=0, description="Total words in extracted text")
    file_size_bytes: Optional[int] = Field(default=None, description="Size of source file in bytes")
    loaded_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="UTC Timestamp when document was ingested"
    )
    extra: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary custom metadata fields")


class RawDocument(BaseModel):
    """
    Structured representation of a single loaded document/page.
    
    This forms the exact input contract for Stage 2 (Text Cleaning).
    """
    doc_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Raw extracted text content")
    metadata: DocumentMetadata = Field(..., description="Structured metadata container")

    def __repr__(self) -> str:
        return (
            f"<RawDocument id='{self.doc_id}' source='{self.metadata.source_file}' "
            f"page={self.metadata.page_number}/{self.metadata.total_pages} "
            f"chars={self.metadata.char_count}>"
        )


class CleanedDocument(BaseModel):
    """
    Structured representation of a text-cleaned and normalized document/page.
    
    This forms the exact input contract for Stage 3 (Token Chunking).
    """
    doc_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Cleaned and normalized text content")
    raw_content: str = Field(..., description="Original raw text content before cleaning")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    cleaning_stats: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Metrics tracking character reduction, hyphen fixes, control char removal, etc."
    )

    def __repr__(self) -> str:
        return (
            f"<CleanedDocument id='{self.doc_id}' source='{self.metadata.source_file}' "
            f"page={self.metadata.page_number} chars={len(self.content)} "
            f"reduction={self.cleaning_stats.get('char_reduction_percent', 0.0):.1f}%>"
        )

