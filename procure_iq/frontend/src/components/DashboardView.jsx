import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { DollarSign, Users, Clock, AlertTriangle, TrendingUp, ShieldAlert } from 'lucide-react';
import { api } from '../utils/api';

const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe'];

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
      <div className="flex items-center gap-3 mb-2">
        <div className={`p-2 rounded-lg ${color}`}><Icon size={18} /></div>
        <span className="text-sm text-slate-400">{label}</span>
      </div>
      <p className="text-2xl font-bold">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

export default function DashboardView() {
  const [data, setData] = useState(null);

  useEffect(() => {
    api.getDashboard().then(setData).catch(() => {});
  }, []);

  if (!data) return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {[...Array(6)].map((_, i) => <div key={i} className="bg-slate-900 border border-slate-800 rounded-xl p-5 h-28 animate-pulse" />)}
    </div>
  );

  const fmt = (n) => n >= 1e6 ? `$${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `$${(n/1e3).toFixed(0)}K` : `$${n.toFixed(0)}`;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard icon={DollarSign} label="Total Spend" value={fmt(data.total_spend)} color="bg-indigo-500/10 text-indigo-400" />
        <StatCard icon={Users} label="Suppliers" value={data.active_suppliers} color="bg-violet-500/10 text-violet-400" />
        <StatCard icon={Clock} label="Pending Orders" value={data.pending_orders} color="bg-amber-500/10 text-amber-400" />
        <StatCard icon={AlertTriangle} label="Anomalies" value={data.anomalies_detected} color="bg-red-500/10 text-red-400" />
        <StatCard icon={ShieldAlert} label="Avg Risk" value={data.avg_risk_score.toFixed(0)} color="bg-orange-500/10 text-orange-400" />
        <StatCard icon={TrendingUp} label="Savings Opp." value={fmt(data.savings_opportunity)} color="bg-emerald-500/10 text-emerald-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Spend Trend (90 days)</h3>
          {data.spend_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={data.spend_trend}>
                <XAxis dataKey="month" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={v => v.slice(5)} />
                <YAxis tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={v => `$${(v/1000).toFixed(0)}k`} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                  formatter={(v) => [`$${v.toLocaleString()}`, 'Spend']} />
                <Bar dataKey="spend" fill="#6366f1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <div className="h-60 flex items-center justify-center text-slate-600">No spend data. Run seed script first.</div>}
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-400 mb-4">Top Categories</h3>
          {data.top_categories.length > 0 ? (
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="50%" height={240}>
                <PieChart>
                  <Pie data={data.top_categories} dataKey="spend" nameKey="name" cx="50%" cy="50%" outerRadius={85} innerRadius={45}>
                    {data.top_categories.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: 8 }}
                    formatter={(v) => [`$${v.toLocaleString()}`, 'Spend']} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-3">
                {data.top_categories.map((c, i) => (
                  <div key={c.name} className="flex items-center gap-2 text-sm">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="text-slate-400">{c.name}</span>
                    <span className="text-slate-200 font-medium ml-auto">{fmt(c.spend)}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : <div className="h-60 flex items-center justify-center text-slate-600">No data available.</div>}
        </div>
      </div>

      {data.high_risk_suppliers.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-slate-400 mb-4">High Risk Suppliers</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {data.high_risk_suppliers.map((s) => (
              <div key={s.name} className="bg-slate-800/50 rounded-lg p-4 border border-red-500/20">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-sm">{s.name}</span>
                  <span className="text-red-400 font-bold text-sm">{s.risk_score}</span>
                </div>
                <span className="text-xs text-slate-500">{s.category}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
