import React, { useState } from 'react';
import { 
  Search, 
  Clock, 
  ArrowUpRight, 
  ArrowDownRight, 
  Minus, 
  CheckCircle2, 
  XCircle, 
  Sliders, 
  Eye, 
  Cpu, 
  Award,
  Zap,
  Layers
} from 'lucide-react';
import { traceQuery } from '../apiClient';

export default function DebuggerView() {
  const [query, setQuery] = useState("How many days of annual leave can be carried over into the next consecutive calendar year?");
  const [groundTruth, setGroundTruth] = useState("Up to 5 unused leave days can be carried over into the next consecutive calendar year.");
  const [topK, setTopK] = useState(5);
  const [rerankTopK, setRerankTopK] = useState(2);
  const [useReranker, setUseReranker] = useState(true);

  const [loading, setLoading] = useState(false);
  const [trace, setTrace] = useState(null);
  const [error, setError] = useState(null);
  const [showPrompt, setShowPrompt] = useState(false);

  const handleTrace = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await traceQuery(query, groundTruth || null, topK, rerankTopK, useReranker);
      setTrace(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
          <Search size={22} color="var(--accent-primary)" />
          <h1 style={{ fontSize: '1.75rem' }}>Interactive RAG Query Debugger</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Inspect every micro-step of RAG query execution in real time: vector similarity scores, neural cross-encoder score shifts, context pruning, prompt structure, token usage, and latency waterfalls.
        </p>
      </div>

      {/* Query Controls Bar */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <form onSubmit={handleTrace} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              User Query
            </label>
            <input
              type="text"
              className="input-text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter query to trace..."
            />
          </div>

          <div>
            <label style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>
              Ground Truth Reference Answer (Optional for real-time Triad evaluation)
            </label>
            <input
              type="text"
              className="input-text"
              value={groundTruth}
              onChange={(e) => setGroundTruth(e.target.value)}
              placeholder="Expected factual answer..."
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', alignItems: 'center' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Vector Retrieval Depth (Top-K): <strong>{topK}</strong>
              </label>
              <input
                type="range"
                min="2"
                max="8"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                style={{ width: '100%', accentColor: 'var(--accent-primary)' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                Rerank Retention (Top-K): <strong>{rerankTopK}</strong>
              </label>
              <input
                type="range"
                min="1"
                max={topK}
                value={rerankTopK}
                onChange={(e) => setRerankTopK(parseInt(e.target.value))}
                disabled={!useReranker}
                style={{ width: '100%', accentColor: 'var(--accent-cyan)' }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <input
                type="checkbox"
                id="rerankerToggle"
                checked={useReranker}
                onChange={(e) => setUseReranker(e.target.checked)}
                style={{ width: '18px', height: '18px', accentColor: 'var(--accent-primary)', cursor: 'pointer' }}
              />
              <label htmlFor="rerankerToggle" style={{ fontSize: '0.875rem', fontWeight: 500, cursor: 'pointer' }}>
                Enable Cross-Encoder Reranking
              </label>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', minWidth: '180px' }}>
                {loading ? <Clock size={16} className="spin" /> : <Zap size={16} />}
                Trace Pipeline Step-by-Step
              </button>
            </div>
          </div>
        </form>
      </div>

      {error && (
        <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FDA4AF' }}>
          Error: {error}
        </div>
      )}

      {/* Trace Results */}
      {trace && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          {/* Latency Waterfall Bar */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Clock size={18} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '1.15rem' }}>Stage Latency Waterfall</h3>
              </div>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: 'var(--accent-primary)' }}>
                Total: {trace.total_latency_ms.toFixed(1)} ms
              </div>
            </div>

            {/* Waterfall Segment Badges */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', marginBottom: '1.25rem' }}>
              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.25)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>1. Vector Retrieval</div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#A5B4FC' }}>{trace.retrieval.latency_ms.toFixed(1)} ms</div>
              </div>

              {trace.rerank && (
                <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(6, 182, 212, 0.1)', border: '1px solid rgba(6, 182, 212, 0.25)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>2. Cross-Encoder Rerank</div>
                  <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#67E8F9' }}>{trace.rerank.latency_ms.toFixed(1)} ms</div>
                </div>
              )}

              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(139, 92, 246, 0.1)', border: '1px solid rgba(139, 92, 246, 0.25)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>3. Prompt Assembly</div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#C084FC' }}>{trace.prompt_assembly.latency_ms.toFixed(2)} ms</div>
              </div>

              <div style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>4. LLM Generation</div>
                <div style={{ fontWeight: 700, fontSize: '1.1rem', color: '#6EE7B7' }}>{trace.generation.latency_ms.toFixed(1)} ms</div>
              </div>
            </div>
          </div>

          {/* Candidate Passages Score Transitions Table */}
          <div className="glass-panel" style={{ padding: '1.75rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Layers size={18} color="var(--accent-violet)" />
                <h3 style={{ fontSize: '1.15rem' }}>Candidate Passage Scoring & Neural Rerank Shifts</h3>
              </div>
              <span className="badge badge-purple">
                {trace.rerank ? `${trace.rerank.top_k_retained} Retained / ${trace.retrieval.total_candidates_found} Candidates` : `${trace.retrieval.total_candidates_found} Candidates`}
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Initial Rank</th>
                    <th style={{ padding: '10px' }}>Final Rank</th>
                    <th style={{ padding: '10px' }}>Rank Shift</th>
                    <th style={{ padding: '10px' }}>Document / Page</th>
                    <th style={{ padding: '10px' }}>Vector Score</th>
                    <th style={{ padding: '10px' }}>Rerank Score</th>
                    <th style={{ padding: '10px' }}>Context Status</th>
                    <th style={{ padding: '10px' }}>Passage Snippet</th>
                  </tr>
                </thead>
                <tbody>
                  {(trace.rerank ? trace.rerank.reranked_chunks : trace.retrieval.retrieved_chunks).map((c, i) => {
                    const hasShift = c.rank_delta !== null && c.rank_delta !== undefined;
                    const shiftPositive = c.rank_delta > 0;
                    const shiftNegative = c.rank_delta < 0;

                    return (
                      <tr key={i} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', background: c.retained_in_context ? 'rgba(99, 102, 241, 0.04)' : 'transparent' }}>
                        <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>#{c.initial_rank}</td>
                        <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                          {c.final_rank ? `#${c.final_rank}` : '-'}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          {!hasShift || c.rank_delta === 0 ? (
                            <span style={{ color: 'var(--text-muted)' }}>=</span>
                          ) : shiftPositive ? (
                            <span style={{ color: 'var(--accent-emerald)', fontWeight: 600 }}>+{c.rank_delta} 🔼</span>
                          ) : (
                            <span style={{ color: 'var(--accent-rose)', fontWeight: 600 }}>{c.rank_delta} 🔽</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          <span className="badge badge-info">{c.source_file}:p{c.page_number}</span>
                        </td>
                        <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>
                          {c.initial_retrieval_score.toFixed(4)}
                        </td>
                        <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)', color: c.rerank_score ? 'var(--accent-cyan)' : 'inherit' }}>
                          {c.rerank_score !== null && c.rerank_score !== undefined ? c.rerank_score.toFixed(4) : '-'}
                        </td>
                        <td style={{ padding: '12px 10px' }}>
                          {c.retained_in_context ? (
                            <span className="badge badge-success"><CheckCircle2 size={12} /> RETAINED</span>
                          ) : (
                            <span className="badge badge-danger"><XCircle size={12} /> PRUNED</span>
                          )}
                        </td>
                        <td style={{ padding: '12px 10px', color: 'var(--text-secondary)', maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {c.content_snippet}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Generated Response & Ground Truth Triad */}
          <div style={{ display: 'grid', gridTemplateColumns: trace.evaluation ? '1.5fr 1fr' : '1fr', gap: '1.5rem' }}>
            {/* Generated Answer Card */}
            <div className="glass-panel" style={{ padding: '1.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <span style={{ fontSize: '0.85rem', fontWeight: 600, color: 'var(--accent-primary)' }}>
                  Generated Response ({trace.generation.model_name})
                </span>
                <span className="badge badge-purple">
                  Tokens: In ~{trace.generation.estimated_prompt_tokens} | Out ~{trace.generation.estimated_completion_tokens}
                </span>
              </div>
              <p style={{ fontSize: '1rem', lineHeight: 1.6, color: 'var(--text-primary)', marginBottom: '1.25rem' }}>
                {trace.generation.generated_answer}
              </p>

              {trace.generation.source_citations && trace.generation.source_citations.length > 0 && (
                <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Citations:</span>
                  <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                    {trace.generation.source_citations.map((cite, idx) => (
                      <span key={idx} className="badge badge-info">{cite}</span>
                    ))}
                  </div>
                </div>
              )}

              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => setShowPrompt(!showPrompt)}
                style={{ fontSize: '0.75rem', padding: '6px 12px' }}
              >
                <Eye size={14} /> {showPrompt ? "Hide Assembled Prompt" : "Inspect Raw Assembled Prompt"}
              </button>

              {showPrompt && (
                <div style={{ marginTop: '1rem', padding: '1rem', background: '#090D16', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)', fontSize: '0.8rem', fontFamily: 'var(--font-mono)', whiteSpace: 'pre-wrap', maxHeight: '200px', overflowY: 'auto' }}>
                  {trace.prompt_assembly.assembled_prompt_preview}
                </div>
              )}
            </div>

            {/* Triad Evaluation Card (If ground truth provided) */}
            {trace.evaluation && (
              <div className="glass-panel" style={{ padding: '1.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '1rem' }}>
                  <Award size={18} color="var(--accent-emerald)" />
                  <h3 style={{ fontSize: '1.1rem' }}>Live Triad Evaluation</h3>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span>Faithfulness (Groundedness)</span>
                      <strong style={{ color: 'var(--accent-emerald)' }}>{(trace.evaluation.faithfulness * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${trace.evaluation.faithfulness * 100}%`, height: '100%', background: 'var(--accent-emerald)' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span>Answer Correctness</span>
                      <strong style={{ color: 'var(--accent-cyan)' }}>{(trace.evaluation.correctness * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${trace.evaluation.correctness * 100}%`, height: '100%', background: 'var(--accent-cyan)' }} />
                    </div>
                  </div>

                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem', marginBottom: '4px' }}>
                      <span>Context Precision</span>
                      <strong style={{ color: 'var(--accent-primary)' }}>{(trace.evaluation.precision * 100).toFixed(1)}%</strong>
                    </div>
                    <div style={{ height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${trace.evaluation.precision * 100}%`, height: '100%', background: 'var(--accent-primary)' }} />
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Composite Triad Score</span>
                    <span style={{ fontSize: '1.25rem', fontWeight: 800, color: '#A5B4FC', fontFamily: 'var(--font-display)' }}>
                      {(trace.evaluation.overall * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
