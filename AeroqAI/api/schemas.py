"""API Request and Response schemas for AeroqAI REST services."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from AeroqAI.models.generation import SourceCitation
from AeroqAI.models.optimization import PipelineConfig


class QueryRequest(BaseModel):
    """Payload for executing a RAG query."""
    query: str = Field(..., description="The user query text")
    top_k: int = Field(4, description="Retrieval depth")
    use_reranker: bool = Field(True, description="Whether to apply neural cross-encoder reranking")
    reranker_top_k: int = Field(2, description="Top candidates retained after reranking")


class QueryResponse(BaseModel):
    """Standard response from the RAG pipeline."""
    query: str
    answer: str
    sources: List[SourceCitation]
    latency_ms: float
    model_name: str
    provider: str


class TraceRequest(BaseModel):
    """Payload for tracing a query through the interactive debugger."""
    query: str = Field(..., description="The user query text")
    ground_truth_answer: Optional[str] = Field(None, description="Optional reference answer for Triad evaluation")
    top_k: int = Field(5, description="Initial retrieval depth")
    rerank_top_k: int = Field(2, description="Rerank candidates kept")
    use_reranker: bool = Field(True, description="Enable cross-encoder reranking")


class CompareRunsRequest(BaseModel):
    """Payload to compare two experiment runs."""
    baseline_run_id: str
    candidate_run_id: str
    regression_tolerance: float = 0.04


class QualityGateEvaluateRequest(BaseModel):
    """Payload to trigger quality gate evaluation on a benchmark report."""
    report_path: Optional[str] = "benchmark_results.json"
    baseline_run_id: Optional[str] = None
    min_faithfulness: float = 0.70
    min_correctness: float = 0.50
    min_precision: float = 0.50
    min_quality: float = 0.65
    min_pass_rate: float = 50.0
    max_regression: float = 0.04


class OptimizerGridRequest(BaseModel):
    """Payload to trigger a hyperparameter grid optimization search."""
    search_space_name: str = "API Grid Sweep"
    chunk_sizes: List[int] = Field(default_factory=lambda: [400, 800])
    chunk_overlaps: List[int] = Field(default_factory=lambda: [60])
    top_k_values: List[int] = Field(default_factory=lambda: [3])
    use_reranker_options: List[bool] = Field(default_factory=lambda: [False, True])
    reranker_top_k: int = 2
    evaluation_samples_count: int = 4
