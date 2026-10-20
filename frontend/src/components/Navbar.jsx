import React from 'react';
import { 
  Activity, 
  Search, 
  CheckCircle2, 
  Zap, 
  Trophy, 
  ShieldCheck,
  Server
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, systemStatus }) {
  const tabs = [
    { id: 'dashboard', label: 'Overview', icon: Activity },
    { id: 'debugger', label: 'RAG Debugger', icon: Search },
    { id: 'evaluation', label: 'Triad Evaluation', icon: CheckCircle2 },
    { id: 'optimizer', label: 'Optimizer & Pareto', icon: Zap },
    { id: 'leaderboard', label: 'Leaderboard & Diffs', icon: Trophy },
    { id: 'quality-gate', label: 'CI/CD Quality Gates', icon: ShieldCheck },
  ];

  const isOnline = systemStatus?.status === 'healthy';

  return (
    <header style={{
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(8, 12, 20, 0.85)',
      backdropFilter: 'blur(16px)',
      position: 'sticky',
      top: 0,
      zIndex: 50,
      padding: '0 2rem'
    }}>
      <div style={{
        maxWidth: '1440px',
        margin: '0 auto',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: '70px',
        gap: '2rem'
      }}>
        {/* Brand Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }} onClick={() => setActiveTab('dashboard')}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #6366F1, #06B6D4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(99, 102, 241, 0.4)'
          }}>
            <Zap size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{
                fontFamily: 'var(--font-display)',
                fontWeight: 800,
                fontSize: '1.25rem',
                letterSpacing: '-0.03em',
                background: 'linear-gradient(90deg, #FFFFFF, #94A3B8)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                AeroqAI
              </span>
              <span className="badge badge-purple" style={{ fontSize: '0.65rem', padding: '1px 6px' }}>v1.0</span>
            </div>
            <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', display: 'block', marginTop: '-2px' }}>
              Enterprise RAG Evaluation & QA
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <nav style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 14px',
                  borderRadius: 'var(--radius-md)',
                  border: isActive ? '1px solid rgba(99, 102, 241, 0.4)' : '1px solid transparent',
                  background: isActive ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                  color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                  fontFamily: 'var(--font-display)',
                  fontSize: '0.875rem',
                  fontWeight: isActive ? 600 : 500,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  outline: 'none'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.color = '#FFFFFF';
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.color = 'var(--text-secondary)';
                }}
              >
                <Icon size={16} color={isActive ? '#6366F1' : 'currentColor'} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>

        {/* Backend Connection Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: 'var(--radius-full)',
            background: isOnline ? 'rgba(16, 185, 129, 0.1)' : 'rgba(244, 63, 94, 0.1)',
            border: isOnline ? '1px solid rgba(16, 185, 129, 0.25)' : '1px solid rgba(244, 63, 94, 0.25)'
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isOnline ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              boxShadow: isOnline ? '0 0 8px var(--accent-emerald)' : '0 0 8px var(--accent-rose)'
            }} />
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 600,
              color: isOnline ? 'var(--accent-emerald)' : 'var(--accent-rose)',
              fontFamily: 'var(--font-mono)'
            }}>
              {isOnline ? 'REST API: 8000' : 'Connecting API...'}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}
