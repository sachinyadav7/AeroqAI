import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  CheckCircle2, 
  Clock, 
  Play, 
  TrendingUp, 
  Award,
  Layers,
  ArrowRight
} from 'lucide-react';
import { fetchLatestOptimizerReport, runOptimizerGrid } from '../apiClient';

export default function OptimizerView() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadLatest();
  }, []);

  const loadLatest = async () => {
    setLoading(true);
    try {
      const data = await fetchLatestOptimizerReport();
      setReport(data);
    } catch (err) {
      // Expected if first time
    } finally {
      setLoading(false);
    }
  };

  const handleRunOptimizer = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await runOptimizerGrid({
        search_space_name: "Web Studio Quick Grid",
        chunk_sizes: [400, 800],
        chunk_overlaps: [60],
        top_k_values: [3],
        use_reranker_options: [false, true],
        reranker_top_k: 2,
        evaluation_samples_count: 4
      });
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
            <Zap size={22} color="var(--accent-cyan)" />
            <h1 style={{ fontSize: '1.75rem' }}>RAG Hyperparameter Optimizer & Pareto Frontier</h1>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
            Explores multi-dimensional hyperparameter combinations to discover the non-dominated Pareto Efficient Frontier across Quality, Query Latency, and Token Cost.
          </p>
        </div>

        <button className="btn btn-primary" onClick={handleRunOptimizer} disabled={running}>
          {running ? <Clock size={16} className="spin" /> : <Play size={16} />}
          Launch Grid Search
        </button>
      </div>

      {error && (
        <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FDA4AF' }}>
          Error: {error}
        </div>
      )}

      {/* Recommended Configuration Highlights */}
      {report && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
            {/* Best Quality Card */}
            <div className="glass-panel" style={{ padding: '1.75rem', borderLeft: '4px solid var(--accent-emerald)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.75rem' }}>
                <Award size={18} color="var(--accent-emerald)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-emerald)' }}>
                  Best Quality Target (Recommended)
                </span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginBottom: '0.5rem' }}>
                {report.best_trial.config.config_id}
              </div>
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <div>Quality: <strong style={{ color: '#FFFFFF' }}>{(report.best_trial.overall_quality_score * 100).toFixed(1)}%</strong></div>
                <div>Precision: <strong style={{ color: 'var(--accent-cyan)' }}>{(report.best_trial.context_precision * 100).toFixed(1)}%</strong></div>
                <div>Latency: <strong style={{ color: '#FFFFFF' }}>{report.best_trial.avg_latency_ms.toFixed(1)} ms</strong></div>
              </div>
            </div>

            {/* Fastest Pipeline Card */}
            <div className="glass-panel" style={{ padding: '1.75rem', borderLeft: '4px solid var(--accent-cyan)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '0.75rem' }}>
                <Zap size={18} color="var(--accent-cyan)" />
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-cyan)' }}>
                  Lowest Latency Target
                </span>
              </div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, fontFamily: 'var(--font-display)', marginBottom: '0.5rem' }}>
                {report.fastest_trial.config.config_id}
              </div>
              <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                <div>Latency: <strong style={{ color: 'var(--accent-cyan)' }}>{report.fastest_trial.avg_latency_ms.toFixed(1)} ms</strong></div>
                <div>Quality: <strong style={{ color: '#FFFFFF' }}>{(report.fastest_trial.overall_quality_score * 100).toFixed(1)}%</strong></div>
                <div>Reranker: <strong style={{ color: '#FFFFFF' }}>OFF</strong></div>
              </div>
            </div>
          </div>

          {/* Pareto Frontier Comparison Table */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <TrendingUp size={18} color="var(--accent-primary)" />
                <h3 style={{ fontSize: '1.15rem' }}>Evaluated Configurations & Pareto Frontier</h3>
              </div>
              <span className="badge badge-success">
                {report.pareto_frontier.length} Non-Dominated Variants
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Trial ID</th>
                    <th style={{ padding: '10px' }}>Chunk / Overlap</th>
                    <th style={{ padding: '10px' }}>Top-K</th>
                    <th style={{ padding: '10px' }}>Reranker</th>
                    <th style={{ padding: '10px' }}>Quality</th>
                    <th style={{ padding: '10px' }}>Correctness</th>
                    <th style={{ padding: '10px' }}>Precision</th>
                    <th style={{ padding: '10px' }}>Latency</th>
                    <th style={{ padding: '10px' }}>Pareto Optimal?</th>
                  </tr>
                </thead>
                <tbody>
                  {report.all_trials.map((t, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', background: t.is_pareto_optimal ? 'rgba(99, 102, 241, 0.04)' : 'transparent' }}>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{t.trial_id}</td>
                      <td style={{ padding: '12px 10px' }}>{t.config.chunk_size} / {t.config.chunk_overlap}</td>
                      <td style={{ padding: '12px 10px' }}>{t.config.top_k}</td>
                      <td style={{ padding: '12px 10px' }}>
                        {t.config.use_reranker ? (
                          <span className="badge badge-purple">ON ({t.config.reranker_top_k})</span>
                        ) : (
                          <span className="badge badge-secondary">OFF</span>
                        )}
                      </td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#A5B4FC' }}>
                        {(t.overall_quality_score * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>
                        {(t.answer_correctness * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>
                        {(t.context_precision * 100).toFixed(1)}%
                      </td>
                      <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>
                        {t.avg_latency_ms.toFixed(1)} ms
                      </td>
                      <td style={{ padding: '12px 10px' }}>
                        {t.is_pareto_optimal ? (
                          <span className="badge badge-success">⭐ PARETO</span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>Dominated</span>
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
