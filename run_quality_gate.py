"""
Module 5: Quality Regression & CI/CD Quality Gates — CLI Runner.

Executes automated quality release checks against benchmark evaluation reports.
Exits with returncode 0 if all quality gates pass, or non-zero (1) if critical
thresholds or regression tolerances are breached.
"""
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

from AeroqAI.models.evaluation import BenchmarkReport
from AeroqAI.models.quality_gate import QualityGateConfig
from AeroqAI.modules.module_4_experiment_tracking.tracker import ExperimentTracker
from AeroqAI.modules.module_5_quality_gates.gate_evaluator import QualityGateEvaluator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AeroqAI CI/CD Quality Gate Runner")
    parser.add_argument(
        "--report",
        type=str,
        default="benchmark_results.json",
        help="Path to generated BenchmarkReport JSON artifact (default: benchmark_results.json)"
    )
    parser.add_argument(
        "--baseline-run",
        type=str,
        default=None,
        help="Optional baseline run ID from ExperimentTracker to check for regression against"
    )
    parser.add_argument(
        "--min-faithfulness",
        type=float,
        default=0.70,
        help="Minimum required Faithfulness score (default: 0.70)"
    )
    parser.add_argument(
        "--min-correctness",
        type=float,
        default=0.50,
        help="Minimum required Answer Correctness score (default: 0.50)"
    )
    parser.add_argument(
        "--min-precision",
        type=float,
        default=0.50,
        help="Minimum required Context Precision score (default: 0.50)"
    )
    parser.add_argument(
        "--min-quality",
        type=float,
        default=0.65,
        help="Minimum required Overall Composite Quality score (default: 0.65)"
    )
    parser.add_argument(
        "--min-pass-rate",
        type=float,
        default=50.0,
        help="Minimum required benchmark pass rate percentage (default: 50.0)"
    )
    parser.add_argument(
        "--max-regression",
        type=float,
        default=0.04,
        help="Maximum allowed drop in overall score compared to baseline (default: 0.04)"
    )
    return parser.parse_args()


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()

    print("=" * 85)
    print(" 🛡️ AeroqAI: CI/CD Quality Gate & Regression Release Gate")
    print("=" * 85)

    # Step 1: Load candidate benchmark report
    report_path = Path(args.report)
    if not report_path.exists():
        print(f"❌ Error: Benchmark report artifact not found at: {report_path.resolve()}")
        print("Please run `python run_evaluation_demo.py` first to generate benchmark_results.json.")
        sys.exit(1)

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    candidate_report = BenchmarkReport(**data)
    print(f"\n[1/3] Loaded Candidate Benchmark Report: '{candidate_report.dataset_name}'")
    print(f"      • Evaluator Engine : {candidate_report.evaluator_model}")
    print(f"      • Overall Score    : {candidate_report.mean_overall_score:.4f}")
    print(f"      • Faithfulness     : {candidate_report.mean_faithfulness:.4f}")
    print(f"      • Correctness      : {candidate_report.mean_correctness:.4f}")
    print(f"      • Precision        : {candidate_report.mean_context_precision:.4f}")
    print(f"      • Pass Rate        : {candidate_report.pass_rate:.1f}%")

    # Step 2: Optionally fetch baseline report from experiment tracker
    baseline_report: Optional[BenchmarkReport] = None
    if args.baseline_run:
        tracker = ExperimentTracker(runs_dir="AeroqAI/data/runs")
        baseline_run = tracker.get_run(args.baseline_run)
        if baseline_run and baseline_run.benchmark_report:
            baseline_report = baseline_run.benchmark_report
            print(f"\n[2/3] Comparing Against Baseline Run: `{baseline_run.run_id}`")
            print(f"      • Baseline Quality : {baseline_run.metrics.overall_quality_score:.4f}")
        else:
            print(f"\n[2/3] Warning: Baseline run '{args.baseline_run}' not found or lacks report. Proceeding with absolute gates.")
    else:
        print("\n[2/3] No baseline run specified. Evaluating absolute quality policy rules.")

    # Step 3: Configure and Evaluate Quality Gate
    config = QualityGateConfig(
        gate_name="AeroqAI Production Release Gate",
        min_faithfulness=args.min_faithfulness,
        min_correctness=args.min_correctness,
        min_context_precision=args.min_precision,
        min_overall_score=args.min_quality,
        min_pass_rate=args.min_pass_rate,
        max_avg_latency_ms=2000.0,
        max_allowable_regression=args.max_regression
    )

    evaluator = QualityGateEvaluator(config=config)
    result = evaluator.evaluate_report(
        candidate_report=candidate_report,
        baseline_report=baseline_report
    )

    # Step 4: Display Markdown Results
    print("\n" + "=" * 85)
    print(" 📋 Quality Gate Evaluation Results")
    print("=" * 85)
    print(result.format_gate_summary())
    print("-" * 85)

    # Step 5: Save artifact
    output_path = Path("quality_gate_report.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, indent=2)
    print(f"📁 Quality Gate Report saved to: {output_path.resolve()}\n")

    # Step 6: Set CI/CD Exit Code
    if result.passed:
        print("🎉 SUCCESS: All quality release gates PASSED! Pipeline approved for deployment.")
        sys.exit(0)
    else:
        print("🚨 FAILURE: Quality gate failed critical thresholds! Release blocked.")
        sys.exit(1)


if __name__ == "__main__":
    main()
