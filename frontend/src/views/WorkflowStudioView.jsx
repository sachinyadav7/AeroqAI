import React, { useState } from 'react';
import { 
  FileText, 
  Scissors, 
  Binary, 
  Database, 
  TrendingUp, 
  MessageSquare, 
  Cpu, 
  ShieldCheck, 
  Play, 
  CheckCircle2, 
  Clock, 
  Sparkles, 
  Sliders, 
  Layers, 
  Zap, 
  X,
  ExternalLink
} from 'lucide-react';
import { traceQuery } from '../apiClient';

export default function WorkflowStudioView({ setActiveTab }) {
  const [selectedNodeId, setSelectedNodeId] = useState('retrieve');
  const [tracing, setTracing] = useState(false);
  const [traceResult, setTraceResult] = useState(null);
  const [sampleQuery, setSampleQuery] = useState("What is the policy for annual leave?");

  // Workflow pipeline nodes matching image_6.jpg node canvas
  const nodes = [
    {
      id: 'source',
      title: 'Document Source',
      category: 'Ingestion',
      icon: FileText,
      color: '#3B82F6',
      x: 40,
      y: 50,
      status: 'HEALTHY',
      duration: '4.2 ms',
      config: {
        loader: 'PDFDocumentLoader',
        file: 'hr_policy.pdf',
        pages: 10,
        empty_page_pruning: true
      },
      inputs: ['Raw PDF File (AeroqAI/data/sample_docs/hr_policy.pdf)'],
      outputs: ['10 Page Documents with page_number and metadata']
    },
    {
      id: 'cleaner',
      title: 'Text Normalizer',
      category: 'Preprocessing',
      icon: Scissors,
      color: '#06B6D4',
      x: 290,
      y: 50,
      status: 'HEALTHY',
      duration: '1.8 ms',
      config: {
        cleaner: 'TextCleaner',
        strip_control_chars: true,
        fix_hyphenation: true,
        unicode_normalization: 'NFKC',
        whitespace_collapse: true
      },
      inputs: ['10 Raw Document Pages'],
      outputs: ['Cleaned Document Pages with standardized whitespace']
    },
    {
      id: 'chunker',
      title: 'Recursive Chunker',
      category: 'Segmentation',
      icon: Layers,
      color: '#8B5CF6',
      x: 540,
      y: 50,
      status: 'HEALTHY',
      duration: '3.1 ms',
      config: {
        strategy: 'recursive',
        chunk_size: 800,
        chunk_overlap: 60,
        separators: ['\n\n', '\n', '. ', ' ']
      },
      inputs: ['Cleaned Documents'],
      outputs: ['11 Text Chunks with unique chunk_id and page provenance']
    },
    {
      id: 'embedder',
      title: 'Dense Embedder',
      category: 'Vectorization',
      icon: Binary,
      color: '#7567FF',
      x: 790,
      y: 50,
      status: 'HEALTHY',
      duration: '18.4 ms',
      config: {
        model: 'sentence-transformers/all-MiniLM-L6-v2',
        dimensions: 384,
        normalize_embeddings: true,
        device: 'CPU'
      },
      inputs: ['11 Text Passages (or user query)'],
      outputs: ['384-dimensional dense vectors (unit normalized)']
    },
    {
      id: 'retrieve',
      title: 'Vector Store Index',
      category: 'Retrieval',
      icon: Database,
      color: '#20C5E7',
      x: 1040,
      y: 50,
      status: 'HEALTHY',
      duration: traceResult ? `${((traceResult.retrieval?.latency_ms ?? traceResult.stages?.retrieval?.latency_ms ?? 12.6)).toFixed(1)} ms` : '12.6 ms',
      config: {
        store_type: 'InMemoryVectorStore',
        similarity_metric: 'Cosine Similarity',
        top_k: 4,
        score_threshold: 0.15
      },
      inputs: ['Query Vector (384-d)', 'Top-K requested = 4'],
      outputs: ['Top-4 candidate passages ranked by cosine similarity']
    },
    {
      id: 'reranker',
      title: 'Neural Cross-Encoder',
      category: 'Reranking',
      icon: TrendingUp,
      color: '#F5B942',
      x: 1040,
      y: 280,
      status: 'HEALTHY',
      duration: traceResult ? `${((traceResult.rerank?.latency_ms ?? traceResult.stages?.rerank?.latency_ms ?? 38.2)).toFixed(1)} ms` : '38.2 ms',
      config: {
        model: 'cross-encoder/ms-marco-MiniLM-L-6-v2',
        reranker_top_k: 2,
        pairwise_scoring: true
      },
      inputs: ['Candidate Passages from Vector Store (4 items)', 'Original Query string'],
      outputs: ['Top-2 reranked passages with cross-encoder relevance scores']
    },
    {
      id: 'context',
      title: 'Context Assembler',
      category: 'Prompt Engineering',
      icon: Sliders,
      color: '#10B981',
      x: 790,
      y: 280,
      status: 'HEALTHY',
      duration: '0.4 ms',
      config: {
        template: 'AeroqAI System Prompt with Grounded Citation Guards',
        max_context_chars: 4000,
        citation_format: '[Doc: {source}, Page: {page}]'
      },
      inputs: ['Reranked Top-2 Chunks', 'Query'],
      outputs: ['Formatted prompt with system instructions and bounded context']
    },
    {
      id: 'generator',
      title: 'LLM Generator',
      category: 'Inference',
      icon: Cpu,
      color: '#635BEE',
      x: 540,
      y: 280,
      status: 'HEALTHY',
      duration: traceResult ? `${(((traceResult.generation?.latency_ms ?? traceResult.stages?.generation?.latency_ms ?? 1240)) / 1000).toFixed(2)} s` : '1.24 s',
      config: {
        provider: 'Groq Cloud LPU',
        model: 'openai/gpt-oss-120b',
        temperature: 0.1,
        max_tokens: 512
      },
      inputs: ['Assembled Prompt with Grounding Guardrails'],
      outputs: ['Synthesized grounded answer with source citations']
    },
    {
      id: 'evaluator',
      title: 'Triad Quality Gate',
      category: 'Governance',
      icon: ShieldCheck,
      color: '#20C997',
      x: 290,
      y: 280,
      status: 'HEALTHY',
      duration: '24.0 ms',
      config: {
        framework: 'Ragas / TruLens Triad',
        faithfulness_min: 0.70,
        correctness_min: 0.50,
        precision_min: 0.50,
        mode: 'Deterministic Heuristic + LLM-as-a-Judge'
      },
      inputs: ['Generated Answer', 'Retrieved Context', 'Ground Truth (Optional)'],
      outputs: ['Faithfulness (1.00), Answer Correctness (0.55), Quality Score']
    }
  ];

  const selectedNode = nodes.find(n => n.id === selectedNodeId) || nodes[0];

  const handleRunTrace = async () => {
    setTracing(true);
    try {
      const trace = await traceQuery(sampleQuery, null, 4, 2, true);
      setTraceResult(trace);
    } catch (err) {
      alert("Pipeline trace execution error: " + err.message);
    } finally {
      setTracing(false);
    }
  };

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      
      {/* Studio Header & Run Controls */}
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
            <span className="badge-pill primary">Interactive Pipeline Canvas</span>
            <span className="badge-pill neutral">7 Stages Active</span>
          </div>
          <h1 style={{ margin: 0, fontSize: '1.75rem' }}>Workflow Studio</h1>
          <p style={{ margin: 0, fontSize: '0.88rem' }}>
            Visual node-based architecture of the live AeroqAI RAG pipeline. Select any stage to inspect configuration, inputs, and outputs.
          </p>
        </div>

        {/* Live Query Execution Bar */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', width: '340px' }}>
            <input 
              type="text"
              className="form-input"
              value={sampleQuery}
              onChange={(e) => setSampleQuery(e.target.value)}
              placeholder="Enter test query for workflow execution..."
              style={{ fontSize: '0.85rem' }}
            />
          </div>

          <button 
            className="btn btn-primary btn-sm"
            onClick={handleRunTrace}
            disabled={tracing}
          >
            <Play size={14} />
            <span>{tracing ? "Tracing Execution..." : "Trace Workflow Execution"}</span>
          </button>
        </div>
      </div>

      {/* Main Studio Layout: Interactive Node Canvas + Inspector Side-Drawer */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 380px',
        gap: '1.5rem',
        alignItems: 'start'
      }}>
        
        {/* Visual Node Canvas (Inspired by image_6.jpg Giselle Node Graph) */}
        <div className="card workflow-canvas" style={{ minHeight: '520px', padding: '2rem 1.5rem', position: 'relative' }}>
          
          {/* Canvas SVG Connecting Bezier Wires */}
          <svg style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none' }}>
            <defs>
              <linearGradient id="wireGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="var(--accent-primary)" />
                <stop offset="100%" stopColor="var(--accent-secondary)" />
              </linearGradient>
            </defs>

            {/* Wire 1: Source -> Cleaner */}
            <path d="M 220,110 C 255,110 255,110 290,110" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />
            
            {/* Wire 2: Cleaner -> Chunker */}
            <path d="M 470,110 C 505,110 505,110 540,110" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />

            {/* Wire 3: Chunker -> Embedder */}
            <path d="M 720,110 C 755,110 755,110 790,110" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />

            {/* Wire 4: Embedder -> Vector Store */}
            <path d="M 970,110 C 1005,110 1005,110 1040,110" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />

            {/* Wire 5: Vector Store -> Neural Reranker (Down curve) */}
            <path d="M 1130,175 C 1130,225 1130,225 1130,280" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />

            {/* Wire 6: Neural Reranker -> Context Assembler (Leftwards curve) */}
            <path d="M 1040,340 C 1005,340 1005,340 970,340" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />

            {/* Wire 7: Context Assembler -> LLM Generator */}
            <path d="M 790,340 C 755,340 755,340 720,340" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />

            {/* Wire 8: LLM Generator -> Triad Quality Gate */}
            <path d="M 540,340 C 505,340 505,340 470,340" stroke="url(#wireGradient)" strokeWidth="2.5" fill="none" opacity="0.75" />
          </svg>

          {/* Interactive Node Cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4rem', position: 'relative', zIndex: 10 }}>
            {/* Upper Row: Ingestion to Retrieval */}
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
              {nodes.slice(0, 5).map((node) => {
                const Icon = node.icon;
                const isSelected = selectedNodeId === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="card card-interactive"
                    style={{
                      width: '210px',
                      padding: '1rem',
                      cursor: 'pointer',
                      border: isSelected ? `2px solid ${node.color}` : '1px solid var(--border)',
                      backgroundColor: isSelected ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
                      boxShadow: isSelected ? `0 0 20px ${node.color}40` : 'var(--card-shadow)',
                      position: 'relative'
                    }}
                  >
                    {/* Node Header */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
                      <div style={{
                        width: '30px',
                        height: '30px',
                        borderRadius: '8px',
                        backgroundColor: `${node.color}25`,
                        color: node.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        <Icon size={16} />
                      </div>
                      <div style={{ overflow: 'hidden' }}>
                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          {node.category}
                        </div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                          {node.title}
                        </div>
                      </div>
                    </div>

                    {/* Node Meta / Latency */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.72rem',
                      backgroundColor: 'var(--bg-app)',
                      padding: '0.3rem 0.5rem',
                      borderRadius: '6px',
                      border: '1px solid var(--border-subtle)'
                    }}>
                      <span style={{ color: 'var(--text-muted)' }}>Latency</span>
                      <span style={{ fontWeight: 600, color: 'var(--accent-secondary)' }}>{node.duration}</span>
                    </div>

                    {/* Output Port Dot */}
                    <span style={{
                      position: 'absolute',
                      right: '-6px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: node.color,
                      border: '2px solid var(--bg-surface)'
                    }} />
                  </div>
                );
              })}
            </div>

            {/* Lower Row: Reranking to Quality Gate (Reverse Flow) */}
            <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap', justifyContent: 'flex-start', paddingLeft: '230px' }}>
              {nodes.slice(5).map((node) => {
                const Icon = node.icon;
                const isSelected = selectedNodeId === node.id;
                return (
                  <div
                    key={node.id}
                    onClick={() => setSelectedNodeId(node.id)}
                    className="card card-interactive"
                    style={{
                      width: '210px',
                      padding: '1rem',
                      cursor: 'pointer',
                      border: isSelected ? `2px solid ${node.color}` : '1px solid var(--border)',
                      backgroundColor: isSelected ? 'var(--bg-surface-elevated)' : 'var(--bg-surface)',
                      boxShadow: isSelected ? `0 0 20px ${node.color}40` : 'var(--card-shadow)',
                      position: 'relative'
                    }}
                  >
                    {/* Node Header */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
                      <div style={{
                        width: '30px',
                        height: '30px',
                        borderRadius: '8px',
                        backgroundColor: `${node.color}25`,
                        color: node.color,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        flexShrink: 0
                      }}>
                        <Icon size={16} />
                      </div>
                      <div style={{ overflow: 'hidden' }}>
                        <div style={{ fontSize: '0.68rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                          {node.category}
                        </div>
                        <div style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                          {node.title}
                        </div>
                      </div>
                    </div>

                    {/* Node Meta / Latency */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.72rem',
                      backgroundColor: 'var(--bg-app)',
                      padding: '0.3rem 0.5rem',
                      borderRadius: '6px',
                      border: '1px solid var(--border-subtle)'
                    }}>
                      <span style={{ color: 'var(--text-muted)' }}>Latency</span>
                      <span style={{ fontWeight: 600, color: 'var(--accent-secondary)' }}>{node.duration}</span>
                    </div>

                    {/* Input Port Dot */}
                    <span style={{
                      position: 'absolute',
                      right: '-6px',
                      top: '50%',
                      transform: 'translateY(-50%)',
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      backgroundColor: node.color,
                      border: '2px solid var(--bg-surface)'
                    }} />
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Node Inspector Side-Drawer */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="card-header">
            <div className="card-title-group">
              <Sliders size={18} style={{ color: selectedNode.color }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Stage Inspector</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {selectedNode.category} • {selectedNode.title}
                </span>
              </div>
            </div>
            <span className="badge-pill success">ACTIVE</span>
          </div>

          <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            {/* Stage Latency & Health */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '0.75rem 1rem',
              backgroundColor: 'var(--bg-surface-elevated)',
              borderRadius: '8px',
              border: '1px solid var(--border-subtle)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Clock size={16} style={{ color: 'var(--text-muted)' }} />
                <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Stage Execution</span>
              </div>
              <span style={{ fontWeight: 700, color: 'var(--accent-secondary)' }}>{selectedNode.duration}</span>
            </div>

            {/* Stage Configuration Parameters */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                Parameters & Hyperparameters
              </div>
              <div style={{
                backgroundColor: 'var(--code-bg)',
                border: '1px solid var(--code-border)',
                borderRadius: '8px',
                padding: '0.85rem',
                fontSize: '0.78rem',
                fontFamily: 'JetBrains Mono, monospace'
              }}>
                {Object.entries(selectedNode.config).map(([key, val]) => (
                  <div key={key} style={{ display: 'flex', justifyContent: 'space-between', padding: '0.2rem 0' }}>
                    <span style={{ color: 'var(--accent-secondary)' }}>{key}:</span>
                    <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Inputs */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                Inputs
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {selectedNode.inputs.map((inp, idx) => (
                  <li key={idx} style={{ marginBottom: '0.25rem' }}>{inp}</li>
                ))}
              </ul>
            </div>

            {/* Outputs */}
            <div>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '0.4rem' }}>
                Outputs
              </div>
              <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                {selectedNode.outputs.map((out, idx) => (
                  <li key={idx} style={{ marginBottom: '0.25rem' }}>{out}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="card-footer" style={{ display: 'flex', justifyContent: 'space-between' }}>
            <button 
              className="btn btn-outline btn-sm"
              onClick={() => setActiveTab('debugger')}
            >
              <span>Inspect in Debugger</span>
              <ExternalLink size={14} />
            </button>
            <button 
              className="btn btn-secondary btn-sm"
              onClick={() => setActiveTab('optimizer')}
            >
              <span>Optimize Node</span>
            </button>
          </div>
        </div>

      </div>

      {/* Trace Execution Drawer (If Run) */}
      {traceResult && (
        <div className="card card-glass animate-fade-in" style={{ borderColor: 'var(--accent-primary)' }}>
          <div className="card-header">
            <div className="card-title-group">
              <CheckCircle2 size={18} style={{ color: 'var(--success)' }} />
              <div>
                <h3 style={{ fontSize: '0.98rem', margin: 0 }}>Live Pipeline Trace Generated</h3>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  Total Latency: {(traceResult.total_latency_ms || 0).toFixed(1)} ms • Retained Passages: {(traceResult.rerank?.reranked_chunks || traceResult.stages?.rerank?.reranked_chunks || traceResult.retrieval?.retrieved_chunks)?.length || 2}
                </span>
              </div>
            </div>
            <button 
              className="btn btn-primary btn-sm"
              onClick={() => setActiveTab('debugger')}
            >
              <span>Open Detailed Profiler</span>
            </button>
          </div>
          <div className="card-body">
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
              <strong>Answer:</strong> {traceResult.generation?.generated_answer || traceResult.generation?.answer || traceResult.stages?.generation?.answer || "No response generated."}
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              {(traceResult.generation?.source_citations || traceResult.generation?.citations || traceResult.stages?.generation?.citations || []).map((c, i) => (
                <span key={i} className="badge-pill neutral" style={{ fontSize: '0.72rem' }}>
                  {typeof c === 'string' ? c : (c.citation_label || `[Page: ${c.page_number}]`)}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
