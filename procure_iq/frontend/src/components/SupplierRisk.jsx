import React, { useState, useEffect } from 'react';
import { ShieldAlert, ChevronRight, Loader2 } from 'lucide-react';
import { api } from '../utils/api';

const riskColors = {
  low: 'text-emerald-400 bg-emerald-400/10',
  medium: 'text-amber-400 bg-amber-400/10',
  high: 'text-orange-400 bg-orange-400/10',
  critical: 'text-red-400 bg-red-400/10',
};

export default function SupplierRisk() {
  const [suppliers, setSuppliers] = useState([]);
  const [selected, setSelected] = useState(null);
  const [risk, setRisk] = useState(null);
  const [loading, setLoading] = useState(true);
  const [riskLoading, setRiskLoading] = useState(false);

  useEffect(() => {
    api.getSuppliers().then(d => { setSuppliers(d.suppliers); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const viewRisk = async (supplier) => {
    setSelected(supplier);
    setRiskLoading(true);
    try {
      const r = await api.getSupplierRisk(supplier.id);
      setRisk(r);
    } catch (e) {
      setRisk(null);
    }
    setRiskLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Supplier Risk Assessment</h2>
        <p className="text-sm text-slate-400 mt-1">Multi-factor risk scoring across delivery, quality, financial, and compliance dimensions.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="p-4 border-b border-slate-800">
            <h3 className="text-sm font-medium text-slate-400">Suppliers ({suppliers.length})</h3>
          </div>
          {loading ? (
            <div className="p-8 text-center text-slate-600">Loading...</div>
          ) : (
            <div className="divide-y divide-slate-800 max-h-[600px] overflow-y-auto">
              {suppliers.map((s) => (
                <button key={s.id} onClick={() => viewRisk(s)}
                  className={`w-full text-left p-4 hover:bg-slate-800/50 transition-colors flex items-center gap-3 ${
                    selected?.id === s.id ? 'bg-slate-800/70' : ''
                  }`}>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm truncate">{s.name}</p>
                    <p className="text-xs text-slate-500">{s.category} - {s.country}</p>
                  </div>
                  <span className={`text-xs font-bold px-2 py-1 rounded ${riskColors[s.risk_level] || riskColors.medium}`}>
                    {s.risk_score.toFixed(0)}
                  </span>
                  <ChevronRight size={14} className="text-slate-600" />
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2">
          {riskLoading ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 flex items-center justify-center">
              <Loader2 size={24} className="animate-spin text-indigo-400" />
            </div>
          ) : risk ? (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-5">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold">{risk.supplier_name}</h3>
                  <span className={`inline-block mt-1 text-xs font-medium uppercase px-2 py-0.5 rounded ${riskColors[risk.risk_level]}`}>
                    {risk.risk_level} risk
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-4xl font-bold">{risk.overall_risk_score.toFixed(0)}</p>
                  <p className="text-xs text-slate-500">/ 100</p>
                </div>
              </div>

              <div className="space-y-3">
                {risk.factors.map((f) => (
                  <div key={f.name} className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium">{f.name}</span>
                      <span className="text-sm font-bold">{f.score.toFixed(0)}</span>
                    </div>
                    <div className="w-full bg-slate-700 rounded-full h-2 mb-2">
                      <div className={`h-2 rounded-full ${
                        f.score > 70 ? 'bg-red-500' : f.score > 40 ? 'bg-amber-500' : 'bg-emerald-500'
                      }`} style={{ width: `${f.score}%` }} />
                    </div>
                    <p className="text-xs text-slate-400">{f.details}</p>
                  </div>
                ))}
              </div>

              <div className="bg-indigo-500/10 border border-indigo-500/20 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-1">
                  <ShieldAlert size={16} className="text-indigo-400" />
                  <span className="text-sm font-medium text-indigo-400">Recommendation</span>
                </div>
                <p className="text-sm text-slate-300">{risk.recommendation}</p>
              </div>
            </div>
          ) : (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-600">
              Select a supplier to view risk assessment
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
