import React, { useState, useEffect } from 'react';
import { Bot, Play, Loader2, ChevronRight } from 'lucide-react';
import { api } from '../utils/api';

const agentIcons = {
  research: '🔍', writer: '📝', analyst: '📊', coder: '💻', coordinator: '🎯',
};

const placeholders = {
  research: { query: 'What are the latest trends in AI agent orchestration?' },
  writer: { prompt: 'Write a professional email announcing a new product launch', tone: 'professional', format: 'email' },
  analyst: { data: 'name,revenue,growth\nProduct A,50000,15\nProduct B,32000,22\nProduct C,78000,8\nProduct D,21000,45' },
  coder: { task: 'Create a Python function that implements binary search on a sorted list', language: 'python' },
  coordinator: { task: 'Build a comprehensive market analysis report for a new SaaS product targeting small businesses' },
};

export default function AgentPanel() {
  const [agents, setAgents] = useState([]);
  const [selected, setSelected] = useState(null);
  const [inputFields, setInputFields] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listAgents().then(d => setAgents(d.agents)).catch(() => {});
  }, []);

  const selectAgent = (agent) => {
    setSelected(agent);
    setInputFields(placeholders[agent.name] || {});
    setResult(null);
  };

  const execute = async () => {
    if (!selected) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await api.executeAgent(selected.name, { input_data: inputFields });
      setResult(res);
    } catch (err) {
      setResult({ success: false, error: err.message });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Agent Playground</h2>
        <p className="text-sm text-zinc-400 mt-1">Select an agent and test it with custom input.</p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
        {agents.map((a) => (
          <button key={a.name} onClick={() => selectAgent(a)}
            className={`p-4 rounded-xl border text-left transition-all ${
              selected?.name === a.name
                ? 'bg-emerald-500/10 border-emerald-500/30'
                : 'bg-zinc-900 border-zinc-800 hover:border-zinc-700'
            }`}>
            <span className="text-2xl">{agentIcons[a.name] || '🤖'}</span>
            <p className="font-medium text-sm mt-2 capitalize">{a.name}</p>
            <p className="text-xs text-zinc-500 mt-1 line-clamp-2">{a.description}</p>
          </button>
        ))}
      </div>

      {selected && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
            <h3 className="font-medium capitalize flex items-center gap-2">
              <Bot size={18} className="text-emerald-400" />
              {selected.name} Agent
            </h3>
            <div className="flex flex-wrap gap-2">
              {selected.capabilities.map((c) => (
                <span key={c} className="text-xs px-2 py-0.5 bg-zinc-800 rounded-full text-zinc-400">{c}</span>
              ))}
            </div>
            <div className="space-y-3">
              {Object.entries(inputFields).map(([key, value]) => (
                <div key={key}>
                  <label className="text-xs text-zinc-400 block mb-1 capitalize">{key}</label>
                  {String(value).length > 50 ? (
                    <textarea value={value} rows={4}
                      onChange={(e) => setInputFields({ ...inputFields, [key]: e.target.value })}
                      className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500 resize-none" />
                  ) : (
                    <input type="text" value={value}
                      onChange={(e) => setInputFields({ ...inputFields, [key]: e.target.value })}
                      className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500" />
                  )}
                </div>
              ))}
              <button onClick={() => setInputFields({ ...inputFields, ['new_field']: '' })}
                className="text-xs text-zinc-500 hover:text-zinc-300">+ Add field</button>
            </div>
            <button onClick={execute} disabled={loading}
              className="w-full bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 text-white font-medium py-2.5 rounded-lg flex items-center justify-center gap-2">
              {loading ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
              {loading ? 'Executing...' : 'Execute Agent'}
            </button>
          </div>

          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5">
            <h3 className="font-medium mb-4">Output</h3>
            {result ? (
              <div className="space-y-3">
                <div className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-medium ${
                  result.success ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
                }`}>
                  {result.success ? 'Success' : 'Failed'}
                </div>
                {result.execution_time_ms && (
                  <p className="text-xs text-zinc-500">{result.execution_time_ms.toFixed(0)}ms | {result.tokens_used} tokens</p>
                )}
                {result.error && <p className="text-red-400 text-sm">{result.error}</p>}
                {result.output && (
                  <pre className="bg-zinc-800/50 rounded-lg p-4 text-sm overflow-auto max-h-96 whitespace-pre-wrap text-zinc-300">
                    {JSON.stringify(result.output, null, 2)}
                  </pre>
                )}
                {result.logs && result.logs.length > 0 && (
                  <div>
                    <p className="text-xs text-zinc-500 mb-1">Logs</p>
                    {result.logs.map((log, i) => (
                      <p key={i} className="text-xs text-zinc-600 font-mono">{log}</p>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <p className="text-zinc-600 text-sm">Execute the agent to see results.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
