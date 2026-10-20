"""
Retrieval and Search Result Data Models.

Defines the structured contracts for vector similarity search, query parameters,
and retrieval outputs across Stage 5 (Vector Store), Stage 6 (Reranker),
and Module 6 (Interactive RAG Debugger).
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from AeroqAI.models.chunk import EmbeddedChunk


class SearchResult(BaseModel):
    """Represents a single chunk matched during similarity search."""
    chunk: EmbeddedChunk = Field(..., description="The matched embedded text chunk")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    rank: int = Field(..., description="1-based position in retrieval ranking")

    def __repr__(self) -> str:
        return (
            f"<SearchResult rank={self.rank} score={self.similarity_score:.4f} "
            f"chunk_id='{self.chunk.chunk_id}' page={self.chunk.metadata.page_number}>"
        )


class RetrievalResult(BaseModel):
    """
    Complete bundle of retrieval execution results for a query.
    
    Feeds directly into:
      - Stage 6: Reranker
      - Stage 7: Context Assembly & LLM Generation
      - Module 2: Evaluation Engine (Context Precision & Relevance)
      - Module 6: Interactive RAG Debugger
    """
    query: str = Field(..., description="The raw user query string")
    results: List[SearchResult] = Field(default_factory=list, description="Ranked list of search results")
    top_k: int = Field(..., description="Configured Top-K requested")
    total_retrieved: int = Field(default=0, description="Number of results matching criteria")
    retrieval_latency_ms: float = Field(default=0.0, description="Execution time of search in milliseconds")
    embedding_model: str = Field(..., description="Model identifier used to encode the query vector")

    def get_context_text(self, separator: str = "\n\n---\n\n") -> str:
        """Helper to assemble all retrieved chunk contents into a single LLM context string."""
        return separator.join(r.chunk.content for r in self.results)
