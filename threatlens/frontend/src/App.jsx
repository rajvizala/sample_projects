import React, { useState } from 'react';
import { Shield, LayoutDashboard, Search, List } from 'lucide-react';
import Dashboard from './components/Dashboard';
import AnalysisForm from './components/AnalysisForm';
import ThreatList from './components/ThreatList';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'analyze', label: 'Analyze', icon: Search },
  { id: 'threats', label: 'Threats', icon: List },
];

export default function App() {
  const [page, setPage] = useState('dashboard');
  const [refreshKey, setRefreshKey] = useState(0);

  const handleAnalysisComplete = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <div className="min-h-screen bg-gray-950">
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-sky-600 p-2 rounded-lg">
              <Shield size={20} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">ThreatLens</h1>
              <p className="text-[10px] text-gray-500 -mt-0.5 uppercase tracking-widest">AI Security Monitor</p>
            </div>
          </div>
          <nav className="flex gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setPage(item.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    page === item.id
                      ? 'bg-gray-800 text-white'
                      : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800/50'
                  }`}
                >
                  <Icon size={16} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {page === 'dashboard' && <Dashboard key={refreshKey} />}
        {page === 'analyze' && (
          <div className="max-w-2xl mx-auto">
            <div className="mb-6">
              <h2 className="text-xl font-bold">Threat Analysis</h2>
              <p className="text-sm text-gray-400 mt-1">
                Submit emails, URLs, or messages to scan for phishing, scams, AI-generated content, and behavioral anomalies.
              </p>
            </div>
            <AnalysisForm onAnalysisComplete={handleAnalysisComplete} />
          </div>
        )}
        {page === 'threats' && <ThreatList key={refreshKey} />}
      </main>
    </div>
  );
}
