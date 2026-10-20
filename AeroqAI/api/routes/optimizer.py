"""RAG Hyperparameter Optimizer and Pareto Frontier routes."""
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException

from AeroqAI.models.optimization import OptimizationResult
from AeroqAI.models.evaluation import EvaluationSample
from AeroqAI.modules.module_3_optimizer.optimizer import RAGOptimizer
from AeroqAI.api.schemas import OptimizerGridRequest
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/optimizer", tags=["Optimizer"])


@router.get("/latest", response_model=OptimizationResult)
def get_latest_optimization_report():
    """Retrieve the latest hyperparameter optimization and Pareto frontier report."""
    report_file = Path("optimization_report.json")
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="No optimization report generated yet.")
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return OptimizationResult(**data)


@router.post("/grid", response_model=OptimizationResult)
def launch_grid_optimization(req: OptimizerGridRequest):
    """Launch a hyperparameter grid search across candidate RAG pipelines and compute Pareto frontier."""
    if not pipeline_state.is_initialized:
        raise HTTPException(status_code=503, detail="Pipeline state not initialized")

    benchmark_path = Path("AeroqAI/data/evaluation_sets/hr_policy_benchmark.json")
    if not benchmark_path.exists():
        raise HTTPException(status_code=404, detail="Benchmark dataset not found")

    with open(benchmark_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    samples = [EvaluationSample(**s) for s in raw][: req.evaluation_samples_count]

    optimizer = RAGOptimizer(
        cleaned_documents=pipeline_state.cleaned_documents,
        evaluation_samples=samples,
        evaluator=pipeline_state.evaluator,
        generator_provider=pipeline_state.generator.provider,
        verbose=False
    )

    result = optimizer.optimize_grid(
        search_space_name=req.search_space_name,
        chunk_sizes=req.chunk_sizes,
        chunk_overlaps=req.chunk_overlaps,
        top_k_values=req.top_k_values,
        use_reranker_options=req.use_reranker_options,
        reranker_top_k=req.reranker_top_k
    )

    # Save artifact
    with open("optimization_report.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    return result
