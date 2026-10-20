"""Unit tests for Module 4: Experiment Tracking."""
import shutil
import tempfile
from pathlib import Path
import pytest

from AeroqAI.models.optimization import PipelineConfig, OptimizationTrial
from AeroqAI.models.evaluation import BenchmarkReport
from AeroqAI.models.experiment import (
    ExperimentRun,
    RunMetrics,
    RunMetadata,
    RunComparison
)
from AeroqAI.modules.module_4_experiment_tracking.tracker import ExperimentTracker


@pytest.fixture
def temp_tracker():
    """Provides an ExperimentTracker writing to an isolated temporary directory."""
    temp_dir = tempfile.mkdtemp()
    tracker = ExperimentTracker(runs_dir=temp_dir)
    yield tracker
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_experiment_run_contracts():
    """Verify ExperimentRun and RunMetrics model validation."""
    cfg = PipelineConfig(config_id="cfg_test_1", chunk_size=500, chunk_overlap=50)
    metrics = RunMetrics(
        overall_quality_score=0.85,
        faithfulness=0.95,
        answer_correctness=0.80,
        context_precision=0.80,
        pass_rate=80.0,
        avg_latency_ms=120.5,
        total_tokens_consumed=1500,
        estimated_cost_usd=0.003
    )
    run = ExperimentRun(
        run_id="run_001",
        experiment_name="test_campaign",
        config=cfg,
        metrics=metrics
    )

    assert run.run_id == "run_001"
    assert run.metrics.overall_quality_score == 0.85
    assert run.status == "COMPLETED"


def test_tracker_create_and_log_metrics(temp_tracker):
    """Verify run lifecycle: create (RUNNING) -> log_metrics (COMPLETED)."""
    cfg = PipelineConfig(config_id="cfg_tune", chunk_size=600, chunk_overlap=80)
    run = temp_tracker.create_run(
        experiment_name="hr_optimization",
        config=cfg,
        run_id="run_custom_001"
    )

    assert run.run_id == "run_custom_001"
    assert run.status == "RUNNING"
    assert run.completed_at is None

    # Verify run is stored on disk
    retrieved = temp_tracker.get_run("run_custom_001")
    assert retrieved is not None
    assert retrieved.status == "RUNNING"

    # Log metrics
    completed_metrics = RunMetrics(
        overall_quality_score=0.88,
        faithfulness=1.0,
        answer_correctness=0.80,
        context_precision=0.84,
        pass_rate=90.0,
        avg_latency_ms=65.2
    )

    final_run = temp_tracker.log_metrics("run_custom_001", completed_metrics)
    assert final_run.status == "COMPLETED"
    assert final_run.completed_at is not None
    assert final_run.metrics.overall_quality_score == 0.88

    # Re-fetch from disk to ensure persistence
    reloaded = temp_tracker.get_run("run_custom_001")
    assert reloaded.status == "COMPLETED"
    assert reloaded.metrics.avg_latency_ms == 65.2


def test_tracker_list_and_sorting(temp_tracker):
    """Verify listing runs with sorting by quality and latency."""
    cfg = PipelineConfig(config_id="c", chunk_size=500, chunk_overlap=50)

    # Run A: High quality, higher latency
    m_a = RunMetrics(overall_quality_score=0.92, faithfulness=1.0, answer_correctness=0.9, context_precision=0.86, pass_rate=90.0, avg_latency_ms=200.0)
    r_a = temp_tracker.create_run("exp_alpha", cfg, run_id="run_a")
    temp_tracker.log_metrics("run_a", m_a)

    # Run B: Lower quality, ultra fast
    m_b = RunMetrics(overall_quality_score=0.75, faithfulness=0.9, answer_correctness=0.7, context_precision=0.65, pass_rate=70.0, avg_latency_ms=25.0)
    r_b = temp_tracker.create_run("exp_alpha", cfg, run_id="run_b")
    temp_tracker.log_metrics("run_b", m_b)

    # Run C: Different experiment
    m_c = RunMetrics(overall_quality_score=0.80, faithfulness=0.8, answer_correctness=0.8, context_precision=0.80, pass_rate=80.0, avg_latency_ms=50.0)
    r_c = temp_tracker.create_run("exp_beta", cfg, run_id="run_c")
    temp_tracker.log_metrics("run_c", m_c)

    # Filter by experiment
    alpha_runs = temp_tracker.list_runs(experiment_name="exp_alpha", sort_by="overall_quality")
    assert len(alpha_runs) == 2
    assert alpha_runs[0].run_id == "run_a"
    assert alpha_runs[1].run_id == "run_b"

    # Sort by latency ascending
    fastest_runs = temp_tracker.list_runs(experiment_name="exp_alpha", sort_by="latency")
    assert fastest_runs[0].run_id == "run_b"
    assert fastest_runs[1].run_id == "run_a"


