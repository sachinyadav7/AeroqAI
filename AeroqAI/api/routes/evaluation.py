"""Evaluation engine and benchmark dataset routes."""
import json
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException

from AeroqAI.models.evaluation import EvaluationSample, BenchmarkReport
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/evaluation", tags=["Evaluation Engine"])


@router.get("/datasets")
def list_datasets():
    """List available evaluation benchmark datasets."""
    eval_dir = Path("AeroqAI/data/evaluation_sets")
    datasets = []
    if eval_dir.exists():
        for file in eval_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    samples = json.load(f)
                datasets.append({
                    "dataset_id": file.stem,
                    "filename": file.name,
                    "sample_count": len(samples),
                    "path": str(file)
                })
            except Exception:
                continue
    return {"datasets": datasets}


@router.get("/latest", response_model=BenchmarkReport)
def get_latest_benchmark_report():
    """Retrieve the latest completed benchmark evaluation report."""
    report_file = Path("benchmark_results.json")
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="No benchmark report has been generated yet.")
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return BenchmarkReport(**data)


@router.post("/run", response_model=BenchmarkReport)
def run_benchmark_evaluation(dataset_name: str = "hr_policy_benchmark", sample_limit: int = 5):
    """Run an automated benchmark evaluation against a golden evaluation dataset."""
    if not pipeline_state.is_initialized:
        raise HTTPException(status_code=503, detail="Pipeline state not initialized")

    dataset_path = Path(f"AeroqAI/data/evaluation_sets/{dataset_name}.json")
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_name}' not found")

    with open(dataset_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    samples = [EvaluationSample(**s) for s in raw][:sample_limit]

    def pipeline_fn(query: str):
        retr = pipeline_state.vector_store.search_text(query, pipeline_state.embedder, top_k=4)
        reranked = pipeline_state.reranker.rerank(query, retr, top_k=2) if pipeline_state.reranker else retr
        gen = pipeline_state.generator.generate(query, reranked)
        return gen.answer, [r.chunk.content for r in reranked.results]

    report = pipeline_state.evaluator.evaluate_dataset(
        dataset_name=f"{dataset_name} (API Run)",
        samples=samples,
        pipeline_fn=pipeline_fn
    )

    # Save to benchmark_results.json
    with open("benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)

    return report
