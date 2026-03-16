import React, { useState, useEffect } from 'react';
import { GitBranch, Play, Plus, Trash2, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';
import { api } from '../utils/api';

const statusIcons = { completed: CheckCircle, failed: XCircle, running: Clock, pending: Clock, skipped: XCircle };
const statusColors = {
  completed: 'text-emerald-400', failed: 'text-red-400',
  running: 'text-amber-400', pending: 'text-zinc-500', skipped: 'text-zinc-600',
};

export default function WorkflowBuilder() {
  const [agents, setAgents] = useState([]);
  const [prebuilt, setPrebuilt] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savedId, setSavedId] = useState(null);

  useEffect(() => {
    api.listAgents().then(d => setAgents(d.agents)).catch(() => {});
    api.listPrebuilt().then(d => setPrebuilt(d.workflows)).catch(() => {});
  }, []);

  const addNode = () => {
    const id = `node_${nodes.length + 1}`;
    setNodes([...nodes, { id, agent_name: agents[0]?.name || 'research', input_data: {}, depends_on: [], input_mapping: {} }]);
  };

  const removeNode = (idx) => {
    const updated = [...nodes];
    updated.splice(idx, 1);
    setNodes(updated);
  };

  const updateNode = (idx, field, value) => {
    const updated = [...nodes];
    updated[idx] = { ...updated[idx], [field]: value };
    setNodes(updated);
  };

  const loadPrebuilt = (template) => {
    setName(template.name);
    setDescription(template.description);
    setNodes(template.nodes.map(n => ({ ...n, input_data: { ...n.input_data }, depends_on: [...n.depends_on] })));
    setSavedId(null);
    setResult(null);
  };

  const saveAndExecute = async () => {
    if (!name || nodes.length === 0) return;
    setLoading(true);
    setResult(null);
    try {
      const saved = await api.createWorkflow({ name, description, nodes });
      setSavedId(saved.id);
      const exec = await api.executeWorkflow(saved.id);
      setResult(exec);
    } catch (err) {
      setResult({ status: 'failed', logs: [err.message] });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Workflow Builder</h2>
        <p className="text-sm text-zinc-400 mt-1">Compose agents into DAG workflows with dependencies and data passing.</p>
      </div>

      {prebuilt.length > 0 && (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {prebuilt.map((t) => (
            <button key={t.id} onClick={() => loadPrebuilt(t)}
              className="shrink-0 bg-zinc-900 border border-zinc-800 rounded-lg p-3 text-left hover:border-emerald-500/30 transition-colors">
              <p className="font-medium text-sm">{t.name}</p>
              <p className="text-xs text-zinc-500 mt-1">{t.description}</p>
            </button>
          ))}
        </div>
      )}

      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-zinc-400 block mb-1">Workflow Name</label>
            <input value={name} onChange={(e) => setName(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500" />
          </div>
          <div>
            <label className="text-xs text-zinc-400 block mb-1">Description</label>
            <input value={description} onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-emerald-500" />
          </div>
        </div>

        <div className="space-y-3">
          {nodes.map((node, idx) => (
            <div key={node.id} className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/50">
              <div className="flex items-center gap-3 mb-3">
                <span className="text-emerald-400 font-mono text-xs bg-emerald-400/10 px-2 py-0.5 rounded">{node.id}</span>
                <select value={node.agent_name}
                  onChange={(e) => updateNode(idx, 'agent_name', e.target.value)}
                  className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm focus:outline-none">
                  {agents.map(a => <option key={a.name} value={a.name}>{a.name}</option>)}
                </select>
                {idx > 0 && (
                  <select value={node.depends_on[0] || ''}
                    onChange={(e) => updateNode(idx, 'depends_on', e.target.value ? [e.target.value] : [])}
                    className="bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-sm focus:outline-none">
                    <option value="">No dependency</option>
                    {nodes.filter((_, i) => i < idx).map(n => (
                      <option key={n.id} value={n.id}>After: {n.id}</option>
                    ))}
                  </select>
                )}
                <button onClick={() => removeNode(idx)} className="ml-auto text-zinc-500 hover:text-red-400">
                  <Trash2 size={14} />
                </button>
              </div>
              <div>
                <label className="text-xs text-zinc-500 block mb-1">Input (JSON)</label>
                <input
                  value={JSON.stringify(node.input_data)}
                  onChange={(e) => { try { updateNode(idx, 'input_data', JSON.parse(e.target.value)) } catch {} }}
                  className="w-full bg-zinc-800 border border-zinc-700 rounded px-2 py-1 text-xs font-mono focus:outline-none"
                  placeholder='{"query": "your input here"}'
                />
              </div>
            </div>
          ))}
        </div>

        <div className="flex gap-3">
          <button onClick={addNode}
            className="flex items-center gap-2 px-4 py-2 bg-zinc-800 hover:bg-zinc-700 rounded-lg text-sm">
            <Plus size={16} /> Add Node
          </button>
          <button onClick={saveAndExecute} disabled={loading || !name || nodes.length === 0}
            className="flex-1 bg-emerald-600 hover:bg-emerald-500 disabled:bg-zinc-700 text-white font-medium py-2 rounded-lg flex items-center justify-center gap-2">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Play size={18} />}
            {loading ? 'Executing...' : 'Save & Execute'}
          </button>
        </div>
      </div>

      {result && (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
          <div className="flex items-center gap-3">
            <h3 className="font-medium">Execution Result</h3>
            <span className={`text-xs font-medium px-2 py-0.5 rounded ${
              result.status === 'completed' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
            }`}>{result.status}</span>
            {result.total_time_ms && <span className="text-xs text-zinc-500">{result.total_time_ms.toFixed(0)}ms</span>}
          </div>

          {result.nodes && Object.entries(result.nodes).map(([nodeId, node]) => {
            const Icon = statusIcons[node.status] || Clock;
            return (
              <div key={nodeId} className="bg-zinc-800/50 rounded-lg p-4 border border-zinc-700/30">
                <div className="flex items-center gap-2 mb-2">
                  <Icon size={14} className={statusColors[node.status]} />
                  <span className="font-mono text-xs text-emerald-400">{nodeId}</span>
                  <span className="text-xs text-zinc-500">({node.agent_name})</span>
                  <span className={`text-xs ${statusColors[node.status]}`}>{node.status}</span>
                </div>
                {node.result?.output && (
                  <pre className="bg-zinc-900 rounded p-3 text-xs overflow-auto max-h-48 whitespace-pre-wrap text-zinc-400">
                    {JSON.stringify(node.result.output, null, 2)}
                  </pre>
                )}
                {node.result?.error && <p className="text-red-400 text-xs mt-1">{node.result.error}</p>}
              </div>
            );
          })}

          {result.logs && (
            <div>
              <p className="text-xs text-zinc-500 mb-1">Execution Log</p>
              <div className="bg-zinc-800/50 rounded-lg p-3">
                {result.logs.map((log, i) => (
                  <p key={i} className="text-xs text-zinc-500 font-mono">{log}</p>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
