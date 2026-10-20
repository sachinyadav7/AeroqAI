import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DashboardView from './views/DashboardView';
import DebuggerView from './views/DebuggerView';
import EvaluationView from './views/EvaluationView';
import OptimizerView from './views/OptimizerView';
import LeaderboardView from './views/LeaderboardView';
import QualityGateView from './views/QualityGateView';
import { fetchHealth } from './apiClient';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [systemStatus, setSystemStatus] = useState(null);

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkHealth = async () => {
    try {
      const data = await fetchHealth();
      setSystemStatus(data);
    } catch (err) {
      setSystemStatus({ status: 'offline' });
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Top Navigation */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        systemStatus={systemStatus} 
      />

      {/* Main Content Area */}
      <main style={{
        flex: 1,
        maxWidth: '1440px',
        width: '100%',
        margin: '0 auto',
        padding: '2.5rem 2rem'
      }}>
        {activeTab === 'dashboard' && (
          <DashboardView systemStatus={systemStatus} setActiveTab={setActiveTab} />
        )}
        {activeTab === 'debugger' && <DebuggerView />}
        {activeTab === 'evaluation' && <EvaluationView />}
        {activeTab === 'optimizer' && <OptimizerView />}
        {activeTab === 'leaderboard' && <LeaderboardView />}
        {activeTab === 'quality-gate' && <QualityGateView />}
      </main>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgba(8, 12, 20, 0.95)',
        padding: '2rem',
        marginTop: 'auto'
      }}>
        <div style={{
          maxWidth: '1440px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          fontSize: '0.85rem',
          color: 'var(--text-muted)'
        }}>
          <div>
            <strong style={{ color: 'var(--text-secondary)' }}>AeroqAI</strong> — Enterprise AI Application Evaluation, RAG Optimization & Quality Assurance Platform
          </div>
          <div>
            B.Tech Major Project • Shri Ramdeobaba College of Engineering & Management
          </div>
        </div>
      </footer>
    </div>
  );
}
