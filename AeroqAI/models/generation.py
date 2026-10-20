"""Data contracts and models for LLM Context Assembly and Generation (Stage 7)."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Metadata representing a specific chunk or document cited in an answer."""
    doc_id: str = Field(..., description="Parent document identifier")
    source_file: str = Field(..., description="Source filename or URI")
    page_number: int = Field(..., description="Source page number (1-indexed)")
    chunk_id: str = Field(..., description="Unique chunk identifier")
    relevance_score: Optional[float] = Field(None, description="Retrieval or reranking score")
    excerpt: Optional[str] = Field(None, description="Brief snippet of the cited chunk content")

    def to_citation_label(self) -> str:
        """Format as a short citation tag."""
        return f"{self.source_file}:p{self.page_number}"


class GenerationResult(BaseModel):
    """Structured response contract for LLM generation in the RAG pipeline."""
    query: str = Field(..., description="The user query or prompt submitted")
    answer: str = Field(..., description="The generated response text")
    sources: List[SourceCitation] = Field(default_factory=list, description="List of source document chunks cited")
    model_name: str = Field(..., description="Name or identifier of the generation model")
    provider: str = Field(..., description="Provider name (e.g., 'openai', 'mock', 'anthropic')")
    prompt_tokens: Optional[int] = Field(None, description="Estimated or actual input token count")
    completion_tokens: Optional[int] = Field(None, description="Estimated or actual output token count")
    total_tokens: Optional[int] = Field(None, description="Total token consumption")
    latency_ms: float = Field(0.0, description="End-to-end generation latency in milliseconds")
    prompt_template: Optional[str] = Field(None, description="Prompt template used for context assembly")
    raw_context: str = Field("", description="Assembled context text injected into the prompt")
    grounded: bool = Field(True, description="Whether the answer was successfully grounded in provided context")

    def get_formatted_sources(self) -> str:
        """Format cited sources as a human-readable markdown reference list."""
        if not self.sources:
            return "No sources cited."
        
        lines = []
        for i, src in enumerate(self.sources, start=1):
            score_str = f" (Score: {src.relevance_score:.4f})" if src.relevance_score is not None else ""
            lines.append(f"[{i}] {src.source_file} (Page {src.page_number}, Chunk: {src.chunk_id}){score_str}")
        return "\n".join(lines)
