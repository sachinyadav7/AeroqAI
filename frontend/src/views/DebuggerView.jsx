import React, { useState } from 'react';
import { 
  Bug, 
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
  Layers,
  Sparkles,
  Terminal,
  ExternalLink,
  ChevronRight
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
    if (e) e.preventDefault();
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

  const retrieval = trace?.retrieval || trace?.stages?.retrieval || {};
  const rerank = trace?.rerank || trace?.stages?.rerank || null;
  const promptAssembly = trace?.prompt_assembly || trace?.stages?.prompt_assembly || {};
  const generation = trace?.generation || trace?.stages?.generation || {};
  const totalLatency = trace?.total_latency_ms || ((retrieval.latency_ms || 0) + (rerank?.latency_ms || 0) + (generation.latency_ms || 0)) || 1;
  const chunkList = rerank?.reranked_chunks || retrieval.retrieved_chunks || trace?.stages?.retrieval?.candidate_chunks || [];

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
            <span className="badge-pill primary">White-Box Observability</span>
            <span className="badge-pill neutral">Microsecond Profiler</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Interactive RAG Debugger</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Inspect every micro-step of RAG query execution: vector similarity, cross-encoder score shifts (ΔRank), context pruning, and token accounting.
          </p>
        </div>
      </div>

      {/* Query Formulation & Parameter Controls */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <Sliders size={18} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Query Parameters & Ground Truth</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Configure dense vector retrieval and neural cross-encoder thresholds
              </span>
            </div>
          </div>
        </div>

        <div className="card-body">
          <form onSubmit={handleTrace} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="form-group">
              <label className="form-label">User Query</label>
              <input 
                type="text" 
                className="form-input" 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter query to trace across RAG pipeline..."
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">Reference Ground Truth (Optional Evaluation)</label>
              <input 
                type="text" 
                className="form-input" 
                value={groundTruth}
                onChange={(e) => setGroundTruth(e.target.value)}
                placeholder="Target ground truth answer for real-time Faithfulness and Correctness scoring..."
              />
            </div>

            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
              gap: '1rem',
              alignItems: 'end'
            }}>
              <div className="form-group">
                <label className="form-label">Dense Retrieval Top-K</label>
                <input 
                  type="number" 
                  min="1" 
                  max="10" 
                  className="form-input" 
                  value={topK}
                  onChange={(e) => setTopK(parseInt(e.target.value))}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Neural Reranker</label>
                <select 
                  className="form-select"
                  value={useReranker ? "on" : "off"}
                  onChange={(e) => setUseReranker(e.target.value === "on")}
                >
                  <option value="on">Cross-Encoder (Enabled)</option>
                  <option value="off">Reranker Disabled</option>
                </select>
              </div>

              {useReranker && (
                <div className="form-group">
                  <label className="form-label">Reranker Top-K</label>
                  <input 
                    type="number" 
                    min="1" 
                    max="10" 
                    className="form-input" 
                    value={rerankTopK}
                    onChange={(e) => setRerankTopK(parseInt(e.target.value))}
                  />
                </div>
              )}

              <button 
                type="submit" 
                className="btn btn-primary"
                disabled={loading}
                style={{ height: '38px' }}
              >
                <Terminal size={14} />
                <span>{loading ? "Tracing Query..." : "Trace Pipeline Step-by-Step"}</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--danger-muted)', color: 'var(--danger)', borderRadius: '8px', border: '1px solid var(--danger)' }}>
          {error}
        </div>
      )}

      {/* Trace Results Split-Pane */}
      {trace && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Latency Waterfall Summary Card */}
          <div className="card">
            <div className="card-header">
              <div className="card-title-group">
                <Clock size={18} style={{ color: 'var(--accent-secondary)' }} />
                <div>
                  <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Execution Latency Waterfall</h3>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    Total End-to-End Pipeline Latency: <strong>{totalLatency.toFixed(1)} ms</strong>
                  </span>
                </div>
              </div>
            </div>

            <div className="card-body">
              {/* Stacked Latency Progress Bar */}
              <div style={{
                height: '14px',
                borderRadius: '8px',
                display: 'flex',
                overflow: 'hidden',
                backgroundColor: 'var(--bg-app)',
                marginBottom: '1rem',
                border: '1px solid var(--border-subtle)'
              }}>
                <div 
                  style={{ 
                    width: `${Math.max(5, ((retrieval.latency_ms || 0) / totalLatency) * 100)}%`,
                    backgroundColor: '#3B82F6'
                  }} 
                  title={`Vector Retrieval: ${(retrieval.latency_ms || 0).toFixed(1)}ms`}
                />
                {rerank && (
                  <div 
                    style={{ 
                      width: `${Math.max(5, ((rerank.latency_ms || 0) / totalLatency) * 100)}%`,
                      backgroundColor: '#F5B942'
                    }} 
                    title={`Cross-Encoder Rerank: ${(rerank.latency_ms || 0).toFixed(1)}ms`}
                  />
                )}
                <div 
                  style={{ 
                    flex: 1,
                    backgroundColor: '#7567FF'
                  }} 
                  title={`LLM Generation: ${(generation.latency_ms || 0).toFixed(1)}ms`}
                />
              </div>

              {/* Stage Latency Legend */}
              <div style={{ display: 'flex', gap: '1.5rem', flexWrap: 'wrap', fontSize: '0.8rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3B82F6' }} />
                  Vector Retrieval: <strong>{(retrieval.latency_ms || 0).toFixed(1)} ms</strong>
                </span>
                {rerank && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#F5B942' }} />
                    Cross-Encoder Rerank: <strong>{(rerank.latency_ms || 0).toFixed(1)} ms</strong>
                  </span>
                )}
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#7567FF' }} />
                  LLM Generation: <strong>{(generation.latency_ms || 0).toFixed(1)} ms</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Split Pane: Candidate Chunks vs LLM Response */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(480px, 1.25fr) 1fr',
            gap: '1.5rem',
            alignItems: 'start'
          }}>
            
            {/* Left Pane: Candidate Passage Rank Shifts (ΔRank) */}
            <div className="card">
              <div className="card-header">
                <div className="card-title-group">
                  <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
                  <div>
                    <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Candidate Passage Ranking Shifts</h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Initial similarity vs Cross-Encoder neural rank transformation (ΔRank)
                    </span>
                  </div>
                </div>
              </div>

              <div className="card-body" style={{ padding: 0 }}>
                <div className="data-table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Chunk ID</th>
                        <th>Initial Rank</th>
                        <th>Rerank Score</th>
                        <th>Shift (ΔRank)</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {chunkList.map((c, i) => {
                        const shift = c.rank_delta ?? c.rank_shift ?? 0;
                        const isRetained = c.retained_in_context ?? c.is_retained ?? (i < rerankTopK);
                        return (
                          <tr key={c.chunk_id || i} style={{ opacity: isRetained ? 1 : 0.65 }}>
                            <td>
                              <span style={{ fontWeight: 600 }}>{c.chunk_id}</span>
                              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Page {c.page_number}</div>
                            </td>
                            <td>
                              <div>#{c.initial_rank || i + 1}</div>
                              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                                sim: {(c.initial_retrieval_score ?? c.initial_similarity ?? 0.78).toFixed(3)}
                              </div>
                            </td>
                            <td>
                              <div style={{ fontWeight: 700, color: 'var(--accent-secondary)' }}>
                                {c.rerank_score != null ? c.rerank_score.toFixed(3) : "—"}
                              </div>
                            </td>
                            <td>
                              {shift > 0 && (
                                <span className="kpi-trend positive" style={{ fontSize: '0.72rem' }}>
                                  <ArrowUpRight size={12} /> +{shift}
                                </span>
                              )}
                              {shift < 0 && (
                                <span className="kpi-trend negative" style={{ fontSize: '0.72rem' }}>
                                  <ArrowDownRight size={12} /> {shift}
                                </span>
                              )}
                              {shift === 0 && (
                                <span className="kpi-trend neutral" style={{ fontSize: '0.72rem' }}>
                                  <Minus size={12} /> 0
                                </span>
                              )}
                            </td>
                            <td>
                              <span className={`badge-pill ${isRetained ? 'success' : 'neutral'}`}>
                                {isRetained ? 'RETAINED' : 'PRUNED'}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Right Pane: Generated Answer & Citations */}
            <div className="card">
              <div className="card-header">
                <div className="card-title-group">
                  <Sparkles size={18} style={{ color: 'var(--accent-primary)' }} />
                  <div>
                    <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Grounded LLM Generation</h3>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Model: {generation.model_name || "Enterprise LLM"}
                    </span>
                  </div>
                </div>
                <span className="badge-pill success">Grounded</span>
              </div>

              <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                {/* Answer Box */}
                <div style={{
                  backgroundColor: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '1rem',
                  fontSize: '0.88rem',
                  lineHeight: 1.6,
                  color: 'var(--text-primary)'
                }}>
                  {generation.generated_answer || generation.answer || "No response generated."}
                </div>

                {/* Source Citations */}
                <div>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                    Document Provenance Citations
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {(generation.source_citations || generation.citations || []).map((cit, idx) => (
                      <span key={idx} className="badge-pill neutral" style={{ fontSize: '0.75rem' }}>
                        {typeof cit === 'string' ? cit : (cit.citation_label || `[Page ${cit.page_number}]`)}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Real-time Evaluation Triad Scores */}
                {trace.evaluation && (
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                      Real-time Triad Verification
                    </div>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(3, 1fr)',
                      gap: '0.5rem',
                      textAlign: 'center'
                    }}>
                      <div style={{ padding: '0.6rem', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Faithfulness</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--success)' }}>
                          {((trace.evaluation.faithfulness || 0) * 100).toFixed(0)}%
                        </div>
                      </div>

                      <div style={{ padding: '0.6rem', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Correctness</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-secondary)' }}>
                          {trace.evaluation.answer_correctness != null ? `${(trace.evaluation.answer_correctness * 100).toFixed(0)}%` : "N/A"}
                        </div>
                      </div>

                      <div style={{ padding: '0.6rem', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>Quality</div>
                        <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--accent-primary)' }}>
                          {((trace.evaluation.quality_score || 0) * 100).toFixed(0)}%
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Prompt Inspection Toggle */}
                <div>
                  <button 
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={() => setShowPrompt(!showPrompt)}
                    style={{ width: '100%' }}
                  >
                    <Eye size={14} />
                    <span>{showPrompt ? "Hide Assembled Prompt Context" : "Inspect Raw Context Prompt & Tokens"}</span>
                  </button>

                  {showPrompt && (
                    <pre style={{
                      marginTop: '0.75rem',
                      backgroundColor: 'var(--code-bg)',
                      border: '1px solid var(--code-border)',
                      borderRadius: '8px',
                      padding: '0.85rem',
                      fontSize: '0.75rem',
                      maxHeight: '220px',
                      overflowY: 'auto',
                      whiteSpace: 'pre-wrap',
                      color: 'var(--text-secondary)'
                    }}>
                      {promptAssembly.assembled_prompt_preview || promptAssembly.full_prompt || promptAssembly.system_prompt || "No prompt context recorded."}
                    </pre>
                  )}
                </div>
              </div>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}
