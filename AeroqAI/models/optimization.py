"""Data contracts and schemas for Module 3: RAG Optimizer."""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from AeroqAI.models.evaluation import BenchmarkReport


class PipelineConfig(BaseModel):
    """
    Hyperparameter specification for a single candidate RAG pipeline variant.
    """
    config_id: str = Field(..., description="Unique configuration tag (e.g., cfg_c500_k3_rrON)")
    chunk_size: int = Field(500, description="Target character or token length of document chunks")
    chunk_overlap: int = Field(50, description="Character overlap between consecutive chunks")
    chunk_strategy: str = Field("recursive", description="Splitting algorithm ('recursive' or 'fixed')")
    top_k: int = Field(4, description="Retrieval depth from the vector store")
    use_reranker: bool = Field(True, description="Whether neural Cross-Encoder reranking is enabled")
    reranker_top_k: int = Field(2, description="Number of top candidates retained after reranking")
    embedding_provider: str = Field("sentence-transformers", description="Embedding provider model tag")
    generator_provider: str = Field("mock", description="LLM generator provider ('mock', 'groq', 'openai')")
    prompt_template_name: str = Field("standard", description="Prompt assembly template variant")


class OptimizationTrial(BaseModel):
    """
    Performance and quality scorecard for a single evaluated pipeline configuration.
    """
    trial_id: str = Field(..., description="Trial execution identifier (e.g., trial_001)")
    config: PipelineConfig = Field(..., description="Pipeline hyperparameters tested in this trial")
    benchmark_report: BenchmarkReport = Field(..., description="Detailed benchmark evaluation output")
    
    # Key Summary Metrics for Pareto Optimization
    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Composite triad quality score")
    faithfulness: float = Field(..., ge=0.0, le=1.0, description="Mean groundedness score")
    answer_correctness: float = Field(..., ge=0.0, le=1.0, description="Mean factual correctness score")
    context_precision: float = Field(..., ge=0.0, le=1.0, description="Mean retrieval relevance score")
    
    avg_latency_ms: float = Field(..., description="Mean per-query latency in milliseconds")
    estimated_cost_per_1k_queries: float = Field(0.0, description="Estimated USD cost per 1,000 queries")
    is_pareto_optimal: bool = Field(False, description="Whether this trial lies on the Pareto frontier")


class OptimizationResult(BaseModel):
    """
    Complete bundle of RAG optimization search results, including the Pareto frontier.
    """
    search_space_name: str = Field(..., description="Name or description of the hyperparameter search space")
    total_trials: int = Field(..., description="Total number of pipeline configurations evaluated")
    best_trial: OptimizationTrial = Field(..., description="Configuration yielding the highest overall quality score")
    fastest_trial: OptimizationTrial = Field(..., description="Configuration yielding the lowest query latency")
    pareto_frontier: List[OptimizationTrial] = Field(default_factory=list, description="Non-dominated optimal trade-off configurations")
    all_trials: List[OptimizationTrial] = Field(default_factory=list, description="All evaluated candidate trials")
    total_optimization_latency_ms: float = Field(0.0, description="Total runtime of the optimization sweep")

    def format_summary_table(self) -> str:
        """Render a readable markdown summary table comparing trials and the Pareto frontier."""
        lines = [
            f"### ⚡ AeroqAI RAG Optimizer: Hyperparameter Grid Report",
            f"- **Search Space**: `{self.search_space_name}` | **Total Configurations Evaluated**: `{self.total_trials}`",
            f"- **Best Overall Quality**: Trial `{self.best_trial.trial_id}` (Quality: `{self.best_trial.overall_quality_score:.4f}`, Latency: `{self.best_trial.avg_latency_ms:.1f}ms`)",
            f"- **Fastest Pipeline**: Trial `{self.fastest_trial.trial_id}` (Latency: `{self.fastest_trial.avg_latency_ms:.1f}ms`, Quality: `{self.fastest_trial.overall_quality_score:.4f}`) ",
            f"- **Pareto Optimal Variants**: `{len(self.pareto_frontier)}` configurations on the efficient frontier",
            "",
            "| Trial ID | Chunk / Overlap | Top-K | Reranker | Quality | Correctness | Precision | Latency | Pareto? |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for t in self.all_trials:
            cfg = t.config
            pareto_tag = "⭐ YES" if t.is_pareto_optimal else "No"
            rr_tag = f"ON ({cfg.reranker_top_k})" if cfg.use_reranker else "OFF"
            lines.append(
                f"| `{t.trial_id}` | `{cfg.chunk_size}/{cfg.chunk_overlap}` | `{cfg.top_k}` | "
                f"`{rr_tag}` | `{t.overall_quality_score:.4f}` | `{t.answer_correctness:.4f}` | "
                f"`{t.context_precision:.4f}` | `{t.avg_latency_ms:.1f}ms` | {pareto_tag} |"
            )

        return "\n".join(lines)