def test_tracker_log_trial_convenience(temp_tracker):
    """Verify direct logging of an OptimizationTrial into the experiment tracker."""
    dummy_report = BenchmarkReport(
        dataset_name="dummy_bench",
        evaluator_model="deterministic",
        total_samples=2,
        passed_samples=2,
        failed_samples=0,
        pass_rate=100.0,
        mean_faithfulness=1.0,
        mean_correctness=0.85,
        mean_context_precision=0.90,
        mean_overall_score=0.9167
    )
    cfg = PipelineConfig(config_id="cfg_trial_opt", chunk_size=800, chunk_overlap=100)
    trial = OptimizationTrial(
        trial_id="trial_042",
        config=cfg,
        benchmark_report=dummy_report,
        overall_quality_score=0.9167,
        faithfulness=1.0,
        answer_correctness=0.85,
        context_precision=0.90,
        avg_latency_ms=45.0,
        is_pareto_optimal=True
    )

    logged_run = temp_tracker.log_trial("optimization_campaign", trial)
    assert logged_run.run_id == "run_trial_042_cfg_trial_opt"
    assert logged_run.status == "COMPLETED"
    assert logged_run.metrics.overall_quality_score == 0.9167
    assert logged_run.metadata.tags.get("is_pareto_optimal") == "True"


def test_tracker_compare_runs(temp_tracker):
    """Verify differential comparison and regression detection between baseline and candidate."""
    cfg = PipelineConfig(config_id="c_base", chunk_size=500, chunk_overlap=50)

    # Baseline: Quality 0.80, Latency 100ms
    m_base = RunMetrics(overall_quality_score=0.80, faithfulness=0.9, answer_correctness=0.75, context_precision=0.75, pass_rate=80.0, avg_latency_ms=100.0)
    temp_tracker.create_run("benchmark", cfg, run_id="baseline_run")
    temp_tracker.log_metrics("baseline_run", m_base)

    # Candidate 1: Improved (Quality 0.88, Latency 80ms)
    m_improved = RunMetrics(overall_quality_score=0.88, faithfulness=1.0, answer_correctness=0.85, context_precision=0.80, pass_rate=90.0, avg_latency_ms=80.0)
    temp_tracker.create_run("benchmark", cfg, run_id="cand_improved")
    temp_tracker.log_metrics("cand_improved", m_improved)

    comp_improved = temp_tracker.compare_runs("baseline_run", "cand_improved", regression_tolerance=0.05)
    assert comp_improved.delta_quality == pytest.approx(0.08, abs=1e-4)
    assert comp_improved.delta_latency_ms == -20.0
    assert comp_improved.is_quality_improved is True
    assert comp_improved.is_latency_improved is True
    assert comp_improved.is_regression is False

    # Candidate 2: Regressed (Quality 0.70, drop > 0.05 tolerance)
    m_regressed = RunMetrics(overall_quality_score=0.70, faithfulness=0.8, answer_correctness=0.65, context_precision=0.65, pass_rate=60.0, avg_latency_ms=120.0)
    temp_tracker.create_run("benchmark", cfg, run_id="cand_regressed")
    temp_tracker.log_metrics("cand_regressed", m_regressed)

    comp_regressed = temp_tracker.compare_runs("baseline_run", "cand_regressed", regression_tolerance=0.05)
    assert comp_regressed.delta_quality == pytest.approx(-0.10, abs=1e-4)
    assert comp_regressed.is_quality_improved is False
    assert comp_regressed.is_regression is True

    # Check table formatting
    table = comp_improved.format_comparison_table()
    assert "AeroqAI Experiment Comparison" in table
    assert "CLEAR (NO REGRESSION)" in table
