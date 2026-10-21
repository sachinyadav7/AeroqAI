import React from 'react';
import { 
  Sun, 
  Moon, 
  Search, 
  Play, 
  Sparkles, 
  Terminal, 
  Cpu, 
  CheckCircle2, 
  ChevronRight,
  Database,
  Upload
} from 'lucide-react';

export default function Topbar({ 
  activeTab, 
  theme, 
  setTheme, 
  systemStatus, 
  onPrimaryAction 
}) {
  const getTabMetadata = () => {
    switch (activeTab) {
      case 'overview':
        return { section: 'Workspace', title: 'AI Quality Command Center', actionLabel: 'Run Evaluation', actionIcon: Play };
      case 'workflow':
        return { section: 'Workspace', title: 'Workflow Studio & Pipeline Nodes', actionLabel: 'Trace Pipeline', actionIcon: Play };
      case 'debugger':
        return { section: 'Workspace', title: 'RAG Debugger & Trace Explorer', actionLabel: 'Run Query Trace', actionIcon: Terminal };
      case 'evaluation':
        return { section: 'Workspace', title: 'Evaluation Lab & Benchmarks', actionLabel: 'Run Benchmark', actionIcon: Sparkles };
      case 'datasets':
        return { section: 'Workspace', title: 'Datasets & Knowledge Base', actionLabel: 'Upload Custom PDF', actionIcon: Upload };
      case 'optimizer':
        return { section: 'Optimization', title: 'RAG Optimizer & Pareto Frontier', actionLabel: 'Launch Grid Search', actionIcon: Sparkles };
      case 'experiments':
        return { section: 'Optimization', title: 'Experiment Run Registry', actionLabel: 'Compare Selected', actionIcon: Play };
      case 'diff':
        return { section: 'Optimization', title: 'Quality Diff (Baseline vs Candidate)', actionLabel: 'Run Regression Check', actionIcon: Play };
      case 'quality-gate':
        return { section: 'Reliability', title: 'CI/CD Quality Gates', actionLabel: 'Evaluate Policies', actionIcon: CheckCircle2 };
      case 'release-center':
        return { section: 'Reliability', title: 'Launch Control & Release Governance', actionLabel: 'Release Decision', actionIcon: CheckCircle2 };
      case 'settings':
        return { section: 'System', title: 'System Diagnostics & Settings', actionLabel: 'Health Check', actionIcon: Cpu };
      default:
        return { section: 'Platform', title: 'AeroqAI Command Center', actionLabel: 'Execute', actionIcon: Play };
    }
  };

  const meta = getTabMetadata();
  const ActionIcon = meta.actionIcon;

  return (
    <header className="topbar">
      {/* Left: Breadcrumbs & Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
        <span style={{ color: 'var(--text-muted)', fontSize: '0.8rem', fontWeight: 600 }}>
          {meta.section}
        </span>
        <ChevronRight size={14} style={{ color: 'var(--text-muted)' }} />
        <h1 style={{ fontSize: '1.05rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
          {meta.title}
        </h1>
      </div>

      {/* Center: Search & Model Context */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          backgroundColor: 'var(--input-bg)',
          border: '1px solid var(--input-border)',
          borderRadius: '8px',
          padding: '0.4rem 0.8rem',
          color: 'var(--text-muted)',
          fontSize: '0.8rem',
          width: '240px'
        }}>
          <Search size={14} />
          <input
            type="text"
            placeholder="Search runs, metrics, traces..."
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: 'var(--text-primary)',
              fontSize: '0.8rem',
              width: '100%'
            }}
          />
          <span style={{
            fontSize: '0.65rem',
            padding: '0.1rem 0.35rem',
            borderRadius: '4px',
            backgroundColor: 'var(--bg-surface-elevated)',
            color: 'var(--text-muted)',
            border: '1px solid var(--border-subtle)'
          }}>⌘K</span>
        </div>

        {/* Model Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: '0.35rem 0.75rem',
          borderRadius: '8px',
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          fontSize: '0.78rem',
          color: 'var(--text-secondary)'
        }}>
          <Cpu size={14} style={{ color: 'var(--accent-primary)' }} />
          <span>{systemStatus?.models?.generator || 'openai/gpt-oss-120b'}</span>
        </div>
      </div>

      {/* Right: Actions & Theme Toggle */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        {/* Theme Toggle Button */}
        <button
          className="btn btn-secondary btn-sm"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
          title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} mode`}
          style={{ width: '36px', height: '36px', padding: 0 }}
        >
          {theme === 'dark' ? (
            <Sun size={17} style={{ color: '#F5B942' }} />
          ) : (
            <Moon size={17} style={{ color: '#635BEE' }} />
          )}
        </button>

        {/* Primary Page Action Button */}
        <button
          className="btn btn-primary btn-sm"
          onClick={() => onPrimaryAction && onPrimaryAction(activeTab)}
        >
          <ActionIcon size={14} />
          <span>{meta.actionLabel}</span>
        </button>
      </div>
    </header>
  );
}
