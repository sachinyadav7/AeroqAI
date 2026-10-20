import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  ShieldAlert, 
  CheckCircle2, 
  XCircle, 
  Play, 
  Clock, 
  Sliders,
  AlertOctagon,
  FileText
} from 'lucide-react';
import { fetchLatestQualityGate, evaluateQualityGate } from '../apiClient';

export default function QualityGateView() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState(null);

  // Policy Thresholds State
  const [minFaithfulness, setMinFaithfulness] = useState(0.70);
  const [minCorrectness, setMinCorrectness] = useState(0.50);
  const [minPrecision, setMinPrecision] = useState(0.50);
  const [minQuality, setMinQuality] = useState(0.65);
  const [minPassRate, setMinPassRate] = useState(50.0);
  const [maxRegression, setMaxRegression] = useState(0.04);

  useEffect(() => {
    loadLatest();
  }, []);

  const loadLatest = async () => {
    setLoading(true);
    try {
      const data = await fetchLatestQualityGate();
      setReport(data);
    } catch (err) {
      // Expected if first time
    } finally {
      setLoading(false);
    }
  };

  const handleEvaluate = async (e) => {
    e.preventDefault();
    setEvaluating(true);
    setError(null);
    try {
      const res = await evaluateQualityGate({
        report_path: "benchmark_results.json",
        min_faithfulness: minFaithfulness,
        min_correctness: minCorrectness,
        min_precision: minPrecision,
        min_quality: minQuality,
        min_pass_rate: minPassRate,
        max_regression: maxRegression
      });
      setReport(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setEvaluating(false);
    }
  };

  const isApproved = report?.passed === true;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Header */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '0.5rem' }}>
          <ShieldCheck size={22} color="var(--accent-primary)" />
          <h1 style={{ fontSize: '1.75rem' }}>CI/CD Quality Gates & Release Governance</h1>
        </div>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Enforces pre-deployment accuracy, groundedness, and regression thresholds. Automated build pipelines exit with returncode 0 on approval or non-zero (1) to block releases with quality breaches.
        </p>
      </div>

      {error && (
        <div style={{ padding: '1rem', borderRadius: 'var(--radius-md)', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', color: '#FDA4AF' }}>
          Error: {error}
        </div>
      )}

      {/* Main Release Status Card */}
      {report && (
        <div className="glass-panel glow-card" style={{ padding: '2rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: isApproved ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {isApproved ? <ShieldCheck size={28} color="var(--accent-emerald)" /> : <ShieldAlert size={28} color="var(--accent-rose)" />}
              </div>
              <div>
                <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Automated Release Verdict</span>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isApproved ? 'var(--accent-emerald)' : 'var(--accent-rose)' }}>
                  {isApproved ? "RELEASE APPROVED (Exit Code 0)" : "RELEASE BLOCKED (Exit Code 1)"}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1.5rem' }}>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Rules Evaluated</span>
                <strong style={{ fontSize: '1.1rem' }}>{report.passed_rules_count} / {report.total_rules_checked} Passed</strong>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block' }}>Breaches Detected</span>
                <strong style={{ fontSize: '1.1rem', color: report.failed_rules_count > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
                  {report.failed_rules_count} Breaches
                </strong>
              </div>
            </div>
          </div>

          {/* Rule Evaluations Table */}
          <div style={{ overflowX: 'auto', borderTop: '1px solid var(--border-subtle)', paddingTop: '1rem' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ color: 'var(--text-muted)' }}>
                  <th style={{ padding: '8px' }}>Rule Description</th>
                  <th style={{ padding: '8px' }}>Operator</th>
                  <th style={{ padding: '8px' }}>Threshold</th>
                  <th style={{ padding: '8px' }}>Observed Value</th>
                  <th style={{ padding: '8px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {report.rule_evaluations.map((ev, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)' }}>
                    <td style={{ padding: '10px 8px', fontWeight: 500 }}>{ev.rule.description || ev.rule.metric_name}</td>
                    <td style={{ padding: '10px 8px', fontFamily: 'var(--font-mono)' }}>{ev.rule.operator}</td>
                    <td style={{ padding: '10px 8px', fontFamily: 'var(--font-mono)' }}>{ev.rule.threshold}</td>
                    <td style={{ padding: '10px 8px', fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{ev.actual_value.toFixed(4)}</td>
                    <td style={{ padding: '10px 8px' }}>
                      {ev.passed ? (
                        <span className="badge badge-success"><CheckCircle2 size={12} /> PASS</span>
                      ) : (
                        <span className="badge badge-danger"><XCircle size={12} /> BREACH</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Policy Threshold Adjustment */}
      <div className="glass-panel" style={{ padding: '1.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '1.25rem' }}>
          <Sliders size={18} color="var(--accent-violet)" />
          <h3 style={{ fontSize: '1.15rem' }}>Configure Release Governance Policies</h3>
        </div>

        <form onSubmit={handleEvaluate} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.25rem', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Min Faithfulness (Groundedness)
            </label>
            <input
              type="number"
              step="0.05"
              min="0.1"
              max="1.0"
              className="input-text"
              value={minFaithfulness}
              onChange={(e) => setMinFaithfulness(parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Min Answer Correctness
            </label>
            <input
              type="number"
              step="0.05"
              min="0.1"
              max="1.0"
              className="input-text"
              value={minCorrectness}
              onChange={(e) => setMinCorrectness(parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Min Context Precision
            </label>
            <input
              type="number"
              step="0.05"
              min="0.1"
              max="1.0"
              className="input-text"
              value={minPrecision}
              onChange={(e) => setMinPrecision(parseFloat(e.target.value))}
            />
          </div>

          <div>
            <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
              Min Benchmark Pass Rate (%)
            </label>
            <input
              type="number"
              step="5"
              min="10"
              max="100"
              className="input-text"
              value={minPassRate}
              onChange={(e) => setMinPassRate(parseFloat(e.target.value))}
            />
          </div>

          <div>
            <button type="submit" className="btn btn-primary" disabled={evaluating} style={{ width: '100%' }}>
              {evaluating ? <Clock size={16} className="spin" /> : <Play size={16} />}
              Re-Evaluate Release Gate
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
