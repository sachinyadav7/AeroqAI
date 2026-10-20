"""
Module 4: Experiment Tracking.

Provides experiment lifecycle logging, local file-based run persistence, leaderboard
querying, and side-by-side regression comparison between baseline and candidate pipelines.
"""
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from AeroqAI.models.optimization import PipelineConfig, OptimizationTrial
from AeroqAI.models.evaluation import BenchmarkReport
from AeroqAI.models.experiment import (
    ExperimentRun,
    RunMetrics,
    RunMetadata,
    RunComparison
)


class ExperimentTracker:
    """
    Central experiment tracking registry and run comparison engine for AeroqAI.
    """

    def __init__(self, runs_dir: Optional[str or Path] = None) -> None:
        self.runs_dir = Path(runs_dir or "AeroqAI/data/runs")
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self._git_commit_cache: Optional[str] = None

    def _get_git_commit(self) -> Optional[str]:
        """Detect current git commit hash if available."""
        if self._git_commit_cache is not None:
            return self._git_commit_cache
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            self._git_commit_cache = res.stdout.strip()
        except Exception:
            self._git_commit_cache = None
        return self._git_commit_cache

    def _run_file_path(self, run_id: str) -> Path:
        """Get file path for a persisted run."""
        return self.runs_dir / f"{run_id}.json"

    def _save_run(self, run: ExperimentRun) -> None:
        """Persist experiment run to disk as JSON."""
        file_path = self._run_file_path(run.run_id)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(run.model_dump(), f, indent=2)

    def create_run(
        self,
        experiment_name: str,
        config: PipelineConfig,
        metadata: Optional[RunMetadata] = None,
        run_id: Optional[str] = None
    ) -> ExperimentRun:
        """Initialize and persist a new experiment run in 'RUNNING' state."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:6]
        assigned_run_id = run_id or f"run_{ts}_{short_id}"

        meta = metadata or RunMetadata(
            git_commit=self._get_git_commit(),
            environment=os.getenv("AEROQAI_ENV", "local"),
            user=os.getenv("USERNAME") or os.getenv("USER", "system")
        )

        dummy_metrics = RunMetrics(
            overall_quality_score=0.0,
            faithfulness=0.0,
            answer_correctness=0.0,
            context_precision=0.0,
            pass_rate=0.0,
            avg_latency_ms=0.0,
            total_tokens_consumed=0,
            estimated_cost_usd=0.0
        )

        run = ExperimentRun(
            run_id=assigned_run_id,
            experiment_name=experiment_name,
            status="RUNNING",
            config=config,
            metrics=dummy_metrics,
            metadata=meta
        )

        self._save_run(run)
        return run

    def log_metrics(
        self,
        run_id: str,
        metrics: RunMetrics,
        benchmark_report: Optional[BenchmarkReport] = None,
        artifact_paths: Optional[List[str]] = None
    ) -> ExperimentRun:
        """Finalize run with evaluated metrics and benchmark artifacts."""
        run = self.get_run(run_id)
        if not run:
            raise KeyError(f"Run '{run_id}' not found in registry at {self.runs_dir}")

        run.metrics = metrics
        run.benchmark_report = benchmark_report
        run.status = "COMPLETED"
        run.completed_at = datetime.now(timezone.utc).isoformat()
        if artifact_paths:
            run.artifact_paths.extend(artifact_paths)

        self._save_run(run)
        return run

    def log_trial(
        self,
        experiment_name: str,
        trial: OptimizationTrial,
        metadata: Optional[RunMetadata] = None
    ) -> ExperimentRun:
        """Convenience method: Record an OptimizationTrial directly as an ExperimentRun."""
        report = trial.benchmark_report
        metrics = RunMetrics(
            overall_quality_score=trial.overall_quality_score,
            faithfulness=trial.faithfulness,
            answer_correctness=trial.answer_correctness,
            context_precision=trial.context_precision,
            pass_rate=report.pass_rate,
            avg_latency_ms=trial.avg_latency_ms,
            total_tokens_consumed=0,
            estimated_cost_usd=trial.estimated_cost_per_1k_queries
        )

        meta = metadata or RunMetadata(
            git_commit=self._get_git_commit(),
            environment=os.getenv("AEROQAI_ENV", "local"),
            user=os.getenv("USERNAME") or os.getenv("USER", "system"),
            tags={"is_pareto_optimal": str(trial.is_pareto_optimal)}
        )

        run = ExperimentRun(
            run_id=f"run_{trial.trial_id}_{trial.config.config_id}",
            experiment_name=experiment_name,
            status="COMPLETED",
            completed_at=datetime.now(timezone.utc).isoformat(),
            config=trial.config,
            metrics=metrics,
            metadata=meta,
            benchmark_report=report
        )

        self._save_run(run)
        return run

    def get_run(self, run_id: str) -> Optional[ExperimentRun]:
        """Retrieve an experiment run by identifier."""
        file_path = self._run_file_path(run_id)
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ExperimentRun(**data)

    def list_runs(
        self,
        experiment_name: Optional[str] = None,
        sort_by: str = "overall_quality",
        descending: bool = True,
        limit: int = 50
    ) -> List[ExperimentRun]:
        """
        List all recorded runs, optionally filtered by experiment name and sorted by metric.
        Sort options: 'overall_quality', 'latency', 'correctness', 'faithfulness', 'created_at'.
        """
        runs: List[ExperimentRun] = []
        for file_path in self.runs_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                run = ExperimentRun(**data)
                if experiment_name is None or run.experiment_name == experiment_name:
                    runs.append(run)
            except Exception:
                continue

        # Sort runs
        if sort_by == "overall_quality":
            runs.sort(key=lambda r: r.metrics.overall_quality_score, reverse=descending)
        elif sort_by == "latency":
            # For latency, lower is generally better
            runs.sort(key=lambda r: r.metrics.avg_latency_ms, reverse=not descending)
        elif sort_by == "correctness":
            runs.sort(key=lambda r: r.metrics.answer_correctness, reverse=descending)
        elif sort_by == "faithfulness":
            runs.sort(key=lambda r: r.metrics.faithfulness, reverse=descending)
        elif sort_by == "created_at":
            runs.sort(key=lambda r: r.created_at, reverse=descending)

        return runs[:limit]

    def compare_runs(
        self,
        baseline_run_id: str,
        candidate_run_id: str,
        regression_tolerance: float = 0.05
    ) -> RunComparison:
        """
        Calculate differential quality, speed, and cost between Baseline and Candidate runs.
        Flags regression if candidate overall quality drops by more than regression_tolerance.
        """
        baseline = self.get_run(baseline_run_id)
        if not baseline:
            raise KeyError(f"Baseline run '{baseline_run_id}' not found.")

        candidate = self.get_run(candidate_run_id)
        if not candidate:
            raise KeyError(f"Candidate run '{candidate_run_id}' not found.")

        b_m = baseline.metrics
        c_m = candidate.metrics

        delta_quality = round(c_m.overall_quality_score - b_m.overall_quality_score, 4)
        delta_faithfulness = round(c_m.faithfulness - b_m.faithfulness, 4)
        delta_correctness = round(c_m.answer_correctness - b_m.answer_correctness, 4)
        delta_context_precision = round(c_m.context_precision - b_m.context_precision, 4)
        delta_latency_ms = round(c_m.avg_latency_ms - b_m.avg_latency_ms, 2)
        delta_cost_usd = round(c_m.estimated_cost_usd - b_m.estimated_cost_usd, 4)

        is_quality_improved = delta_quality > 0
        is_latency_improved = delta_latency_ms < 0
        is_regression = delta_quality < -abs(regression_tolerance)

        return RunComparison(
            baseline_run_id=baseline_run_id,
            candidate_run_id=candidate_run_id,
            delta_quality=delta_quality,
            delta_faithfulness=delta_faithfulness,
            delta_correctness=delta_correctness,
            delta_context_precision=delta_context_precision,
            delta_latency_ms=delta_latency_ms,
            delta_cost_usd=delta_cost_usd,
            is_quality_improved=is_quality_improved,
            is_latency_improved=is_latency_improved,
            is_regression=is_regression
        )

    def format_leaderboard(
        self,
        experiment_name: Optional[str] = None,
        limit: int = 10
    ) -> str:
        """Render a markdown leaderboard of top experiment runs."""
        runs = self.list_runs(experiment_name=experiment_name, sort_by="overall_quality", limit=limit)
        exp_tag = f"'{experiment_name}'" if experiment_name else "All Experiments"
        lines = [
            f"### 🏆 AeroqAI Experiment Leaderboard: {exp_tag}",
            f"- **Total Recorded Runs Listed**: `{len(runs)}`",
            "",
            "| Rank | Run ID | Chunk / Overlap | Top-K | Reranker | Quality | Faithfulness | Correctness | Latency | Status |",
            "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
        ]

        for rank, run in enumerate(runs, start=1):
            cfg = run.config
            m = run.metrics
            rr_str = f"ON ({cfg.reranker_top_k})" if cfg.use_reranker else "OFF"
            lines.append(
                f"| `{rank}` | `{run.run_id}` | `{cfg.chunk_size}/{cfg.chunk_overlap}` | `{cfg.top_k}` | "
                f"`{rr_str}` | `{m.overall_quality_score:.4f}` | `{m.faithfulness:.4f}` | "
                f"`{m.answer_correctness:.4f}` | `{m.avg_latency_ms:.1f}ms` | `{run.status}` |"
            )

        return "\n".join(lines)
