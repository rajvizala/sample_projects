import React, { useState, useEffect } from 'react';
import { Clock, CheckCircle, XCircle, ChevronRight } from 'lucide-react';
import { api } from '../utils/api';

export default function ExecutionHistory() {
  const [executions, setExecutions] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listExecutions().then(d => { setExecutions(d.executions); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const viewDetail = async (exec) => {
    setSelected(exec.id);
    try {
      const d = await api.getExecution(exec.id);
      setDetail(d);
    } catch (e) {
      setDetail(null);
    }
  };

  const statusIcon = (s) => {
    if (s === 'completed') return <CheckCircle size={14} className="text-emerald-400" />;
    if (s === 'failed') return <XCircle size={14} className="text-red-400" />;
    return <Clock size={14} className="text-amber-400" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Execution History</h2>
        <p className="text-sm text-zinc-400 mt-1">View past workflow and agent executions.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-zinc-800">
            <h3 className="text-sm font-medium text-zinc-400">Executions ({executions.length})</h3>
          </div>
          {loading ? (
            <div className="p-8 text-center text-zinc-600">Loading...</div>
          ) : executions.length === 0 ? (
            <div className="p-8 text-center text-zinc-600">No executions yet. Run a workflow to get started.</div>
          ) : (
            <div className="divide-y divide-zinc-800 max-h-[500px] overflow-y-auto">
              {executions.map((e) => (
                <button key={e.id} onClick={() => viewDetail(e)}
                  className={`w-full text-left p-4 hover:bg-zinc-800/50 transition-colors flex items-center gap-3 ${
                    selected === e.id ? 'bg-zinc-800/70' : ''
                  }`}>
                  {statusIcon(e.status)}
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{e.workflow_name}</p>
                    <p className="text-xs text-zinc-500">
                      {e.total_time_ms ? `${e.total_time_ms.toFixed(0)}ms` : 'N/A'}
                      {' - '}
                      {new Date(e.created_at).toLocaleString()}
                    </p>
                  </div>
                  <ChevronRight size={14} className="text-zinc-600" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          {detail ? (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 space-y-4">
              <div className="flex items-center gap-3">
                {statusIcon(detail.status)}
                <h3 className="font-medium">{detail.workflow_name}</h3>
                <span className="text-xs text-zinc-500">
                  {detail.total_time_ms ? `${detail.total_time_ms.toFixed(0)}ms` : ''}
                </span>
              </div>

              {detail.nodes && Object.entries(detail.nodes).map(([nodeId, node]) => (
                <div key={nodeId} className="bg-zinc-800/50 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-2">
                    {statusIcon(node.status)}
                    <span className="font-mono text-xs text-emerald-400">{nodeId}</span>
                    <span className="text-xs text-zinc-500">({node.agent_name})</span>
                  </div>
                  {node.result?.output && (
                    <pre className="bg-zinc-900 rounded p-3 text-xs overflow-auto max-h-40 whitespace-pre-wrap text-zinc-400">
                      {JSON.stringify(node.result.output, null, 2)}
                    </pre>
                  )}
                </div>
              ))}

              {detail.logs && (
                <div className="bg-zinc-800/50 rounded-lg p-3">
                  {detail.logs.map((log, i) => (
                    <p key={i} className="text-xs text-zinc-500 font-mono">{log}</p>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center text-zinc-600">
              Select an execution to view details
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
