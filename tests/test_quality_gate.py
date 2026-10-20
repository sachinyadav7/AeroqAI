"""Unit tests for Module 5: Quality Regression & CI/CD Quality Gates."""
import pytest

from AeroqAI.models.evaluation import BenchmarkReport, SampleEvaluationResult, MetricScore
from AeroqAI.models.quality_gate import (
    QualityGateConfig,
    QualityGateRule,
    RuleEvaluation,
    QualityGateResult
)
from AeroqAI.modules.module_5_quality_gates.gate_evaluator import QualityGateEvaluator


@pytest.fixture
def passing_benchmark_report():
    """Benchmark report meeting standard release thresholds."""
    return BenchmarkReport(
        dataset_name="Release Validation Dataset",
        evaluator_model="deterministic",
        total_samples=10,
        passed_samples=9,
        failed_samples=1,
        pass_rate=90.0,
        mean_faithfulness=0.92,
        mean_correctness=0.85,
        mean_context_precision=0.88,
        mean_overall_score=0.8833,
        total_eval_latency_ms=150.0,
        sample_results=[]
    )


@pytest.fixture
def failing_benchmark_report():
    """Benchmark report with severe hallucination / faithfulness failure."""
    return BenchmarkReport(
        dataset_name="Degraded Pipeline Dataset",
        evaluator_model="deterministic",
        total_samples=10,
        passed_samples=3,
        failed_samples=7,
        pass_rate=30.0,
        mean_faithfulness=0.45,  # Breaches 0.70 threshold
        mean_correctness=0.40,  # Breaches 0.60 threshold
        mean_context_precision=0.50,  # Breaches 0.60 threshold
        mean_overall_score=0.45,  # Breaches 0.70 threshold
        total_eval_latency_ms=300.0,
        sample_results=[]
    )


def test_quality_gate_config_contract():
    """Verify QualityGateConfig defaults and custom attributes."""
    cfg = QualityGateConfig(
        gate_name="Production Gate",
        min_faithfulness=0.85,
        min_correctness=0.75,
        max_avg_latency_ms=250.0
    )
    assert cfg.gate_name == "Production Gate"
    assert cfg.min_faithfulness == 0.85
    assert cfg.min_correctness == 0.75
    assert cfg.max_avg_latency_ms == 250.0


def test_operator_evaluations():
    """Verify numeric comparison evaluation logic."""
    evaluator = QualityGateEvaluator()
    assert evaluator._eval_operator(0.85, ">=", 0.80) is True
    assert evaluator._eval_operator(0.75, ">=", 0.80) is False
    assert evaluator._eval_operator(50.0, "<=", 100.0) is True
    assert evaluator._eval_operator(150.0, "<=", 100.0) is False
    assert evaluator._eval_operator(0.90, ">", 0.89) is True
    assert evaluator._eval_operator(0.90, "<", 0.95) is True
    assert evaluator._eval_operator(1.0, "==", 1.0) is True


def test_quality_gate_passes_on_healthy_report(passing_benchmark_report):
    """Verify that a compliant candidate report passes the quality gate."""
    evaluator = QualityGateEvaluator()
    result = evaluator.evaluate_report(
        candidate_report=passing_benchmark_report,
        candidate_latency_ms=85.0
    )

    assert result.passed is True
    assert result.failed_rules_count == 0
    assert result.passed_rules_count == result.total_rules_checked
    assert result.regression_detected is False

    summary = result.format_gate_summary()
    assert "RELEASE APPROVED" in summary
    assert "Minimum Faithfulness" in summary


def test_quality_gate_fails_on_degraded_report(failing_benchmark_report):
    """Verify that a degraded candidate report fails the quality gate and identifies breached rules."""
    evaluator = QualityGateEvaluator()
    result = evaluator.evaluate_report(candidate_report=failing_benchmark_report)

    assert result.passed is False
    assert result.failed_rules_count > 0

    failed_metrics = [e.rule.metric_name for e in result.rule_evaluations if not e.passed]
    assert "faithfulness" in failed_metrics
    assert "answer_correctness" in failed_metrics
    assert "pass_rate" in failed_metrics

    summary = result.format_gate_summary()
    assert "RELEASE BLOCKED" in summary


def test_differential_regression_detection(passing_benchmark_report):
    """Verify regression detection when comparing against a superior baseline."""
    evaluator = QualityGateEvaluator(
        QualityGateConfig(max_allowable_regression=0.03)
    )

    # Superior baseline: Overall Quality 0.96
    baseline_report = BenchmarkReport(
        dataset_name="Golden Baseline",
        evaluator_model="deterministic",
        total_samples=10,
        passed_samples=10,
        failed_samples=0,
        pass_rate=100.0,
        mean_faithfulness=0.98,
        mean_correctness=0.95,
        mean_context_precision=0.95,
        mean_overall_score=0.9600,
        sample_results=[]
    )

    # Candidate overall score is 0.8833. Delta = 0.8833 - 0.9600 = -0.0767.
    # Exceeds allowed regression drop of 0.03 -> Should fail regression gate!
    result = evaluator.evaluate_report(
        candidate_report=passing_benchmark_report,
        baseline_report=baseline_report
    )

    assert result.regression_detected is True
    assert result.passed is False
    assert result.regression_delta == pytest.approx(-0.0767, abs=1e-4)

    summary = result.format_gate_summary()
    assert "REGRESSION DETECTED" in summary
