import React, { useState } from 'react';
import { Cpu, Bot, GitBranch, History, Wrench } from 'lucide-react';
import AgentPanel from './components/AgentPanel';
import WorkflowBuilder from './components/WorkflowBuilder';
import ExecutionHistory from './components/ExecutionHistory';

const navItems = [
  { id: 'agents', label: 'Agents', icon: Bot },
  { id: 'workflows', label: 'Workflows', icon: GitBranch },
  { id: 'history', label: 'History', icon: History },
];

export default function App() {
  const [page, setPage] = useState('agents');

  return (
    <div className="min-h-screen bg-zinc-950">
      <header className="border-b border-zinc-800 bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-emerald-600 p-2 rounded-lg">
              <Cpu size={20} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight">AgentForge</h1>
              <p className="text-[10px] text-zinc-500 -mt-0.5 uppercase tracking-widest">Agent Orchestration</p>
            </div>
          </div>
          <nav className="flex gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button key={item.id} onClick={() => setPage(item.id)}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    page === item.id
                      ? 'bg-zinc-800 text-white'
                      : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50'
                  }`}>
                  <Icon size={16} />
                  {item.label}
                </button>
              );
            })}
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {page === 'agents' && <AgentPanel />}
        {page === 'workflows' && <WorkflowBuilder />}
        {page === 'history' && <ExecutionHistory />}
      </main>
    </div>
  );
}
