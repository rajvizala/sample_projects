import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { ShieldAlert, ShieldCheck, Activity, TrendingUp } from 'lucide-react';
import { api } from '../utils/api';

const COLORS = ['#dc2626', '#ea580c', '#d97706', '#65a30d', '#0284c7'];

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 flex items-center gap-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon size={22} />
      </div>
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-gray-400">{label}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [timeline, setTimeline] = useState([]);

  useEffect(() => {
    api.getDashboardStats().then(setStats).catch(() => {});
    api.getTimeline(30).then(setTimeline).catch(() => {});
  }, []);

  if (!stats) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-gray-900 border border-gray-800 rounded-xl p-5 h-24 animate-pulse" />
        ))}
      </div>
    );
  }

  const severityData = Object.entries(stats.threat_by_severity || {}).map(([name, value]) => ({ name, value }));
  const typeData = Object.entries(stats.threat_by_type || {}).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Activity} label="Total Analyses" value={stats.total_analyses} color="bg-sky-500/10 text-sky-400" />
        <StatCard icon={ShieldAlert} label="Threats Detected" value={stats.threats_detected} color="bg-red-500/10 text-red-400" />
        <StatCard icon={ShieldCheck} label="Resolved" value={stats.resolved_threats} color="bg-green-500/10 text-green-400" />
        <StatCard icon={TrendingUp} label="Detection Rate" value={`${stats.detection_rate}%`} color="bg-amber-500/10 text-amber-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Threat Timeline (30 days)</h3>
          {timeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={timeline}>
                <XAxis dataKey="date" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(d) => d.slice(5)} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Bar dataKey="count" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-600">No data yet. Run some analyses.</div>
          )}
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-gray-400 mb-4">Threats by Severity</h3>
          {severityData.length > 0 ? (
            <div className="flex items-center gap-6">
              <ResponsiveContainer width="50%" height={220}>
                <PieChart>
                  <Pie data={severityData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} innerRadius={40}>
                    {severityData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-2">
                {severityData.map((d, i) => (
                  <div key={d.name} className="flex items-center gap-2 text-sm">
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                    <span className="text-gray-400 capitalize">{d.name}</span>
                    <span className="text-gray-200 font-medium ml-auto">{d.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-[220px] flex items-center justify-center text-gray-600">No threats recorded yet.</div>
          )}
        </div>
      </div>
    </div>
  );
}
