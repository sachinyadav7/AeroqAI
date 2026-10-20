import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  GitCompare, 
  ArrowUpRight, 
  ArrowDownRight, 
  CheckCircle2, 
  AlertTriangle,
  Clock,
  Sparkles
} from 'lucide-react';
import { fetchRuns, compareRuns } from '../apiClient';

export default function LeaderboardView() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [baselineId, setBaselineId] = useState('');
  const [candidateId, setCandidateId] = useState('');
  const [comparison, setComparison] = useState(null);
  const [compareLoading, setCompareLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    setLoading(true);
    try {
      const data = await fetchRuns(null, "overall_quality");
      setRuns(data);
      if (data.length >= 2) {
        setCandidateId(data[0].run_id);
        const baseCandidate = data.find(r => r.run_id.includes('trial_001')) || data[data.length - 1];
        setBaselineId(baseCandidate.run_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!baselineId || !candidateId) return;
    setCompareLoading(true);
    setError(null);
    try {
      const diff = await compareRuns(baselineId, candidateId);
      setComparison(diff);
    } catch (err) {
      setError(err.message);
    } finally {
      setCompareLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
          <Trophy size={22} color="var(--accent-primary)" />
          <h1 style={{ fontSize: '1.75rem' }}>Experiment Leaderboard & Differential Comparisons</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Tracks model and hyperparameter iterations over time, ranks configurations by overall quality, and performs pairwise regression checks between baseline releases and candidate pipelines.
        </p>
      </div>

      {error && (
        <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FDA4AF' }}>
          Error: {error}
        </div>
      )}

      {/* Differential Comparison Tool */}
      <div className="glass-panel glow-card" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.25rem' }}>
          <GitCompare size={18} color="var(--accent-cyan)" />
          <h3 style={{ fontSize: '1.15rem' }}>Pairwise Run Comparison (Diff Engine)</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem', alignItems: 'flex-end', marginBottom: '1.25rem' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Baseline Run (Reference)
            </label>
            <select value={baselineId} onChange={(e) => setBaselineId(e.target.value)}>
              {runs.map(r => (
                <option key={r.run_id} value={r.run_id}>{r.run_id}</option>
              ))}
            </select>
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Candidate Run (New Pipeline)
            </label>
            <select value={candidateId} onChange={(e) => setCandidateId(e.target.value)}>
              {runs.map(r => (
                <option key={r.run_id} value={r.run_id}>{r.run_id}</option>
              ))}
            </select>
          </div>

          <div>
            <button className="btn btn-primary" onClick={handleCompare} disabled={compareLoading || !baselineId || !candidateId} style={{ width: '100%' }}>
              {compareLoading ? <Clock size={16} className="spin" /> : <GitCompare size={16} />}
              Compare Runs
            </button>
          </div>
        </div>

        {/* Comparison Diff Results */}
        {comparison && (
          <div style={{ background: 'rgba(15, 23, 42, 0.7)', borderRadius: 'var(--radius-md)', padding: '1.25rem', border: '1px solid var(--border-subtle)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '10px' }}>
              <span style={{ fontSize: '0.9rem', fontWeight: 600 }}>
                Delta vs Baseline ({comparison.candidate_run_id} vs {comparison.baseline_run_id})
              </span>
              <div>
                {comparison.is_regression ? (
                  <span className="badge badge-danger">🚨 REGRESSION DETECTED</span>
                ) : (
                  <span className="badge badge-success">✅ CLEAR (NO REGRESSION)</span>
                )}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Δ Overall Quality</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: comparison.delta_quality >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {comparison.delta_quality >= 0 ? `+${(comparison.delta_quality * 100).toFixed(1)}%` : `${(comparison.delta_quality * 100).toFixed(1)}%`}
                </div>
              </div>

              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Δ Context Precision</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: comparison.delta_context_precision >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {comparison.delta_context_precision >= 0 ? `+${(comparison.delta_context_precision * 100).toFixed(1)}%` : `${(comparison.delta_context_precision * 100).toFixed(1)}%`}
                </div>
              </div>

              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Δ Faithfulness</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: comparison.delta_faithfulness >= 0 ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {comparison.delta_faithfulness >= 0 ? `+${(comparison.delta_faithfulness * 100).toFixed(1)}%` : `${(comparison.delta_faithfulness * 100).toFixed(1)}%`}
                </div>
              </div>

              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Δ Query Latency</div>
                <div style={{ fontSize: '1.1rem', fontWeight: 700, color: comparison.delta_latency_ms <= 0 ? 'var(--accent-emerald)' : 'var(--accent-amber)' }}>
                  {comparison.delta_latency_ms >= 0 ? `+${comparison.delta_latency_ms.toFixed(1)} ms` : `${comparison.delta_latency_ms.toFixed(1)} ms`}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Leaderboard Table */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Trophy size={18} color="var(--accent-primary)" />
            <h3 style={{ fontSize: '1.15rem' }}>Recorded Experiment Runs ({runs.length})</h3>
          </div>
          <span className="badge badge-purple">Sorted by Quality</span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px' }}>Rank</th>
                <th style={{ padding: '10px' }}>Run ID</th>
                <th style={{ padding: '10px' }}>Chunk / Overlap</th>
                <th style={{ padding: '10px' }}>Top-K</th>
                <th style={{ padding: '10px' }}>Reranker</th>
                <th style={{ padding: '10px' }}>Overall Quality</th>
                <th style={{ padding: '10px' }}>Faithfulness</th>
                <th style={{ padding: '10px' }}>Latency</th>
                <th style={{ padding: '10px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r, idx) => (
                <tr key={r.run_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                  <td style={{ padding: '12px 10px', fontWeight: 700 }}>#{idx + 1}</td>
                  <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{r.run_id}</td>
                  <td style={{ padding: '12px 10px' }}>{r.config.chunk_size} / {r.config.chunk_overlap}</td>
                  <td style={{ padding: '12px 10px' }}>{r.config.top_k}</td>
                  <td style={{ padding: '12px 10px' }}>
                    {r.config.use_reranker ? (
                      <span className="badge badge-purple">ON ({r.config.reranker_top_k})</span>
                    ) : (
                      <span className="badge badge-secondary">OFF</span>
                    )}
                  </td>
                  <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#A5B4FC' }}>
                    {(r.metrics.overall_quality_score * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>
                    {(r.metrics.faithfulness * 100).toFixed(1)}%
                  </td>
                  <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>
                    {r.metrics.avg_latency_ms.toFixed(1)} ms
                  </td>
                  <td style={{ padding: '12px 10px' }}>
                    <span className="badge badge-success">{r.status}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
