import React from 'react';
import {
  LayoutDashboard,
  GitFork,
  Bug,
  FlaskConical,
  Database,
  TrendingUp,
  History,
  GitCompare,
  ShieldCheck,
  Rocket,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Activity,
  Layers
} from 'lucide-react';

export default function Sidebar({ 
  activeTab, 
  setActiveTab, 
  systemStatus, 
  collapsed, 
  setCollapsed 
}) {
  const isHealthy = systemStatus?.status === 'healthy';

  const navSections = [
    {
      title: 'Workspace',
      items: [
        { id: 'overview', label: 'Overview', icon: LayoutDashboard },
        { id: 'workflow', label: 'Workflow Studio', icon: GitFork, badge: 'Visual' },
        { id: 'debugger', label: 'RAG Debugger', icon: Bug },
        { id: 'evaluation', label: 'Evaluation Lab', icon: FlaskConical },
        { id: 'datasets', label: 'Datasets & Corpus', icon: Database }
      ]
    },
    {
      title: 'Optimization',
      items: [
        { id: 'optimizer', label: 'Optimizer & Pareto', icon: TrendingUp },
        { id: 'experiments', label: 'Experiments', icon: History },
        { id: 'diff', label: 'Quality Diff', icon: GitCompare, badge: 'Diffs' }
      ]
    },
    {
      title: 'Reliability & CI/CD',
      items: [
        { id: 'quality-gate', label: 'CI/CD Quality Gates', icon: ShieldCheck },
        { id: 'release-center', label: 'Release Center', icon: Rocket }
      ]
    },
    {
      title: 'System',
      items: [
        { id: 'settings', label: 'Settings & Health', icon: Settings }
      ]
    }
  ];

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      {/* Brand Header */}
      <div className="sidebar-header">
        <div className="brand-badge" onClick={() => setActiveTab('overview')}>
          <div className="brand-icon-box">
            <Layers size={20} />
          </div>
          {!collapsed && (
            <div className="brand-text">
              <span className="brand-title">AeroqAI</span>
              <span className="brand-tagline">AI Quality Engineering</span>
            </div>
          )}
        </div>
        <button
          className="btn btn-ghost btn-sm"
          onClick={() => setCollapsed(!collapsed)}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          style={{ padding: '0.3rem', color: 'var(--text-muted)' }}
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>

      {/* Nav Menu */}
      <nav className="sidebar-nav">
        {navSections.map((section, idx) => (
          <div key={idx} className="nav-group">
            {!collapsed && (
              <div className="nav-section-title">{section.title}</div>
            )}
            {section.items.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <div
                  key={item.id}
                  className={`nav-item ${isActive ? 'active' : ''}`}
                  onClick={() => setActiveTab(item.id)}
                  title={collapsed ? item.label : undefined}
                >
                  <Icon size={18} style={{ flexShrink: 0 }} />
                  {!collapsed && (
                    <span style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {item.label}
                    </span>
                  )}
                  {!collapsed && item.badge && (
                    <span 
                      style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '0.1rem 0.4rem',
                        borderRadius: '4px',
                        backgroundColor: isActive ? 'var(--accent-primary)' : 'var(--bg-surface-elevated)',
                        color: isActive ? '#FFFFFF' : 'var(--accent-secondary)'
                      }}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </nav>

      {/* Sidebar Footer with Live System Status */}
      <div className="sidebar-footer">
        {!collapsed ? (
          <div className="platform-status-badge">
            <span className={`status-dot ${isHealthy ? 'online' : 'danger'}`} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                {isHealthy ? 'System Operational' : 'System Offline'}
              </span>
              <span style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                FastAPI v1.0 • Groq LPU
              </span>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', justifyContent: 'center' }} title="System Operational">
            <span className={`status-dot ${isHealthy ? 'online' : 'danger'}`} />
          </div>
        )}
      </div>
    </aside>
  );
}
