"""Unit tests for AeroqAI REST API endpoints."""
import pytest
from fastapi.testclient import TestClient

from AeroqAI.api.app import app
from AeroqAI.api.state import pipeline_state


@pytest.fixture(scope="module")
def client():
    """Initializes FastAPI TestClient with mock components for fast, reliable unit testing."""
    pipeline_state.initialize(force_mock=True)
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client):
    """Verify API root descriptor."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["platform"] == "AeroqAI"
    assert data["documentation"] == "/docs"


def test_system_health(client):
    """Verify system health and status reporting."""
    res = client.get("/api/system/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["initialized"] is True
    assert "embedder" in data["models"]
    assert "generator" in data["models"]


def test_rag_query_endpoint(client):
    """Verify RAG query execution."""
    payload = {
        "query": "What is the policy for annual leave?",
        "top_k": 3,
        "use_reranker": False,
        "reranker_top_k": 2
    }
    res = client.post("/api/rag/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["query"] == payload["query"]
    assert len(data["answer"]) > 0
    assert "latency_ms" in data


def test_debugger_trace_endpoint(client):
    """Verify interactive debugger trace endpoint."""
    payload = {
        "query": "How many remote days are allowed?",
        "ground_truth_answer": "Up to 2 days per week with manager approval.",
        "top_k": 3,
        "rerank_top_k": 2,
        "use_reranker": True
    }
    res = client.post("/api/debugger/trace", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "trace_id" in data
    assert "retrieval" in data
    assert "prompt_assembly" in data
    assert "generation" in data
    assert data["generation"]["provider"] in ["mock", "groq"]


def test_evaluation_datasets_endpoint(client):
    """Verify listing evaluation datasets."""
    res = client.get("/api/evaluation/datasets")
    assert res.status_code == 200
    data = res.json()
    assert "datasets" in data
    assert any("hr_policy" in d["dataset_id"] for d in data["datasets"])


def test_experiments_runs_and_leaderboard(client):
    """Verify experiment run retrieval and leaderboard."""
    # List runs
    res = client.get("/api/experiments/runs")
    assert res.status_code == 200
    runs = res.json()
    assert isinstance(runs, list)

    # Leaderboard
    res_lb = client.get("/api/experiments/leaderboard")
    assert res_lb.status_code == 200
    lb_data = res_lb.json()
    assert "markdown_leaderboard" in lb_data


def test_quality_gate_evaluate_endpoint(client):
    """Verify quality gate evaluation endpoint."""
    payload = {
        "report_path": "benchmark_results.json",
        "min_faithfulness": 0.70,
        "min_correctness": 0.50,
        "min_precision": 0.50,
        "min_quality": 0.65,
        "min_pass_rate": 50.0
    }
    res = client.post("/api/quality-gate/evaluate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "passed" in data
    assert data["total_rules_checked"] >= 5
