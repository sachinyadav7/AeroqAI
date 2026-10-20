"""Data contracts and schemas for Module 6: Interactive RAG Debugger."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ChunkTraceItem(BaseModel):
    """Detailed audit information for a candidate passage during retrieval and reranking."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    source_file: str = Field(..., description="Source document file name")
    page_number: int = Field(1, description="Source page number")
    content_snippet: str = Field(..., description="First 100-150 characters of chunk text")
    char_length: int = Field(0, description="Total characters in chunk")
    
    # Retrieval Phase
    initial_retrieval_score: float = Field(..., description="Vector cosine similarity score")
    initial_rank: int = Field(..., description="1-based retrieval position")
    
    # Reranking Phase
    rerank_score: Optional[float] = Field(None, description="Neural cross-encoder relevance score")
    final_rank: Optional[int] = Field(None, description="1-based position after neural reranking")
    rank_delta: Optional[int] = Field(None, description="Rank shift (positive = moved up, negative = dropped)")
    retained_in_context: bool = Field(True, description="Whether chunk was passed into LLM context window")


class RetrievalStageTrace(BaseModel):
    """Diagnostic profile of Vector Retrieval (Stage 5)."""
    top_k_requested: int = Field(..., description="Target retrieval depth")
    total_candidates_found: int = Field(..., description="Total retrieved chunks")
    retrieved_chunks: List[ChunkTraceItem] = Field(default_factory=list, description="Candidate chunks sorted by vector similarity")
    latency_ms: float = Field(..., description="Retrieval latency in milliseconds")


class RerankStageTrace(BaseModel):
    """Diagnostic profile of Neural Cross-Encoder Reranking (Stage 6)."""
    model_name: str = Field(..., description="Cross-encoder model identifier")
    top_k_retained: int = Field(..., description="Number of top candidates kept for context")
    reranked_chunks: List[ChunkTraceItem] = Field(default_factory=list, description="Chunks ordered by reranker score")
    latency_ms: float = Field(..., description="Reranker inference latency in milliseconds")


class PromptAssemblyStageTrace(BaseModel):
    """Diagnostic profile of Context Assembly & Prompt Engineering (Stage 7a)."""
    context_chunks_count: int = Field(..., description="Number of chunk contexts injected")
    context_total_characters: int = Field(..., description="Total character length of injected context")
    system_prompt: str = Field(..., description="Injected system role instructions")
    assembled_prompt_preview: str = Field(..., description="First 300 characters of the final assembled prompt")
    latency_ms: float = Field(..., description="Assembly latency in milliseconds")


class GenerationStageTrace(BaseModel):
    """Diagnostic profile of LLM Generation (Stage 7b)."""
    provider: str = Field(..., description="LLM provider ('groq', 'openai', 'mock')")
    model_name: str = Field(..., description="Model identifier used for generation")
    generated_answer: str = Field(..., description="Final generated answer string")
    source_citations: List[str] = Field(default_factory=list, description="Extracted source citations")
    estimated_prompt_tokens: int = Field(0, description="Estimated input token count")
    estimated_completion_tokens: int = Field(0, description="Estimated output token count")
    latency_ms: float = Field(..., description="LLM generation inference latency in milliseconds")


class QueryExecutionTrace(BaseModel):
    """
    Unified end-to-end trace profiling every internal transformation of a RAG query.
    """
    trace_id: str = Field(..., description="Unique query trace identifier (e.g., trace_20261020_001)")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Execution timestamp in ISO 8601 UTC"
    )
    query: str = Field(..., description="Original user query")
    total_latency_ms: float = Field(..., description="Total end-to-end execution latency in milliseconds")
    
    # Stage Traces
    retrieval: RetrievalStageTrace = Field(..., description="Vector retrieval diagnostics")
    rerank: Optional[RerankStageTrace] = Field(None, description="Neural reranking diagnostics (if enabled)")
    prompt_assembly: PromptAssemblyStageTrace = Field(..., description="Prompt assembly diagnostics")
    generation: GenerationStageTrace = Field(..., description="LLM generation diagnostics")
    
    # Optional Real-Time Triad Evaluation
    evaluation: Optional[Dict[str, Any]] = Field(None, description="Optional Triad evaluation against ground truth")

    def format_trace_report(self) -> str:
        """Render a comprehensive, readable markdown trace inspection report."""
        lines = [
            f"### 🔍 AeroqAI Interactive RAG Query Trace: `{self.trace_id}`",
            f"- **Query**: *\"{self.query}\"*",
            f"- **Total Latency**: `{self.total_latency_ms:.1f} ms`",
            f"- **Execution Timestamp**: `{self.timestamp}`",
            "",
            "#### ⏱️ Latency Waterfall Breakdown",
            f"- Vector Retrieval : `{self.retrieval.latency_ms:.1f} ms`",
        ]

        if self.rerank:
            lines.append(f"- Cross-Encoder Rerank: `{self.rerank.latency_ms:.1f} ms`")
        
        lines.append(f"- Prompt Assembly  : `{self.prompt_assembly.latency_ms:.2f} ms`")
        lines.append(f"- LLM Generation   : `{self.generation.latency_ms:.1f} ms` ({self.generation.model_name})")

        lines.extend([
            "",
            "#### 📑 Candidate Passages & Score Transitions",
            "| Initial Rank | Final Rank | Rank Shift | File / Page | Retr. Score | Rerank Score | Retained? | Content Snippet |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |"
        ])

        chunks = self.rerank.reranked_chunks if self.rerank else self.retrieval.retrieved_chunks
        for c in chunks:
            f_rank = f"`#{c.final_rank}`" if c.final_rank is not None else f"`#{c.initial_rank}`"
            
            if c.rank_delta is None or c.rank_delta == 0:
                shift_str = "`=`"
            elif c.rank_delta > 0:
                shift_str = f"`+{c.rank_delta}` 🔼"
            else:
                shift_str = f"`{c.rank_delta}` 🔽"

            rr_score = f"`{c.rerank_score:.4f}`" if c.rerank_score is not None else "-"
            retained_str = "✅ YES" if c.retained_in_context else "❌ PRUNED"
            snippet = c.content_snippet.replace("\n", " ").strip()
            if len(snippet) > 60:
                snippet = snippet[:57] + "..."

            lines.append(
                f"| `#{c.initial_rank}` | {f_rank} | {shift_str} | `{c.source_file}:p{c.page_number}` | "
                f"`{c.initial_retrieval_score:.4f}` | {rr_score} | {retained_str} | {snippet} |"
            )

        lines.extend([
            "",
            "#### 🤖 Final Generated Response",
            f"> {self.generation.generated_answer}",
            "",
            f"- **Model**: `{self.generation.model_name}` (Provider: `{self.generation.provider}`)",
            f"- **Estimated Tokens**: In: `{self.generation.estimated_prompt_tokens}` | Out: `{self.generation.estimated_completion_tokens}`",
        ])

        if self.generation.source_citations:
            lines.append(f"- **Citations**: {', '.join(self.generation.source_citations)}")

        if self.evaluation:
            lines.extend([
                "",
                "#### ⚖️ Ground Truth Evaluation Triad",
                f"- **Faithfulness**: `{self.evaluation.get('faithfulness', 0.0):.4f}`",
                f"- **Answer Correctness**: `{self.evaluation.get('correctness', 0.0):.4f}`",
                f"- **Context Precision**: `{self.evaluation.get('precision', 0.0):.4f}`",
                f"- **Overall Triad Score**: `{self.evaluation.get('overall', 0.0):.4f}`"
            ])

        return "\n".join(lines)
