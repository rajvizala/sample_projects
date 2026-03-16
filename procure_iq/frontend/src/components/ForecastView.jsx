import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { TrendingUp, Loader2 } from 'lucide-react';
import { api } from '../utils/api';

const CATEGORIES = ['Raw Materials', 'Electronics', 'Logistics', 'Chemicals', 'Packaging', 'Services'];

export default function ForecastView() {
  const [category, setCategory] = useState('');
  const [periods, setPeriods] = useState(12);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const generate = async () => {
    if (!category) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.generateForecast({ category, periods });
      setResult(res);
    } catch (err) {
      setError(err.message);
    }
    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold">Demand Forecasting</h2>
        <p className="text-sm text-slate-400 mt-1">Time series prediction using exponential smoothing with confidence intervals.</p>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="text-xs text-slate-400 block mb-1">Category</label>
            <select value={category} onChange={(e) => setCategory(e.target.value)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-indigo-500">
              <option value="">Select category...</option>
              {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="text-xs text-slate-400 block mb-1">Periods</label>
            <input type="number" min={1} max={52} value={periods}
              onChange={(e) => setPeriods(parseInt(e.target.value) || 12)}
              className="bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm w-20 focus:outline-none focus:border-indigo-500" />
          </div>
          <button onClick={generate} disabled={loading || !category}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <TrendingUp size={16} />}
            Generate Forecast
          </button>
        </div>
      </div>

      {error && <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">{error}</div>}

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <InfoCard label="Category" value={result.category} />
            <InfoCard label="Model" value={result.model_type.replace(/_/g, ' ')} />
            <InfoCard label="Trend" value={result.trend} />
            <InfoCard label="Next Period Est." value={`$${result.next_period_estimate.toLocaleString()}`} />
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
            <h3 className="text-sm font-medium text-slate-400 mb-4">Spend Forecast with Confidence Interval</h3>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={result.forecast}>
                <XAxis dataKey="date" tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={v => v.slice(5, 7) + '/' + v.slice(2, 4)} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }}
                  tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  formatter={(v) => [`$${Number(v).toLocaleString()}`, '']}
                  labelFormatter={(l) => `Period: ${l}`} />
                <Area type="monotone" dataKey="confidence_upper" stroke="none" fill="#6366f1" fillOpacity={0.1} />
                <Area type="monotone" dataKey="confidence_lower" stroke="none" fill="#1e293b" fillOpacity={1} />
                <Line type="monotone" dataKey="predicted_spend" stroke="#6366f1" strokeWidth={2} dot={{ fill: '#6366f1', r: 3 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="text-left p-3 text-slate-400 font-medium">Date</th>
                  <th className="text-right p-3 text-slate-400 font-medium">Predicted Qty</th>
                  <th className="text-right p-3 text-slate-400 font-medium">Predicted Spend</th>
                  <th className="text-right p-3 text-slate-400 font-medium">Confidence Range</th>
                </tr>
              </thead>
              <tbody>
                {result.forecast.map((f, i) => (
                  <tr key={i} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td className="p-3">{f.date}</td>
                    <td className="p-3 text-right text-slate-300">{f.predicted_quantity.toFixed(0)}</td>
                    <td className="p-3 text-right font-medium">${f.predicted_spend.toLocaleString()}</td>
                    <td className="p-3 text-right text-slate-400">
                      ${f.confidence_lower.toLocaleString()} - ${f.confidence_upper.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function InfoCard({ label, value }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <p className="text-xs text-slate-500">{label}</p>
      <p className="font-medium capitalize mt-0.5">{value}</p>
    </div>
  );
}
