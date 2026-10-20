"""Experiment tracking and run registry routes."""
from typing import List, Optional
from fastapi import APIRouter, HTTPException

from AeroqAI.models.experiment import ExperimentRun, RunComparison
from AeroqAI.api.schemas import CompareRunsRequest
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/experiments", tags=["Experiments"])


@router.get("/runs", response_model=List[ExperimentRun])
def list_experiment_runs(
    experiment_name: Optional[str] = None,
    sort_by: str = "overall_quality",
    limit: int = 50
):
    """List all recorded experiment runs with multi-metric sorting."""
    if not pipeline_state.tracker:
        raise HTTPException(status_code=503, detail="Tracker service not initialized")
    return pipeline_state.tracker.list_runs(
        experiment_name=experiment_name,
        sort_by=sort_by,
        limit=limit
    )


@router.get("/runs/{run_id}", response_model=ExperimentRun)
def get_experiment_run(run_id: str):
    """Retrieve details and metrics for a specific experiment run."""
    if not pipeline_state.tracker:
        raise HTTPException(status_code=503, detail="Tracker service not initialized")
    run = pipeline_state.tracker.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run


@router.get("/leaderboard")
def get_leaderboard(experiment_name: Optional[str] = None, limit: int = 10):
    """Generate markdown and JSON leaderboard ranking top pipeline configurations."""
    if not pipeline_state.tracker:
        raise HTTPException(status_code=503, detail="Tracker service not initialized")
    runs = pipeline_state.tracker.list_runs(experiment_name=experiment_name, sort_by="overall_quality", limit=limit)
    markdown_table = pipeline_state.tracker.format_leaderboard(experiment_name=experiment_name, limit=limit)
    return {
        "experiment_name": experiment_name or "All",
        "total_runs": len(runs),
        "markdown_leaderboard": markdown_table,
        "runs": runs
    }


@router.post("/compare", response_model=RunComparison)
def compare_runs(req: CompareRunsRequest):
    """Perform side-by-side differential comparison and regression check between two runs."""
    if not pipeline_state.tracker:
        raise HTTPException(status_code=503, detail="Tracker service not initialized")
    try:
        comparison = pipeline_state.tracker.compare_runs(
            baseline_run_id=req.baseline_run_id,
            candidate_run_id=req.candidate_run_id,
            regression_tolerance=req.regression_tolerance
        )
        return comparison
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
