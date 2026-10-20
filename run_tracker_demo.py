"""
Module 4: Experiment Tracking — Live Demo & Run Registry Runner.

Demonstrates logging experiment runs, querying leaderboard rankings,
and performing side-by-side differential comparisons (Baseline vs. Candidate).
"""
import json
import sys
from pathlib import Path

from AeroqAI.models.experiment import RunMetrics, RunMetadata
from AeroqAI.models.optimization import OptimizationResult
from AeroqAI.modules.module_4_experiment_tracking.tracker import ExperimentTracker


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 85)
    print(" 📊 AeroqAI: Module 4 Experiment Tracker & Run Registry")
    print("=" * 85)

    tracker = ExperimentTracker(runs_dir="AeroqAI/data/runs")
    print(f"\n[1/4] Connected to local experiment registry at: {tracker.runs_dir.resolve()}")

    # Step 1: Ingest optimizer trials from optimization_report.json if available
    opt_report_path = Path("optimization_report.json")
    if opt_report_path.exists():
        print(f"\n[2/4] Ingesting Optimization Trials from '{opt_report_path.name}'...")
        with open(opt_report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        opt_result = OptimizationResult(**data)

        for trial in opt_result.all_trials:
            run = tracker.log_trial(
                experiment_name="hr_policy_rag_tuning",
                trial=trial,
                metadata=RunMetadata(
                    environment="local",
                    tags={
                        "search_space": opt_result.search_space_name,
                        "is_pareto_optimal": str(trial.is_pareto_optimal)
                    }
                )
            )
            print(f"      • Recorded Run: `{run.run_id}` (Quality: {run.metrics.overall_quality_score:.4f}, Latency: {run.metrics.avg_latency_ms:.1f}ms)")
    else:
        print("\n[2/4] No optimization_report.json found; generating sample baseline runs...")
        # Will list existing runs if already populated

    # Step 2: Render Experiment Leaderboard
    print(f"\n[3/4] Generating Experiment Leaderboard Ranking (Sorted by Overall Quality):")
    print("-" * 85)
    leaderboard = tracker.format_leaderboard(experiment_name="hr_policy_rag_tuning", limit=10)
    print(leaderboard)
    print("-" * 85)

    # Step 3: Run Differential Comparison (Baseline vs. Candidate)
    runs = tracker.list_runs(experiment_name="hr_policy_rag_tuning", sort_by="overall_quality")
    if len(runs) >= 2:
        # Candidate is top quality run, Baseline is lowest/first configuration (e.g., trial_001)
        candidate_run = runs[0]
        # Look for trial_001 as the baseline
        baseline_candidates = [r for r in runs if "trial_001" in r.run_id]
        baseline_run = baseline_candidates[0] if baseline_candidates else runs[-1]

        print(f"\n[4/4] Executing Side-by-Side Run Comparison:")
        print(f"      Baseline Run : `{baseline_run.run_id}`")
        print(f"      Candidate Run: `{candidate_run.run_id}`")
        print("-" * 85)

        comparison = tracker.compare_runs(
            baseline_run_id=baseline_run.run_id,
            candidate_run_id=candidate_run.run_id,
            regression_tolerance=0.03
        )
        print(comparison.format_comparison_table())
        print("-" * 85)

    print("\n✅ Module 4 Experiment Tracking execution completed successfully!")


if __name__ == "__main__":
    main()
