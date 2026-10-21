import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Topbar from './components/Topbar';
import OverviewView from './views/OverviewView';
import WorkflowStudioView from './views/WorkflowStudioView';
import DebuggerView from './views/DebuggerView';
import EvaluationView from './views/EvaluationView';
import OptimizerView from './views/OptimizerView';
import LeaderboardView from './views/LeaderboardView';
import QualityDiffView from './views/QualityDiffView';
import QualityGateView from './views/QualityGateView';
import DatasetsView from './views/DatasetsView';
import SettingsView from './views/SettingsView';
import { fetchHealth } from './apiClient';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('aeroqai_theme') || 'dark';
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);

  // Synchronize theme with data-theme attribute on root html element
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('aeroqai_theme', theme);
  }, [theme]);

  // Poll system health
  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
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

  const handlePrimaryAction = (tab) => {
    if (tab === 'overview' || tab === 'evaluation') {
      setActiveTab('evaluation');
    } else if (tab === 'workflow' || tab === 'debugger') {
      setActiveTab('debugger');
    } else if (tab === 'optimizer') {
      setActiveTab('optimizer');
    } else if (tab === 'experiments' || tab === 'diff') {
      setActiveTab('diff');
    } else if (tab === 'quality-gate' || tab === 'release-center') {
      setActiveTab('quality-gate');
    } else {
      checkHealth();
    }
  };

  return (
    <div className="app-shell">
      {/* Persistent Left Sidebar Navigation */}
      <Sidebar 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        systemStatus={systemStatus}
        collapsed={sidebarCollapsed}
        setCollapsed={setSidebarCollapsed}
      />

      {/* Main App Container */}
      <div className="main-container">
        {/* Top Navigation Bar */}
        <Topbar 
          activeTab={activeTab}
          theme={theme}
          setTheme={setTheme}
          systemStatus={systemStatus}
          onPrimaryAction={handlePrimaryAction}
        />

        {/* Dynamic View Body */}
        <main className="content-body">
          {activeTab === 'overview' && (
            <OverviewView 
              systemStatus={systemStatus} 
              setActiveTab={setActiveTab} 
              theme={theme}
            />
          )}

          {activeTab === 'workflow' && (
            <WorkflowStudioView 
              setActiveTab={setActiveTab} 
            />
          )}

          {activeTab === 'debugger' && (
            <DebuggerView />
          )}

          {activeTab === 'evaluation' && (
            <EvaluationView />
          )}

          {activeTab === 'optimizer' && (
            <OptimizerView />
          )}

          {activeTab === 'experiments' && (
            <LeaderboardView 
              setActiveTab={setActiveTab} 
            />
          )}

          {activeTab === 'diff' && (
            <QualityDiffView />
          )}

          {(activeTab === 'quality-gate' || activeTab === 'release-center') && (
            <QualityGateView />
          )}

          {activeTab === 'datasets' && (
            <DatasetsView />
          )}

          {activeTab === 'settings' && (
            <SettingsView 
              systemStatus={systemStatus} 
            />
          )}
        </main>
      </div>
    </div>
  );
}
