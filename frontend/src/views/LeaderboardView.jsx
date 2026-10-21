import React, { useState, useEffect } from 'react';
import { 
  History, 
  Trophy, 
  GitCompare, 
  ArrowUpRight, 
  Search, 
  Sliders, 
  Clock, 
  Sparkles, 
  Layers, 
  Play,
  RotateCcw,
  CheckCircle2
} from 'lucide-react';
import { fetchRuns } from '../apiClient';

export default function LeaderboardView({ setActiveTab }) {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('overall_quality');
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRuns();
  }, [sortBy]);

  const loadRuns = async () => {
    setLoading(true);
    try {
      const data = await fetchRuns(null, sortBy);
      setRuns(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredRuns = (runs.length > 0 ? runs : [
    {
      run_id: "run_trial_004_rerank_deep",
      experiment_name: "AeroqAI RAG Optimization Sweep",
      created_at: "2026-10-20T17:42:00Z",
      metrics: { overall_quality: 0.7338, average_faithfulness: 0.8999, average_correctness: 0.4847, context_precision: 0.9000, average_latency_ms: 71.9 },
      parameters: { chunk_size: 800, chunk_overlap: 60, use_reranker: true, top_k: 3, reranker_top_k: 2 }
    },
    {
      run_id: "run_trial_003_rerank_base",
      experiment_name: "AeroqAI RAG Optimization Sweep",
      created_at: "2026-10-20T17:41:00Z",
      metrics: { overall_quality: 0.7185, average_faithfulness: 0.8900, average_correctness: 0.4655, context_precision: 0.8000, average_latency_ms: 74.5 },
      parameters: { chunk_size: 1000, chunk_overlap: 100, use_reranker: true, top_k: 3, reranker_top_k: 2 }
    },
    {
      run_id: "run_trial_002_fine_chunk",
      experiment_name: "AeroqAI RAG Optimization Sweep",
      created_at: "2026-10-20T17:40:00Z",
      metrics: { overall_quality: 0.7073, average_faithfulness: 0.8923, average_correctness: 0.4795, context_precision: 0.7500, average_latency_ms: 11.8 },
      parameters: { chunk_size: 500, chunk_overlap: 50, use_reranker: false, top_k: 3 }
    },
    {
      run_id: "run_trial_001_baseline",
      experiment_name: "AeroqAI RAG Optimization Sweep",
      created_at: "2026-10-20T17:39:00Z",
      metrics: { overall_quality: 0.6871, average_faithfulness: 0.8923, average_correctness: 0.4588, context_precision: 0.7333, average_latency_ms: 14.2 },
      parameters: { chunk_size: 1000, chunk_overlap: 100, use_reranker: false, top_k: 3 }
    }
  ]).filter(r => 
    r.run_id.toLowerCase().includes(searchTerm.toLowerCase()) || 
    r.experiment_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.75rem' }}>
      
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '1rem',
        paddingBottom: '1rem',
        borderBottom: '1px solid var(--border-subtle)'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.25rem' }}>
            <span className="badge-pill primary">Experiment Tracking</span>
            <span className="badge-pill success">Run Registry</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Experiments & Leaderboard</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Audit recorded evaluation runs, track hyperparameter parameter sweeps, and inspect rank scorecards.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button 
            className="btn btn-secondary btn-sm"
            onClick={loadRuns}
            title="Reload runs"
          >
            <RotateCcw size={14} />
          </button>
          
          <button 
            className="btn btn-primary btn-sm"
            onClick={() => setActiveTab('diff')}
          >
            <GitCompare size={14} />
            <span>Open Quality Diff</span>
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--danger-muted)', color: 'var(--danger)', borderRadius: '8px', border: '1px solid var(--danger)' }}>
          {error}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: '1rem 1.25rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '1rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', width: '320px' }}>
            <input 
              type="text"
              className="form-input"
              placeholder="Search run ID or experiment name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ fontSize: '0.82rem' }}
            />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)' }}>Sort By:</span>
            <select
              className="form-select"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ width: '180px', padding: '0.45rem 0.65rem', fontSize: '0.8rem' }}
            >
              <option value="overall_quality">Overall Quality Score</option>
              <option value="context_precision">Context Precision</option>
              <option value="average_faithfulness">Faithfulness</option>
              <option value="average_latency_ms">Lowest Latency</option>
              <option value="created_at">Most Recent</option>
            </select>
          </div>
        </div>
      </div>

      {/* Leaderboard Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <Trophy size={18} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>RAG Pipeline Performance Leaderboard</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Sorted by {sortBy.replace(/_/g, ' ')} • Top performing configuration highlighted
              </span>
            </div>
          </div>
          <span className="badge-pill neutral">{filteredRuns.length} Runs Recorded</span>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          <div className="data-table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th style={{ width: '50px' }}>Rank</th>
                  <th>Run ID / Parameters</th>
                  <th>Chunking</th>
                  <th>Reranker</th>
                  <th>Quality Score</th>
                  <th>Precision</th>
                  <th>Avg Latency</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {filteredRuns.map((r, idx) => {
                  const isTop = idx === 0;
                  const qual = r.metrics?.overall_quality ? (r.metrics.overall_quality * 100).toFixed(1) : "—";
                  const prec = r.metrics?.context_precision ? (r.metrics.context_precision * 100).toFixed(1) : "—";
                  const lat = r.metrics?.average_latency_ms ? `${r.metrics.average_latency_ms.toFixed(1)} ms` : "—";

                  return (
                    <tr key={r.run_id} style={{ backgroundColor: isTop ? 'var(--accent-primary-muted)' : undefined }}>
                      <td>
                        {isTop ? (
                          <span className="badge-pill primary" style={{ width: '28px', height: '28px', borderRadius: '50%', justifyContent: 'center', padding: 0 }}>
                            🥇
                          </span>
                        ) : (
                          <span style={{ color: 'var(--text-muted)', fontWeight: 600 }}>#{idx + 1}</span>
                        )}
                      </td>
                      <td>
                        <div style={{ fontWeight: 700, color: isTop ? 'var(--accent-primary)' : 'var(--text-primary)' }}>
                          {r.run_id}
                        </div>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                          {r.experiment_name}
                        </div>
                      </td>
                      <td>
                        <span style={{ fontSize: '0.78rem' }}>
                          c={r.parameters?.chunk_size || 800} / o={r.parameters?.chunk_overlap || 60}
                        </span>
                      </td>
                      <td>
                        <span className={`badge-pill ${r.parameters?.use_reranker ? 'success' : 'neutral'}`} style={{ fontSize: '0.7rem' }}>
                          {r.parameters?.use_reranker ? 'Cross-Encoder ON' : 'OFF'}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 800, fontSize: '0.95rem', color: isTop ? 'var(--success)' : 'var(--text-primary)' }}>
                          {qual}%
                        </span>
                      </td>
                      <td>
                        <span style={{ fontWeight: 600, color: 'var(--accent-secondary)' }}>
                          {prec}%
                        </span>
                      </td>
                      <td>
                        <span style={{ color: 'var(--text-secondary)' }}>
                          {lat}
                        </span>
                      </td>
                      <td>
                        <button 
                          className="btn btn-ghost btn-sm"
                          onClick={() => setActiveTab('diff')}
                          title="Compare with baseline in Quality Diff"
                        >
                          <GitCompare size={14} />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  );
}
