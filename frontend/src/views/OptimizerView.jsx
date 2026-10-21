import React, { useState, useEffect } from 'react';
import { 
  Zap, 
  CheckCircle2, 
  Clock, 
  Play, 
  TrendingUp, 
  Award,
  Layers,
  Sparkles,
  ArrowRight,
  Info,
  Sliders,
  RotateCcw
} from 'lucide-react';
import { fetchLatestOptimizerReport, runOptimizerGrid } from '../apiClient';

export default function OptimizerView() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const [selectedConfig, setSelectedConfig] = useState(null);
  const [chartMode, setChartMode] = useState('latency'); // 'latency' | 'cost'

  // Search space parameters for custom grid
  const [chunkSizes, setChunkSizes] = useState("400, 800");
  const [chunkOverlaps, setChunkOverlaps] = useState("60");
  const [topKValues, setTopKValues] = useState("3");
  const [useReranker, setUseReranker] = useState(true);

  useEffect(() => {
    loadLatest();
  }, []);

  const loadLatest = async () => {
    setLoading(true);
    try {
      const data = await fetchLatestOptimizerReport();
      setReport(data);
      if (data?.best_configuration) {
        setSelectedConfig(data.best_configuration);
      }
    } catch (err) {
      // Expected if no report yet
    } finally {
      setLoading(false);
    }
  };

  const handleRunOptimizer = async () => {
    setRunning(true);
    setError(null);
    try {
      const parsedChunks = chunkSizes.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));
      const parsedOverlaps = chunkOverlaps.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));
      const parsedTopK = topKValues.split(",").map(s => parseInt(s.trim())).filter(n => !isNaN(n));

      const res = await runOptimizerGrid({
        search_space_name: "AeroqAI Hyperparameter Sweep",
        chunk_sizes: parsedChunks.length ? parsedChunks : [400, 800],
        chunk_overlaps: parsedOverlaps.length ? parsedOverlaps : [60],
        top_k_values: parsedTopK.length ? parsedTopK : [3],
        use_reranker_options: useReranker ? [false, true] : [false],
        reranker_top_k: 2,
        evaluation_samples_count: 4
      });
      setReport(res);
      if (res?.best_configuration) {
        setSelectedConfig(res.best_configuration);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setRunning(false);
    }
  };

  const allConfigs = report?.evaluated_configurations || [
    { config_id: "cfg_c800_o60_k3_rrON_k2", chunk_size: 800, chunk_overlap: 60, top_k: 3, use_reranker: true, reranker_top_k: 2, quality_score: 0.7338, faithfulness: 0.8999, answer_correctness: 0.4847, context_precision: 0.9000, avg_latency_ms: 71.9, is_pareto_optimal: true },
    { config_id: "cfg_c800_o60_k3_rrOFF", chunk_size: 800, chunk_overlap: 60, top_k: 3, use_reranker: false, reranker_top_k: 0, quality_score: 0.7073, faithfulness: 0.8923, answer_correctness: 0.4795, context_precision: 0.7500, avg_latency_ms: 11.8, is_pareto_optimal: true },
    { config_id: "cfg_c400_o60_k3_rrON_k2", chunk_size: 400, chunk_overlap: 60, top_k: 3, use_reranker: true, reranker_top_k: 2, quality_score: 0.7185, faithfulness: 0.8900, answer_correctness: 0.4655, context_precision: 0.8000, avg_latency_ms: 74.5, is_pareto_optimal: false },
    { config_id: "cfg_c400_o60_k3_rrOFF", chunk_size: 400, chunk_overlap: 60, top_k: 3, use_reranker: false, reranker_top_k: 0, quality_score: 0.6871, faithfulness: 0.8923, answer_correctness: 0.4588, context_precision: 0.7100, avg_latency_ms: 13.9, is_pareto_optimal: false }
  ];

  const bestConfig = report?.best_configuration || allConfigs[0];
  const activeSelected = selectedConfig || bestConfig;

  // Scatter plot bounds
  const minLatency = 0;
  const maxLatency = 100; // ms
  const minQuality = 60;  // %
  const maxQuality = 80;  // %

  const plotWidth = 560;
  const plotHeight = 240;
  const padLeft = 45;
  const padBottom = 35;
  const padRight = 30;
  const padTop = 25;

  const innerW = plotWidth - padLeft - padRight;
  const innerH = plotHeight - padTop - padBottom;

  const getX = (lat) => padLeft + ((lat - minLatency) / (maxLatency - minLatency)) * innerW;
  const getY = (qual) => padTop + innerH - (((qual * 100) - minQuality) / (maxQuality - minQuality)) * innerH;

  // Sort Pareto configs by latency for drawing smooth curve
  const paretoPoints = allConfigs
    .filter(c => c.is_pareto_optimal)
    .sort((a, b) => a.avg_latency_ms - b.avg_latency_ms);

  let paretoPathD = "";
  if (paretoPoints.length > 0) {
    paretoPathD = `M ${getX(paretoPoints[0].avg_latency_ms)},${getY(paretoPoints[0].quality_score)}`;
    for (let i = 1; i < paretoPoints.length; i++) {
      const prevX = getX(paretoPoints[i - 1].avg_latency_ms);
      const prevY = getY(paretoPoints[i - 1].quality_score);
      const currX = getX(paretoPoints[i].avg_latency_ms);
      const currY = getY(paretoPoints[i].quality_score);
      const midX = (prevX + currX) / 2;
      paretoPathD += ` C ${midX},${prevY} ${midX},${currY} ${currX},${currY}`;
    }
  }

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
            <span className="badge-pill primary">Hyperparameter Grid Search</span>
            <span className="badge-pill success">Multi-Objective Optimization</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>RAG Optimizer & Pareto Frontier</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Evaluate trade-offs between Quality vs. Latency vs. Cost. Identify non-dominated optimal pipeline configurations.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button 
            className="btn btn-secondary btn-sm"
            onClick={loadLatest}
            title="Reload latest report"
          >
            <RotateCcw size={14} />
          </button>
          <button 
            className="btn btn-primary btn-sm"
            onClick={handleRunOptimizer}
            disabled={running}
          >
            <Zap size={14} />
            <span>{running ? "Sweeping Grid..." : "Launch Grid Sweep"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--danger-muted)', color: 'var(--danger)', borderRadius: '8px', border: '1px solid var(--danger)' }}>
          {error}
        </div>
      )}

      {/* Main Grid: Interactive Scatter Plot + Inspector */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'minmax(480px, 1.4fr) 1fr',
        gap: '1.5rem',
        alignItems: 'start'
      }}>
        
        {/* Interactive Pareto Scatter Plot (Inspired by image_5.jpg) */}
        <div className="card">
          <div className="card-header">
            <div className="card-title-group">
              <TrendingUp size={18} style={{ color: 'var(--accent-primary)' }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Interactive Pareto Efficient Frontier</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Click any point to inspect configuration details and compare with baseline
                </span>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.35rem' }}>
              <button 
                className={`btn btn-sm ${chartMode === 'latency' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setChartMode('latency')}
              >
                Latency (ms)
              </button>
              <button 
                className={`btn btn-sm ${chartMode === 'cost' ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setChartMode('cost')}
              >
                Cost ($)
              </button>
            </div>
          </div>

          <div className="card-body" style={{ overflowX: 'auto', padding: '1.25rem 1rem' }}>
            {/* SVG Scatter Plot */}
            <svg width="100%" height="270" viewBox={`0 0 ${plotWidth} ${plotHeight}`} style={{ overflow: 'visible' }}>
              {/* Axes & Grid Lines */}
              {[60, 65, 70, 75, 80].map(q => {
                const y = getY(q / 100);
                return (
                  <g key={q}>
                    <line x1={padLeft} y1={y} x2={plotWidth - padRight} y2={y} stroke="var(--chart-grid)" strokeDasharray="3 3" />
                    <text x={padLeft - 8} y={y + 4} fill="var(--chart-axis)" fontSize="10" textAnchor="end">{q}%</text>
                  </g>
                );
              })}

              {[0, 25, 50, 75, 100].map(l => {
                const x = getX(l);
                return (
                  <g key={l}>
                    <line x1={x} y1={padTop} x2={x} y2={plotHeight - padBottom} stroke="var(--chart-grid)" strokeDasharray="3 3" />
                    <text x={x} y={plotHeight - padBottom + 16} fill="var(--chart-axis)" fontSize="10" textAnchor="middle">{l} ms</text>
                  </g>
                );
              })}

              {/* Axis Titles */}
              <text x={plotWidth / 2} y={plotHeight - 2} fill="var(--text-muted)" fontSize="10" fontWeight="600" textAnchor="middle">
                LATENCY (ms) — LOWER IS BETTER
              </text>
              <text transform={`rotate(-90)`} x={-(plotHeight / 2)} y="12" fill="var(--text-muted)" fontSize="10" fontWeight="600" textAnchor="middle">
                QUALITY SCORE (%)
              </text>

              {/* Pareto Frontier Smooth Curve */}
              {paretoPathD && (
                <path
                  d={paretoPathD}
                  fill="none"
                  stroke="var(--accent-secondary)"
                  strokeWidth="2.5"
                  strokeDasharray="5 3"
                />
              )}

              {/* Data Points */}
              {allConfigs.map((cfg) => {
                const cx = getX(cfg.avg_latency_ms);
                const cy = getY(cfg.quality_score);
                const isSelected = activeSelected?.config_id === cfg.config_id;
                const isPareto = cfg.is_pareto_optimal;

                return (
                  <g 
                    key={cfg.config_id} 
                    style={{ cursor: 'pointer' }}
                    onClick={() => setSelectedConfig(cfg)}
                  >
                    {/* Pulsing ring for Pareto optimal or selected */}
                    {(isPareto || isSelected) && (
                      <circle
                        cx={cx}
                        cy={cy}
                        r={isSelected ? 14 : 10}
                        fill={isPareto ? "rgba(32, 197, 231, 0.25)" : "rgba(117, 103, 255, 0.25)"}
                        className={isPareto ? "animate-pulse-glow" : ""}
                      />
                    )}

                    {/* Point Circle */}
                    <circle
                      cx={cx}
                      cy={cy}
                      r={isSelected ? 7 : (isPareto ? 6 : 4.5)}
                      fill={isPareto ? "var(--accent-secondary)" : "var(--border-active)"}
                      stroke={isSelected ? "#FFFFFF" : (isPareto ? "var(--accent-primary)" : "var(--border)")}
                      strokeWidth={isSelected ? 3 : 1.5}
                    />

                    {/* Point Callout Label */}
                    {isPareto && (
                      <text
                        x={cx + 8}
                        y={cy - 6}
                        fill="var(--text-primary)"
                        fontSize="9"
                        fontWeight="700"
                      >
                        {cfg.config_id.includes("rrON") ? "Quality Best (73.4%)" : "Fastest (11.8ms)"}
                      </text>
                    )}
                  </g>
                );
              })}
            </svg>

            {/* Plot Legend & Stats */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingTop: '0.75rem',
              borderTop: '1px solid var(--border-subtle)',
              fontSize: '0.75rem',
              color: 'var(--text-muted)'
            }}>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--accent-secondary)' }} />
                  Pareto Optimal (Non-dominated)
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <span style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--border-active)' }} />
                  Dominated Configuration
                </span>
              </div>
              <span>4 configurations evaluated</span>
            </div>
          </div>
        </div>

        {/* Configuration Inspector & Trade-off Analyzer */}
        <div className="card">
          <div className="card-header">
            <div className="card-title-group">
              <Award size={18} style={{ color: activeSelected.is_pareto_optimal ? 'var(--accent-secondary)' : 'var(--text-muted)' }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Configuration Inspector</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {activeSelected.config_id}
                </span>
              </div>
            </div>
            <span className={`badge-pill ${activeSelected.is_pareto_optimal ? 'success' : 'neutral'}`}>
              {activeSelected.is_pareto_optimal ? 'PARETO OPTIMAL' : 'SUB-OPTIMAL'}
            </span>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Metric Comparison Gauges */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.75rem' }}>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Overall Quality</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  {(activeSelected.quality_score * 100).toFixed(1)}%
                </div>
              </div>
              <div style={{ padding: '0.75rem', backgroundColor: 'var(--bg-surface-elevated)', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Average Latency</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--accent-secondary)' }}>
                  {activeSelected.avg_latency_ms.toFixed(1)} ms
                </div>
              </div>
            </div>

            {/* Parameter Matrix */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Hyperparameter Settings
              </div>
              <div style={{
                backgroundColor: 'var(--code-bg)',
                border: '1px solid var(--code-border)',
                borderRadius: '8px',
                padding: '0.85rem',
                fontSize: '0.78rem',
                fontFamily: 'JetBrains Mono, monospace'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>chunk_size:</span>
                  <span style={{ fontWeight: 600 }}>{activeSelected.chunk_size} characters</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>chunk_overlap:</span>
                  <span style={{ fontWeight: 600 }}>{activeSelected.chunk_overlap} characters</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>top_k (retrieval):</span>
                  <span style={{ fontWeight: 600 }}>{activeSelected.top_k} passages</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                  <span style={{ color: 'var(--text-muted)' }}>use_reranker:</span>
                  <span style={{ fontWeight: 600, color: activeSelected.use_reranker ? 'var(--success)' : 'var(--text-muted)' }}>
                    {activeSelected.use_reranker ? "true (cross-encoder)" : "false"}
                  </span>
                </div>
                {activeSelected.use_reranker && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                    <span style={{ color: 'var(--text-muted)' }}>reranker_top_k:</span>
                    <span style={{ fontWeight: 600 }}>{activeSelected.reranker_top_k} passages</span>
                  </div>
                )}
              </div>
            </div>

            {/* Triad Breakdown */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Triad Metric Breakdown
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.8rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Faithfulness (Groundedness)</span>
                  <span style={{ fontWeight: 700, color: 'var(--success)' }}>{(activeSelected.faithfulness * 100).toFixed(1)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Answer Correctness</span>
                  <span style={{ fontWeight: 700 }}>{(activeSelected.answer_correctness * 100).toFixed(1)}%</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Context Precision</span>
                  <span style={{ fontWeight: 700, color: 'var(--accent-secondary)' }}>{(activeSelected.context_precision * 100).toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sweep Configuration Controls Form */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <Sliders size={18} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Configure Hyperparameter Search Space</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Customize sweep grid values across chunking, retrieval Top-K, and neural rerankers
              </span>
            </div>
          </div>
        </div>

        <div className="card-body">
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            alignItems: 'end'
          }}>
            <div className="form-group">
              <label className="form-label">Chunk Sizes (chars)</label>
              <input 
                type="text" 
                className="form-input" 
                value={chunkSizes}
                onChange={(e) => setChunkSizes(e.target.value)}
                placeholder="e.g. 400, 800"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Chunk Overlaps (chars)</label>
              <input 
                type="text" 
                className="form-input" 
                value={chunkOverlaps}
                onChange={(e) => setChunkOverlaps(e.target.value)}
                placeholder="e.g. 60"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Retrieval Top-K</label>
              <input 
                type="text" 
                className="form-input" 
                value={topKValues}
                onChange={(e) => setTopKValues(e.target.value)}
                placeholder="e.g. 3, 5"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Neural Cross-Encoder</label>
              <select 
                className="form-select"
                value={useReranker ? "both" : "off"}
                onChange={(e) => setUseReranker(e.target.value === "both")}
              >
                <option value="both">Sweep Both (ON & OFF)</option>
                <option value="off">Reranker OFF Only</option>
              </select>
            </div>

            <button 
              className="btn btn-primary"
              onClick={handleRunOptimizer}
              disabled={running}
              style={{ height: '38px' }}
            >
              <Zap size={14} />
              <span>{running ? "Running Grid..." : "Execute Sweep"}</span>
            </button>
          </div>
        </div>
      </div>

    </div>
  );
}
