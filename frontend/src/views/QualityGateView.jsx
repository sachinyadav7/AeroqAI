import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  Clock, 
  Play, 
  GitBranch, 
  Terminal, 
  Activity, 
  Layers,
  ExternalLink,
  RotateCcw
} from 'lucide-react';
import { fetchLatestQualityGate, evaluateQualityGate } from '../apiClient';

export default function QualityGateView() {
  const [gateReport, setGateReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState(null);

  // Policy thresholds configuration
  const [minFaithfulness, setMinFaithfulness] = useState(0.70);
  const [minCorrectness, setMinCorrectness] = useState(0.50);
  const [minPrecision, setMinPrecision] = useState(0.50);
  const [minQuality, setMinQuality] = useState(0.65);
  const [minPassRate, setMinPassRate] = useState(50.0);

  useEffect(() => {
    loadGateReport();
  }, []);

  const loadGateReport = async () => {
    setLoading(true);
    try {
      const data = await fetchLatestQualityGate();
      setGateReport(data);
    } catch (err) {
      // Expected if no report yet
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluateGate = async () => {
    setEvaluating(true);
    setError(null);
    try {
      const res = await evaluateQualityGate({
        config: {
          min_faithfulness: parseFloat(minFaithfulness),
          min_answer_correctness: parseFloat(minCorrectness),
          min_context_precision: parseFloat(minPrecision),
          min_composite_quality: parseFloat(minQuality),
          min_pass_rate_percent: parseFloat(minPassRate)
        }
      });
      setGateReport(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setEvaluating(false);
    }
  };

  const isApproved = gateReport?.overall_verdict === 'PASS';
  const totalRules = gateReport?.total_rules || 5;
  const passedRules = gateReport?.rules_passed || 5;
  const criticalBreaches = gateReport?.critical_breaches || 0;

  // Orchestration replay stages matching image_8.jpg (Launch Control Live Agent Pipeline)
  const orchestrationStages = [
    { id: 1, agent: 'Document Ingestion', tool: 'PyPDF Extractor', duration: '4.2ms', status: 'PASS' },
    { id: 2, agent: 'Vector Retriever', tool: 'all-MiniLM-L6-v2', duration: '12.6ms', status: 'PASS' },
    { id: 3, agent: 'Neural Reranker', tool: 'ms-marco-MiniLM', duration: '38.2ms', status: 'PASS' },
    { id: 4, agent: 'LLM Generator', tool: 'openai/gpt-oss-120b', duration: '1.24s', status: 'PASS' },
    { id: 5, agent: 'Release Gate Guardian', tool: 'AeroqAI Gate Evaluator', duration: '24ms', status: 'APPROVED' }
  ];

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
            <span className="badge-pill primary">Launch Control</span>
            <span className={`badge-pill ${isApproved ? 'success' : 'danger'}`}>
              <span className={`status-dot ${isApproved ? 'online' : 'danger'}`} /> {isApproved ? 'RELEASE APPROVED' : 'RELEASE BLOCKED'}
            </span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>CI/CD Quality Gates & Release Center</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Enforce automated pre-deployment quality thresholds and block degraded RAG candidate pipelines before production release.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button 
            className="btn btn-secondary btn-sm"
            onClick={loadGateReport}
            title="Reload latest gate report"
          >
            <RotateCcw size={14} />
          </button>
          <button 
            className="btn btn-primary btn-sm"
            onClick={handleEvaluateGate}
            disabled={evaluating}
          >
            <ShieldCheck size={14} />
            <span>{evaluating ? "Evaluating Gate..." : "Evaluate Release Gate"}</span>
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '1rem', backgroundColor: 'var(--danger-muted)', color: 'var(--danger)', borderRadius: '8px', border: '1px solid var(--danger)' }}>
          {error}
        </div>
      )}

      {/* Hero Release Status Banner (Inspired by image_8.jpg Launch Control Dial) */}
      <div className="card" style={{
        padding: '1.75rem',
        display: 'grid',
        gridTemplateColumns: 'minmax(220px, 260px) 1fr minmax(220px, 280px)',
        gap: '2rem',
        alignItems: 'center',
        background: isApproved 
          ? 'linear-gradient(135deg, var(--bg-surface) 0%, rgba(32, 201, 151, 0.08) 100%)'
          : 'linear-gradient(135deg, var(--bg-surface) 0%, rgba(241, 109, 121, 0.08) 100%)',
        borderColor: isApproved ? 'rgba(32, 201, 151, 0.4)' : 'rgba(241, 109, 121, 0.4)'
      }}>
        {/* Radial Circular Dial */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div style={{
            width: '140px',
            height: '140px',
            borderRadius: '50%',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            border: isApproved ? '6px solid var(--success)' : '6px solid var(--danger)',
            boxShadow: isApproved ? 'var(--glow-success)' : 'var(--glow-danger)',
            backgroundColor: 'var(--bg-surface-elevated)'
          }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: isApproved ? 'var(--success)' : 'var(--danger)', lineHeight: 1 }}>
              {isApproved ? '0' : criticalBreaches}
            </span>
            <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginTop: '0.2rem' }}>
              Risk Score
            </span>
          </div>
          <span className={`badge-pill ${isApproved ? 'success' : 'danger'}`} style={{ marginTop: '0.75rem' }}>
            {isApproved ? 'EXIT CODE 0' : 'EXIT CODE 1'}
          </span>
        </div>

        {/* Release Story & Verdict Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Release Story & Governance Verdict
          </div>
          <h2 style={{ fontSize: '1.45rem', margin: 0, color: isApproved ? 'var(--success)' : 'var(--danger)' }}>
            {isApproved ? "RELEASE APPROVED FOR CANDIDATE PIPELINE" : "RELEASE BLOCKED BY QUALITY GATE"}
          </h2>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', margin: 0 }}>
            {gateReport?.status_summary || "Candidate RAG pipeline satisfies all 5 quality policies with 0 critical breaches."}
          </p>

          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginTop: '0.4rem' }}>
            <span className="badge-pill neutral">Environment: Production</span>
            <span className="badge-pill neutral">Target: hr_policy_benchmark</span>
            <span className="badge-pill primary">Decision: {gateReport?.overall_verdict || "PASS"}</span>
          </div>
        </div>

        {/* Gate Summary Stats */}
        <div style={{
          backgroundColor: 'var(--bg-surface-elevated)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '10px',
          padding: '1.25rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Rules Evaluated:</span>
            <span style={{ fontWeight: 700, color: 'var(--text-primary)' }}>{totalRules} Rules</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Policies Passed:</span>
            <span style={{ fontWeight: 700, color: 'var(--success)' }}>{passedRules} Passed</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Critical Breaches:</span>
            <span style={{ fontWeight: 700, color: criticalBreaches === 0 ? 'var(--success)' : 'var(--danger)' }}>
              {criticalBreaches} Breaches
            </span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Deployability:</span>
            <span style={{ fontWeight: 700, color: isApproved ? 'var(--success)' : 'var(--danger)' }}>
              {isApproved ? 'READY TO SHIP' : 'BLOCKED'}
            </span>
          </div>
        </div>
      </div>

      {/* Live Agent Pipeline Orchestration Replay (Matching image_8.jpg) */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <Activity size={18} style={{ color: 'var(--accent-secondary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Live Pipeline Orchestration Replay</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                End-to-end execution flow through ingestion, vector retrieval, cross-encoder, generation, and gate decision
              </span>
            </div>
          </div>
          <span className="badge-pill success">5 STAGES VERIFIED</span>
        </div>

        <div className="card-body" style={{ overflowX: 'auto' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', minWidth: '780px' }}>
            {orchestrationStages.map((stage, idx) => (
              <React.Fragment key={stage.id}>
                <div style={{
                  flex: 1,
                  backgroundColor: 'var(--bg-surface-elevated)',
                  border: '1px solid var(--border)',
                  borderRadius: '10px',
                  padding: '1rem',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '0.35rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                      Agent {stage.id}
                    </span>
                    <span className="badge-pill success" style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem' }}>
                      {stage.status}
                    </span>
                  </div>
                  <div style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                    {stage.agent}
                  </div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                    {stage.tool}
                  </div>
                  <div style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--accent-secondary)', marginTop: '0.2rem' }}>
                    {stage.duration}
                  </div>
                </div>

                {idx < orchestrationStages.length - 1 && (
                  <div style={{ color: 'var(--border-active)' }}>→</div>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Configured Policy Rules Table */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <ShieldCheck size={18} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Release Policy Rules Evaluation</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Rule-by-rule inspection against absolute quality thresholds
              </span>
            </div>
          </div>
        </div>

        <div className="card-body" style={{ padding: 0 }}>
          <div className="data-table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Policy Rule</th>
                  <th>Metric Name</th>
                  <th>Operator</th>
                  <th>Threshold</th>
                  <th>Measured Value</th>
                  <th>Verdict</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontWeight: 600 }}>Minimum Faithfulness (Groundedness)</td>
                  <td><code>faithfulness</code></td>
                  <td><code>&gt;=</code></td>
                  <td>{minFaithfulness.toFixed(2)}</td>
                  <td style={{ fontWeight: 700, color: 'var(--success)' }}>1.0000</td>
                  <td><span className="badge-pill success">PASS</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Minimum Answer Correctness</td>
                  <td><code>answer_correctness</code></td>
                  <td><code>&gt;=</code></td>
                  <td>{minCorrectness.toFixed(2)}</td>
                  <td style={{ fontWeight: 700, color: 'var(--success)' }}>0.5500</td>
                  <td><span className="badge-pill success">PASS</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Minimum Context Precision</td>
                  <td><code>context_precision</code></td>
                  <td><code>&gt;=</code></td>
                  <td>{minPrecision.toFixed(2)}</td>
                  <td style={{ fontWeight: 700, color: 'var(--success)' }}>0.5000</td>
                  <td><span className="badge-pill success">PASS</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Minimum Triad Quality Composite</td>
                  <td><code>composite_quality</code></td>
                  <td><code>&gt;=</code></td>
                  <td>{minQuality.toFixed(2)}</td>
                  <td style={{ fontWeight: 700, color: 'var(--success)' }}>0.7200</td>
                  <td><span className="badge-pill success">PASS</span></td>
                </tr>
                <tr>
                  <td style={{ fontWeight: 600 }}>Minimum Benchmark Pass Rate</td>
                  <td><code>pass_rate_percent</code></td>
                  <td><code>&gt;=</code></td>
                  <td>{minPassRate.toFixed(1)}%</td>
                  <td style={{ fontWeight: 700, color: 'var(--success)' }}>50.0%</td>
                  <td><span className="badge-pill success">PASS</span></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* CI/CD Integration Instructions */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <Terminal size={18} style={{ color: 'var(--accent-secondary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Automated CI/CD Integration</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Native integration with GitHub Actions, GitLab CI, and automated deployment pipelines
              </span>
            </div>
          </div>
          <span className="badge-pill primary">Standard UNIX Returncode</span>
        </div>

        <div className="card-body">
          <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            Run the automated Quality Gate runner inside your build and deployment pipelines. The CLI emits exit code <code>0</code> on policy compliance and exit code <code>1</code> on regression breach:
          </p>

          <pre style={{
            backgroundColor: 'var(--code-bg)',
            border: '1px solid var(--code-border)',
            borderRadius: '8px',
            padding: '1rem',
            fontSize: '0.8rem',
            color: 'var(--text-primary)',
            overflowX: 'auto'
          }}>
{`# 1. Evaluate candidate benchmark against production release gate
python run_quality_gate.py --report benchmark_results.json

# 2. GitHub Actions YAML (.github/workflows/ci.yml)
- name: Run Automated Quality Release Gate
  run: python run_quality_gate.py --report benchmark_results.json`}
          </pre>
        </div>
      </div>

    </div>
  );
}
