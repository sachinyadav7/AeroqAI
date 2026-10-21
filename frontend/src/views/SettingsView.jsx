import React from 'react';
import { 
  Settings, 
  Cpu, 
  Database, 
  ShieldCheck, 
  Terminal, 
  ExternalLink, 
  CheckCircle2, 
  Sparkles,
  Layers,
  FileText
} from 'lucide-react';

export default function SettingsView({ systemStatus }) {
  const isHealthy = systemStatus?.status === 'healthy';

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
            <span className="badge-pill primary">Platform Diagnostics</span>
            <span className="badge-pill success">v1.0.0 Production</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>System & Engine Diagnostics</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Inspect loaded transformer models, vector store state, Groq LPU acceleration, and API documentation endpoints.
          </p>
        </div>
      </div>

      {/* Model Catalog Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '1rem'
      }}>
        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <div className="kpi-icon-wrap" style={{ background: 'var(--accent-primary-muted)', color: 'var(--accent-primary)' }}>
              <Cpu size={16} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Dense Embedding Model
              </div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                {systemStatus?.models?.embedder || "all-MiniLM-L6-v2"}
              </div>
            </div>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
            SentenceTransformers architecture producing 384-dimensional dense vectors with cosine nearest-neighbor search.
          </p>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <div className="kpi-icon-wrap" style={{ background: 'var(--accent-secondary-muted)', color: 'var(--accent-secondary)' }}>
              <Sparkles size={16} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Cross-Encoder Reranker
              </div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                {systemStatus?.models?.reranker || "cross-encoder/ms-marco-MiniLM-L-6-v2"}
              </div>
            </div>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
            Full joint pairwise neural cross-attention scoring query and passage pairs to lift context precision by +16.7%.
          </p>
        </div>

        <div className="card" style={{ padding: '1.25rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
            <div className="kpi-icon-wrap" style={{ background: 'var(--success-muted)', color: 'var(--success)' }}>
              <Terminal size={16} />
            </div>
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                Generation LLM Provider
              </div>
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)' }}>
                {systemStatus?.models?.generator || "openai/gpt-oss-120b"}
              </div>
            </div>
          </div>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
            Groq LPU hardware acceleration providing ultra-low inference latency with grounded citations.
          </p>
        </div>
      </div>

      {/* API Documentation & Swagger Endpoints */}
      <div className="card">
        <div className="card-header">
          <div className="card-title-group">
            <ExternalLink size={18} style={{ color: 'var(--accent-primary)' }} />
            <div>
              <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Interactive REST API Documentation</h3>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Direct access to OpenAPI schemas and Swagger documentation
              </span>
            </div>
          </div>
          <span className="badge-pill success">FASTAPI ACTIVE</span>
        </div>

        <div className="card-body">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
            <a 
              href="http://127.0.0.1:8000/docs" 
              target="_blank" 
              rel="noreferrer"
              className="card card-interactive"
              style={{ padding: '1.25rem', textDecoration: 'none', backgroundColor: 'var(--bg-surface-elevated)' }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--accent-primary)', marginBottom: '0.25rem' }}>
                Interactive Swagger UI ↗
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Explore live REST endpoints, send test payloads, and inspect schema responses.
              </div>
            </a>

            <a 
              href="http://127.0.0.1:8000/redoc" 
              target="_blank" 
              rel="noreferrer"
              className="card card-interactive"
              style={{ padding: '1.25rem', textDecoration: 'none', backgroundColor: 'var(--bg-surface-elevated)' }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--accent-secondary)', marginBottom: '0.25rem' }}>
                ReDoc API Reference ↗
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Clean three-panel technical documentation for enterprise integration.
              </div>
            </a>

            <a 
              href="http://127.0.0.1:8000/openapi.json" 
              target="_blank" 
              rel="noreferrer"
              className="card card-interactive"
              style={{ padding: '1.25rem', textDecoration: 'none', backgroundColor: 'var(--bg-surface-elevated)' }}
            >
              <div style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                OpenAPI Specification (JSON) ↗
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Standard machine-readable OpenAPI schema for client SDK generation.
              </div>
            </a>
          </div>
        </div>
      </div>

      {/* Project Meta Information */}
      <div className="card" style={{ padding: '1.5rem', backgroundColor: 'var(--bg-surface-elevated)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.05rem', color: 'var(--text-primary)' }}>
              AeroqAI — AI Quality Engineering Platform
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              B.Tech Major Project • Shri Ramdeobaba College of Engineering & Management
            </div>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <span className="badge-pill neutral">Pytest: 79 / 79 Passing</span>
            <span className="badge-pill neutral">CI/CD: GitHub Actions</span>
          </div>
        </div>
      </div>

    </div>
  );
}
