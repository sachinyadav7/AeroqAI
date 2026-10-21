/**
 * API client for interacting with AeroqAI FastAPI backend.
 */
const API_BASE = "http://127.0.0.1:8000";

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/system/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function fetchCorpus() {
  const res = await fetch(`${API_BASE}/api/system/corpus`);
  if (!res.ok) throw new Error("Failed to fetch corpus");
  return res.json();
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/system/upload`, {
    method: "POST",
    body: formData
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || "Failed to upload document");
  }
  return res.json();
}

export async function executeQuery(query, topK = 4, useReranker = true, rerankerTopK = 2) {
  const res = await fetch(`${API_BASE}/api/rag/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK, use_reranker: useReranker, reranker_top_k: rerankerTopK })
  });
  if (!res.ok) throw new Error("Query execution failed");
  return res.json();
}

export async function traceQuery(query, groundTruth = null, topK = 5, rerankTopK = 2, useReranker = true) {
  const res = await fetch(`${API_BASE}/api/debugger/trace`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      ground_truth_answer: groundTruth,
      top_k: topK,
      rerank_top_k: rerankTopK,
      use_reranker: useReranker
    })
  });
  if (!res.ok) throw new Error("Query trace failed");
  return res.json();
}

export async function fetchDatasets() {
  const res = await fetch(`${API_BASE}/api/evaluation/datasets`);
  if (!res.ok) throw new Error("Failed to fetch datasets");
  return res.json();
}

export async function fetchLatestEvaluation() {
  const res = await fetch(`${API_BASE}/api/evaluation/latest`);
  if (!res.ok) throw new Error("Failed to fetch latest evaluation report");
  return res.json();
}

export async function runEvaluation(datasetName = "hr_policy_benchmark", sampleLimit = 5) {
  const res = await fetch(`${API_BASE}/api/evaluation/run?dataset_name=${datasetName}&sample_limit=${sampleLimit}`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Evaluation run failed");
  return res.json();
}

export async function fetchLatestOptimizerReport() {
  const res = await fetch(`${API_BASE}/api/optimizer/latest`);
  if (!res.ok) throw new Error("Failed to fetch optimizer report");
  return res.json();
}

export async function runOptimizerGrid(config) {
  const res = await fetch(`${API_BASE}/api/optimizer/grid`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
  if (!res.ok) throw new Error("Optimizer grid sweep failed");
  return res.json();
}

export async function fetchRuns(experimentName = null, sortBy = "overall_quality") {
  const url = new URL(`${API_BASE}/api/experiments/runs`);
  if (experimentName) url.searchParams.append("experiment_name", experimentName);
  url.searchParams.append("sort_by", sortBy);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch experiment runs");
  return res.json();
}

export async function fetchLeaderboard(experimentName = null) {
  const url = new URL(`${API_BASE}/api/experiments/leaderboard`);
  if (experimentName) url.searchParams.append("experiment_name", experimentName);
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error("Failed to fetch leaderboard");
  return res.json();
}

export async function compareRuns(baselineId, candidateId) {
  const res = await fetch(`${API_BASE}/api/experiments/compare`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      baseline_run_id: baselineId,
      candidate_run_id: candidateId,
      regression_tolerance: 0.04
    })
  });
  if (!res.ok) throw new Error("Run comparison failed");
  return res.json();
}

export async function fetchLatestQualityGate() {
  const res = await fetch(`${API_BASE}/api/quality-gate/latest`);
  if (!res.ok) throw new Error("Failed to fetch quality gate report");
  return res.json();
}

export async function evaluateQualityGate(config) {
  const res = await fetch(`${API_BASE}/api/quality-gate/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(config)
  });
  if (!res.ok) throw new Error("Quality gate evaluation failed");
  return res.json();
}
