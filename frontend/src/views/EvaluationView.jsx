import React, { useState, useEffect } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Play, 
  Clock, 
  Award, 
  Database, 
  ShieldCheck,
  FileCheck
} from 'lucide-react';
import { fetchLatestEvaluation, runEvaluation } from '../apiClient';

export default function EvaluationView() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [sampleLimit, setSampleLimit] = useState(5);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadLatest();
  }, []);

  const loadLatest = async () => {
    setLoading(true);
    try {
      const data = await fetchLatestEvaluation();
      setReport(data);
    } catch (err) {
      // Expected if first time
    } finally {
      setLoading(false);
    }
  };

  const handleRunEvaluation = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await runEvaluation("hr_policy_benchmark", sampleLimit);
      setReport(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
            <Award size={22} color="var(--accent-primary)" />
            <h1 style={{ fontSize: '1.75rem' }}>Automated Evaluation Engine & Triad Benchmark</h1>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Evaluates the RAG pipeline against curated golden ground-truth benchmarks across Faithfulness, Factual Correctness, and Retrieval Precision.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <select 
            value={sampleLimit} 
            onChange={(e) => setSampleLimit(parseInt(e.target.value))}
            style={{ width: '130px', padding: '8px 12px' }}
          >
            <option value={3}>3 Samples (Fast)</option>
            <option value={5}>5 Samples (Standard)</option>
            <option value={10}>10 Samples (Complete)</option>
          </select>
          <button className="btn btn-primary" onClick={handleRunEvaluation} disabled={running}>
            {running ? <Clock size={16} className="spin" /> : <Play size={16} />}
            Run Live Benchmark
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FDA4AF' }}>
          Error: {error}
        </div>
      )}

      {/* Aggregate Scorecards */}
      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '1.25rem' }}>
            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Faithfulness (Groundedness)</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-emerald)', fontFamily: 'var(--font-display)' }}>
                {(report.mean_faithfulness * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Target: ≥ 70.0%</div>
            </div>

            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Answer Correctness</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-cyan)', fontFamily: 'var(--font-display)' }}>
                {(report.mean_correctness * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Target: ≥ 60.0%</div>
            </div>

            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Context Precision</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--accent-primary)', fontFamily: 'var(--font-display)' }}>
                {(report.mean_context_precision * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>Target: ≥ 60.0%</div>
            </div>

            <div className="glass-panel" style={{ padding: '1.5rem' }}>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '4px' }}>Overall Composite & Pass Rate</div>
              <div style={{ fontSize: '2rem', fontWeight: 800, color: '#A5B4FC', fontFamily: 'var(--font-display)' }}>
                {(report.mean_overall_score * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '4px' }}>
                Pass Rate: {report.pass_rate.toFixed(1)}% ({report.passed_samples}/{report.total_samples})
              </div>
            </div>
          </div>

          {/* Sample Results Table */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <FileCheck size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1.15rem' }}>Per-Query Benchmark Evaluations</h3>
              </div>
              <span className="badge badge-purple">{report.dataset_name}</span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Sample ID</th>
                    <th style={{ padding: '10px' }}>Query</th>
                    <th style={{ padding: '10px' }}>Faithfulness</th>
                    <th style={{ padding: '10px' }}>Correctness</th>
                    <th style={{ padding: '10px' }}>Precision</th>
                    <th style={{ padding: '10px' }}>Overall</th>
                    <th style={{ padding: '10px' }}>Verdict</th>
                  </tr>
                </thead>
                <tbody>
                  {report.sample_results.map((s, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{s.sample_id}</td>
                      <td style={{ padding: '12px 10px', maxWidth: '300px' }}>{s.query}</td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>{(s.faithfulness.score * 100).toFixed(1)}%</td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>{(s.answer_correctness.score * 100).toFixed(1)}%</td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>{(s.context_precision.score * 100).toFixed(1)}%</td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#A5B4FC' }}>
                        {(s.overall_score * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        {s.passed ? (
                          <span className="badge badge-success"><CheckCircle2 size={12} /> PASS</span>
                        ) : (
                          <span className="badge badge-danger"><XCircle size={12} /> FAIL</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
