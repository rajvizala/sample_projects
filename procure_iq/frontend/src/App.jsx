import React, { useState } from 'react';
import { BarChart3, LayoutDashboard, FileText, ShieldAlert, TrendingUp } from 'lucide-react';
import DashboardView from './components/DashboardView';
import DocumentParser from './components/DocumentParser';
import SupplierRisk from './components/SupplierRisk';
import ForecastView from './components/ForecastView';

const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'parser', label: 'Document Parser', icon: FileText },
  { id: 'suppliers', label: 'Supplier Risk', icon: ShieldAlert },
  { id: 'forecast', label: 'Forecast', icon: TrendingUp },
];

export default function App() {
  const [page, setPage] = useState('dashboard');

  return (
    <div className="min-h-screen bg-slate-950">
      <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <BarChart3 size={20} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">ProcureIQ</h1>
              <p className="text-[10px] text-slate-500 -mt-0.5 uppercase tracking-widest">AI Procurement Intelligence</p>
            </div>
          </div>
          <nav className="flex gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button key={item.id} onClick={() => setPage(item.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    page === item.id
                      ? 'bg-slate-800 text-white'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
                  }`}>
                  <Icon size={16} />
                  <span className="hidden md:inline">{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {page === 'dashboard' && <DashboardView />}
        {page === 'parser' && <DocumentParser />}
        {page === 'suppliers' && <SupplierRisk />}
        {page === 'forecast' && <ForecastView />}
      </main>
    </div>
  );
}
