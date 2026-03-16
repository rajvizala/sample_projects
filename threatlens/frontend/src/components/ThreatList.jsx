import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react';
import { api } from '../utils/api';
import ThreatScore from './ThreatScore';

const statusIcons = {
  active: AlertTriangle,
  investigating: Clock,
  resolved: CheckCircle,
  dismissed: XCircle,
};

const statusColors = {
  active: 'text-red-400 bg-red-400/10',
  investigating: 'text-amber-400 bg-amber-400/10',
  resolved: 'text-green-400 bg-green-400/10',
  dismissed: 'text-gray-400 bg-gray-400/10',
};

export default function ThreatList() {
  const [threats, setThreats] = useState([]);
  const [total, setTotal] = useState(0);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const params = filter ? { status: filter } : {};
      const data = await api.getThreats(params);
      setThreats(data.threats);
      setTotal(data.total);
    } catch (e) {
      // ignore
    }
    setLoading(false);
  };

  useEffect(() => { load(); }, [filter]);

  const updateStatus = async (id, status) => {
    try {
      await api.updateThreat(id, { status });
      load();
    } catch (e) {
      // ignore
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between p-5 border-b border-gray-800">
        <h2 className="font-semibold">Threat Log ({total})</h2>
        <div className="flex gap-2">
          {['', 'active', 'investigating', 'resolved', 'dismissed'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filter === f ? 'bg-sky-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-gray-200'
              }`}
            >
              {f || 'All'}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="p-8 text-center text-gray-600">Loading...</div>
      ) : threats.length === 0 ? (
        <div className="p-8 text-center text-gray-600">No threats found. Run an analysis to get started.</div>
      ) : (
        <div className="divide-y divide-gray-800">
          {threats.map((t) => {
            const StatusIcon = statusIcons[t.status] || AlertTriangle;
            return (
              <div key={t.id} className="p-5 hover:bg-gray-800/30 transition-colors">
                <div className="flex items-start gap-4">
                  <ThreatScore score={t.threat_score} severity={t.severity} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium capitalize">{t.threat_type.replace('_', ' ')}</span>
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${statusColors[t.status]}`}>
                        <StatusIcon size={12} />
                        {t.status}
                      </span>
                      <span className="text-xs text-gray-600 ml-auto">
                        {new Date(t.created_at).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 line-clamp-2">{t.analysis_summary}</p>
                    {t.status === 'active' && (
                      <div className="flex gap-2 mt-2">
                        <button onClick={() => updateStatus(t.id, 'investigating')}
                          className="text-xs px-2 py-1 bg-amber-500/10 text-amber-400 rounded hover:bg-amber-500/20">
                          Investigate
                        </button>
                        <button onClick={() => updateStatus(t.id, 'resolved')}
                          className="text-xs px-2 py-1 bg-green-500/10 text-green-400 rounded hover:bg-green-500/20">
                          Resolve
                        </button>
                        <button onClick={() => updateStatus(t.id, 'dismissed')}
                          className="text-xs px-2 py-1 bg-gray-500/10 text-gray-400 rounded hover:bg-gray-500/20">
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
