"""Quality Regression & CI/CD release gate routes."""
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException

from AeroqAI.models.evaluation import BenchmarkReport
from AeroqAI.models.quality_gate import QualityGateConfig, QualityGateResult
from AeroqAI.modules.module_5_quality_gates.gate_evaluator import QualityGateEvaluator
from AeroqAI.api.schemas import QualityGateEvaluateRequest
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/quality-gate", tags=["Quality Gates"])


@router.get("/latest", response_model=QualityGateResult)
def get_latest_quality_gate_report():
    """Retrieve the latest evaluated quality gate report."""
    report_file = Path("quality_gate_report.json")
    if not report_file.exists():
        raise HTTPException(status_code=404, detail="No quality gate report found.")
    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return QualityGateResult(**data)


@router.post("/evaluate", response_model=QualityGateResult)
def evaluate_quality_gate(req: QualityGateEvaluateRequest):
    """Evaluate candidate benchmark report against quality policies and differential regression tolerance."""
    report_file = Path(req.report_path or "benchmark_results.json")
    if not report_file.exists():
        raise HTTPException(status_code=404, detail=f"Benchmark report '{report_file}' not found.")

    with open(report_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    candidate_report = BenchmarkReport(**data)

    baseline_report: Optional[BenchmarkReport] = None
    if req.baseline_run_id and pipeline_state.tracker:
        run = pipeline_state.tracker.get_run(req.baseline_run_id)
        if run and run.benchmark_report:
            baseline_report = run.benchmark_report

    config = QualityGateConfig(
        gate_name="AeroqAI Automated API Release Gate",
        min_faithfulness=req.min_faithfulness,
        min_correctness=req.min_correctness,
        min_context_precision=req.min_precision,
        min_overall_score=req.min_quality,
        min_pass_rate=req.min_pass_rate,
        max_allowable_regression=req.max_regression
    )

    evaluator = QualityGateEvaluator(config=config)
    result = evaluator.evaluate_report(
        candidate_report=candidate_report,
        baseline_report=baseline_report
    )

    # Save to quality_gate_report.json
    with open("quality_gate_report.json", "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)

    return result
