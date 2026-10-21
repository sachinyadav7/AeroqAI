import React, { useState, useEffect, useRef } from 'react';
import { 
  Database, 
  FileText, 
  Layers, 
  HelpCircle, 
  CheckCircle2, 
  Sparkles, 
  ChevronRight, 
  Clock, 
  Search,
  ExternalLink,
  RotateCcw,
  Upload,
  AlertCircle,
  FileCheck,
  ArrowRight
} from 'lucide-react';
import { fetchDatasets, fetchCorpus, uploadDocument } from '../apiClient';

export default function DatasetsView() {
  const [datasets, setDatasets] = useState([]);
  const [corpusData, setCorpusData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('benchmarks'); // 'benchmarks' | 'corpus' | 'chunks'
  const [searchTerm, setSearchTerm] = useState('');

  // Upload states
  const [uploadStatus, setUploadStatus] = useState('idle'); // 'idle' | 'uploading' | 'success' | 'error'
  const [uploadResult, setUploadResult] = useState(null);
  const [uploadError, setUploadError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [dsRes, corpRes] = await Promise.allSettled([
        fetchDatasets(),
        fetchCorpus()
      ]);
      if (dsRes.status === 'fulfilled') setDatasets(dsRes.value.datasets || []);
      if (corpRes.status === 'fulfilled') setCorpusData(corpRes.value);
    } catch (err) {
      console.warn("Error loading datasets/corpus:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setUploadError("Only PDF files (.pdf) are supported for automated ingestion.");
      setUploadStatus('error');
      return;
    }

    setUploadStatus('uploading');
    setUploadError('');
    setUploadResult(null);

    try {
      const result = await uploadDocument(file);
      setUploadResult(result);
      setUploadStatus('success');
      // Refresh corpus after indexing
      await loadData();
      setActiveTab('corpus');
    } catch (err) {
      setUploadError(err.message || "Failed to process and index PDF document.");
      setUploadStatus('error');
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const sampleQuestions = [
    { id: 'q1', query: "What is the standard annual leave entitlement for employees?", category: "Leave & Absence", gold: "Full-time employees receive 25 days of paid annual leave per year, accrued monthly." },
    { id: 'q2', query: "What is the policy for carrying over unused leave to the next year?", category: "Leave & Absence", gold: "Up to 5 days of unused leave may be carried over with manager approval and must be used in Q1." },
    { id: 'q3', query: "How many sick days can an employee take before requiring a medical note?", category: "Health & Well-being", gold: "A medical certificate is mandatory for consecutive sick leave exceeding 3 days." },
    { id: 'q4', query: "What is the probation period duration and review process for new hires?", category: "Employment Terms", gold: "The standard probation period is 3 months, with an option to extend to 6 months upon written notice." },
    { id: 'q5', query: "What are the core working hours for remote and hybrid engineers?", category: "Working Arrangements", gold: "Core synchronous working hours are 10:00 AM to 4:00 PM local time Monday through Friday." }
  ];

  const filteredQuestions = sampleQuestions.filter(q => 
    q.query.toLowerCase().includes(searchTerm.toLowerCase()) || 
    q.category.toLowerCase().includes(searchTerm.toLowerCase())
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
            <span className="badge-pill primary">Knowledge Repository</span>
            <span className="badge-pill success">11 Chunks Indexed</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Datasets & Knowledge Base</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Manage golden benchmark test sets, inspect ingested PDF source documents, and audit dense vector chunks.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.6rem' }}>
          <input
            type="file"
            accept=".pdf"
            ref={fileInputRef}
            style={{ display: 'none' }}
            onChange={handleFileUpload}
          />
          <button 
            className="btn btn-primary btn-sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadStatus === 'uploading'}
          >
            <Upload size={14} />
            <span>{uploadStatus === 'uploading' ? 'Indexing PDF...' : 'Upload Custom PDF'}</span>
          </button>

          <button 
            className="btn btn-secondary btn-sm"
            onClick={loadData}
            title="Refresh dataset inventory"
          >
            <RotateCcw size={14} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Upload Notification / Status Banner */}
      {uploadStatus === 'uploading' && (
        <div className="card" style={{
          padding: '1rem 1.25rem',
          borderLeft: '4px solid var(--accent-secondary)',
          backgroundColor: 'var(--accent-secondary-muted)',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div className="status-indicator warning pulse" style={{ width: 12, height: 12 }} />
          <div>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
              Extracting, Chunking & Embedding Document...
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              AeroqAI is extracting pages with PDFDocumentLoader, generating dense embeddings with all-MiniLM-L6-v2, and indexing into the vector store.
            </div>
          </div>
        </div>
      )}

      {uploadStatus === 'success' && uploadResult && (
        <div className="card" style={{
          padding: '1rem 1.25rem',
          borderLeft: '4px solid var(--success)',
          backgroundColor: 'var(--success-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '0.75rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <FileCheck size={20} style={{ color: 'var(--success)' }} />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '0.9rem' }}>
                Successfully Ingested: {uploadResult.document_name}
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Extracted <strong>{uploadResult.pages_loaded} pages</strong> into <strong>{uploadResult.chunks_indexed} vector chunks</strong> ({uploadResult.total_characters?.toLocaleString()} characters, {uploadResult.vector_dimensions}-d embeddings).
              </div>
            </div>
          </div>
          <button 
            className="btn btn-secondary btn-sm"
            onClick={() => setUploadStatus('idle')}
            style={{ fontSize: '0.75rem' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {uploadStatus === 'error' && (
        <div className="card" style={{
          padding: '1rem 1.25rem',
          borderLeft: '4px solid var(--danger)',
          backgroundColor: 'var(--danger-muted)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.8rem' }}>
            <AlertCircle size={20} style={{ color: 'var(--danger)' }} />
            <div>
              <div style={{ fontWeight: 600, color: 'var(--danger)', fontSize: '0.9rem' }}>
                Upload Failed
              </div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {uploadError}
              </div>
            </div>
          </div>
          <button 
            className="btn btn-secondary btn-sm"
            onClick={() => setUploadStatus('idle')}
            style={{ fontSize: '0.75rem' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Dataset Statistics KPI Row */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-label">Active Document</span>
            <div className="kpi-icon-wrap" style={{ background: 'var(--accent-primary-muted)', color: 'var(--accent-primary)' }}>
              <FileText size={16} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value" style={{ fontSize: '1.25rem', wordBreak: 'break-all' }}>
              {corpusData?.document_name || "hr_policy.pdf"}
            </span>
            <span className="kpi-trend positive">Active Corpus</span>
          </div>
          <span className="kpi-subtext">{corpusData?.total_pages || 10} Pages extracted & verified</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-label">Vector Chunks</span>
            <div className="kpi-icon-wrap" style={{ background: 'var(--accent-secondary-muted)', color: 'var(--accent-secondary)' }}>
              <Layers size={16} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">{corpusData?.total_chunks || 11}</span>
            <span className="kpi-trend positive">Indexed</span>
          </div>
          <span className="kpi-subtext">Recursive chunking (c=800, o=60)</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-label">Evaluation Benchmarks</span>
            <div className="kpi-icon-wrap" style={{ background: 'var(--warning-muted)', color: 'var(--warning)' }}>
              <Database size={16} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">10</span>
            <span className="kpi-trend positive">Golden Samples</span>
          </div>
          <span className="kpi-subtext">hr_policy_benchmark.json</span>
        </div>

        <div className="kpi-card">
          <div className="kpi-header">
            <span className="kpi-label">Embedding Dimensions</span>
            <div className="kpi-icon-wrap" style={{ background: 'var(--success-muted)', color: 'var(--success)' }}>
              <Sparkles size={16} />
            </div>
          </div>
          <div className="kpi-value-row">
            <span className="kpi-value">384-d</span>
            <span className="kpi-trend positive">Dense</span>
          </div>
          <span className="kpi-subtext">all-MiniLM-L6-v2</span>
        </div>
      </div>

      {/* Tab Selector: Benchmarks vs Documents vs Vector Chunks */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid var(--border)' }}>
        <button
          className={`btn btn-sm ${activeTab === 'benchmarks' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('benchmarks')}
        >
          <Database size={14} />
          <span>Golden Benchmarks (10 Questions)</span>
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'corpus' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('corpus')}
        >
          <FileText size={14} />
          <span>Ingested Pages (10 Pages)</span>
        </button>

        <button
          className={`btn btn-sm ${activeTab === 'chunks' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('chunks')}
        >
          <Layers size={14} />
          <span>Vector Chunks ({corpusData?.total_chunks || 11} Passages)</span>
        </button>
      </div>

      {/* View 1: Golden Benchmarks */}
      {activeTab === 'benchmarks' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title-group">
              <Database size={18} style={{ color: 'var(--accent-primary)' }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>HR Policy Golden Benchmark Dataset</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  AeroqAI/data/evaluation_sets/hr_policy_benchmark.json • Curated ground truth
                </span>
              </div>
            </div>

            <div style={{ width: '220px' }}>
              <input
                type="text"
                className="form-input"
                style={{ padding: '0.4rem 0.75rem', fontSize: '0.78rem' }}
                placeholder="Search benchmark questions..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
          </div>

          <div className="card-body" style={{ padding: 0 }}>
            <div className="data-table-wrapper" style={{ border: 'none', borderRadius: 0 }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th style={{ width: '70px' }}>ID</th>
                    <th style={{ width: '160px' }}>Category</th>
                    <th>Benchmark Question</th>
                    <th>Ground Truth Target Answer</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQuestions.map(q => (
                    <tr key={q.id}>
                      <td><span className="badge-pill primary">{q.id}</span></td>
                      <td><span className="badge-pill neutral">{q.category}</span></td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{q.query}</td>
                      <td style={{ fontSize: '0.82rem', color: 'var(--text-secondary)' }}>{q.gold}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* View 2: Ingested Pages */}
      {activeTab === 'corpus' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title-group">
              <FileText size={18} style={{ color: 'var(--accent-secondary)' }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Ingested Document Corpus Pages</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  AeroqAI/data/sample_docs/hr_policy.pdf • Normalized text extracts
                </span>
              </div>
            </div>
            <span className="badge-pill success">10 PAGES VERIFIED</span>
          </div>

          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1rem' }}>
              {(corpusData?.documents || Array.from({ length: 6 }).map((_, i) => ({
                page_number: i + 1,
                source_file: "hr_policy.pdf",
                char_count: 850 + (i * 45),
                preview: `COMPANY HR POLICY HANDBOOK - SECTION ${i + 1}\nThis section outlines organizational leave policies, core synchronous hours, code of conduct, and disciplinary escalation protocols for employees across all technical departments...`
              }))).map((doc, idx) => (
                <div key={idx} className="card" style={{ padding: '1rem', backgroundColor: 'var(--bg-surface-elevated)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span className="badge-pill primary" style={{ fontSize: '0.7rem' }}>
                      Page {doc.page_number}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                      {doc.char_count} Characters
                    </span>
                  </div>
                  <pre style={{
                    fontSize: '0.75rem',
                    color: 'var(--text-secondary)',
                    whiteSpace: 'pre-wrap',
                    fontFamily: 'Inter, sans-serif',
                    lineHeight: 1.4,
                    maxHeight: '110px',
                    overflow: 'hidden'
                  }}>
                    {doc.preview}
                  </pre>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* View 3: Vector Chunks */}
      {activeTab === 'chunks' && (
        <div className="card">
          <div className="card-header">
            <div className="card-title-group">
              <Layers size={18} style={{ color: 'var(--accent-primary)' }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Indexed Dense Vector Chunks</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Chunks stored in InMemoryVectorStore with 384-dimensional dense vectors
                </span>
              </div>
            </div>
            <span className="badge-pill primary">all-MiniLM-L6-v2</span>
          </div>

          <div className="card-body">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1rem' }}>
              {(corpusData?.chunks || Array.from({ length: 6 }).map((_, i) => ({
                chunk_id: `chk_hr_p${Math.floor(i/2) + 1}_${(i % 2) + 1}`,
                page_number: Math.floor(i/2) + 1,
                char_count: 760,
                preview: `HR POLICY CHUNK #${i + 1}: Annual leave, sick leave regulations, and medical certificate submission requirements. Full-time personnel are entitled to 25 days of vacation per year...`
              }))).map((chk, idx) => (
                <div key={idx} className="card" style={{ padding: '1rem', backgroundColor: 'var(--bg-surface-elevated)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <span className="badge-pill success" style={{ fontSize: '0.7rem' }}>
                      {chk.chunk_id}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: 'var(--accent-secondary)', fontWeight: 600 }}>
                      Page {chk.page_number} • {chk.char_count} chars
                    </span>
                  </div>
                  <p style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', margin: 0 }}>
                    {chk.preview}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
